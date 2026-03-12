from recons_enum import *
from recons_model import *
import os
import shutil
import fastapi
import zipfile
import datetime
import reconexecdetailslog_getlatestexedetails

router = fastapi.APIRouter(prefix='/recons')

@router.post('/downloadAllReport', tags=['Recons'])
async def ReconsdownloadAllReport(data: downloadAllReportParams):
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

    fp = os.path.join(mftpath, 'OUTPUT', data.reconId, stmtdate)
    if data.cyclewise:
        fp = os.path.join(mftpath, 'OUTPUT', data.reconId, stmtdate, data.cyclewise)
    if os.path.exists(fp):
        login_session = await framework.restapi.me()
        userid = login_session.get('given_name')
        downloadpath = os.path.join(mftpath, 'downloads', userid)
        if not os.path.exists(downloadpath):
            os.makedirs(downloadpath)
        if not os.path.exists('/tmp/'+ userid +'/'):
            os.makedirs('/tmp/'+ userid +'/')
        zipObj = zipfile.ZipFile('/tmp/'+ userid +'/' + data.reconId + '-' + str(stmtdate) + '.zip', 'w')
        retval = os.getcwd()
        os.chdir(fp)
        final_reports = [f for f in os.listdir(fp) if os.path.isfile(f)]
        for file in os.listdir(fp):
            if file in final_reports:
                zipObj.write(file)
        zipObj.close()
        os.chdir(retval)

        # creating link to downloads folder
        if not os.path.exists('/usr/share/nginx/newsmartrecon/ui/downloads'):
            os.system('ln -s /data/ngerecon/mft/downloads/ /usr/share/nginx/newsmartrecon/ui/')
        filename = os.path.join('/tmp', userid, data.reconId+'-'+str(stmtdate)+'.zip')
        shutil.copy(filename, downloadpath)
        if os.path.exists(filename):
            os.remove(filename)
        return {"status": True, "data": os.path.join('/downloads', userid, os.path.split(filename)[1])}

    return {"status":False, "message":"File Doesn't exist", "data": []}
