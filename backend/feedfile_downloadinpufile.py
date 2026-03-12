from FeedFile_enum import *
from FeedFile_model import *
import json
import fastapi
import reconexecdetailslog_getlatestexedetails
import SourceReference_stdapi

router = fastapi.APIRouter(prefix='/feedfile')

@router.post('/downloadInpufile', tags=['FeedFile'])
async def FeedFiledownloadInpufile(data: downloadInpufileParams):
    mftpath = framework.settings.mftpath
    if not data.stmtDate:
        data1 = reconexecdetailslog_getlatestexedetails.getLatestExeDetailsParams
        data1.reconId = data.reconId
        doc = await reconexecdetailslog_getlatestexedetails.ReconExecDetailsLoggetLatestExeDetails(data1)
        if doc['status']:
            data.stmtDate = datetime.datetime.fromisoformat(
                doc["data"][0].get('statementDate', None)).strftime('%d%m%Y')
        else:
            return {"status": False, "message": "No Latest Execution Found", "data": []}
    else:
        data.stmtDate = datetime.datetime.strptime(data.stmtDate, '%d-%m-%Y').strftime('%d%m%Y')
    
    # data = self.mclient['sourceReference'].find_one({'reconId':reconId, 'source': sourceName})
    query = {"reconId": data.reconId, "source": data.sourceName}
    params = framework.queryparams.QueryParams()
    params.limit = 100
    params.skip = 0
    params.q = json.dumps(query)
    resp = await SourceReference_stdapi.SourceReference.get_all(params, framework.settings.dbName)
    if not resp.get('data', []):
        return {"status":False,"message": 'Please Provide Source Details', "data": []}
    resp = resp.get('data', [])[0]
    fp = os.path.join(mftpath, 'sources', resp.get('folderName', ''), data.stmtDate, data.filename)
    print("fp: ",fp)
    if os.path.exists(fp):
        login_session = await framework.restapi.me()
        # userid = flask.session["sessionData"].get('_id', '')
        userid = login_session.get('given_name')
        downloadpath = os.path.join(mftpath, 'downloads', userid)
        if not os.path.exists(downloadpath):
            os.makedirs(downloadpath)

        # creating link to downloads folder
        if not os.path.exists(f'{framework.settings.ui_code_path}downloads'):
            os.system('ln -s {framework.settings.mftpath}downloads/ {framework.settings.ui_code_path}')
        
        shutil.copy(fp, downloadpath)
        return {"status": True, "message": "Success", "data": os.path.join('/downloads', userid, os.path.split(data.filename)[1])}

    return {"status": False, "message": "File Doesn't exist", "data": []}
