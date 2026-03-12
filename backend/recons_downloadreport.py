from recons_enum import *
from recons_model import *
import fastapi
import reconexecdetailslog_getlatestexedetails

router = fastapi.APIRouter(prefix='/recons')

@router.post('/downloadReport', tags=['Recons'])
async def ReconsdownloadReport(data: downloadReportParams):
    mftpath = framework.settings.mftpath
    if not data.stmtdate:
        data1 = reconexecdetailslog_getlatestexedetails.getLatestExeDetailsParams
        data1.reconId = data.reconId
        resp = await reconexecdetailslog_getlatestexedetails.ReconExecDetailsLoggetLatestExeDetails(data1)
        recon_exec_data = resp.get('data', [])
        if not recon_exec_data:
            return False, "Unable to find latest execution details"
        recon_exec_data = recon_exec_data[0]
        stmtdate = datetime.datetime.strptime(recon_exec_data['statementDate'], '%Y-%m-%dT%H:%M:%S').strftime('%d%m%Y')
    else:
        stmtdate = datetime.datetime.strptime(data.stmtdate, '%d-%m-%Y').strftime('%d%m%Y')

    fp = os.path.join(mftpath, 'OUTPUT', data.reconId, stmtdate, data.filename)
    # if data.cyclewise:
    #     fp = os.path.join(mftpath, 'OUTPUT', data.reconId, stmtdate, data.cyclewise, data.filename)
    if os.path.exists(fp):
        login_session = await framework.restapi.me()
        # userid = flask.session["sessionData"].get('_id', '')
        userid = login_session.get('given_name')
        downloadpath = os.path.join(mftpath, 'downloads', userid)
        if not os.path.exists(downloadpath):
            os.makedirs(downloadpath)

        # creating link to downloads folder
        if not os.path.exists('/usr/share/nginx/newsmartrecon/postgresui/downloads'):
            os.system('ln -s /data/ngerecon/mft/downloads/ /usr/share/nginx/newsmartrecon/postgresui/')
        
        shutil.copy(fp, downloadpath)
        final_filename = os.path.join('/downloads', userid, os.path.split(data.filename)[1])
        print('final_filename -->',final_filename)
        return {"status": True, "message": "Success", "data": os.path.join('/downloads', userid, os.path.split(data.filename)[1])}

    return {"status":False, "message":"File Doesn't exist", "data": []}
