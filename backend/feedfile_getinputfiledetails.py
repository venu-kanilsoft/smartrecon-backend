from FeedFile_enum import *
from FeedFile_model import *
import os
import json
import glob
import fastapi
import reconexecdetailslog_getlatestexedetails
import feedfile_getsources
import SourceReference_stdapi

router = fastapi.APIRouter(prefix='/feedfile')

@router.post('/getInputFileDetails', tags=['FeedFile'])
async def FeedFilegetInputFileDetails(data: getInputFileDetailsParams):
    listOfFiles = []
    if data.stmtDate:
        data.stmtDate = datetime.datetime.strptime(data.stmtDate, '%d-%m-%Y').strftime('%d%m%Y')
    else:
        data1 = reconexecdetailslog_getlatestexedetails.getLatestExeDetailsParams
        data1.reconId = data.reconId
        doc = await reconexecdetailslog_getlatestexedetails.ReconExecDetailsLoggetLatestExeDetails(data1)
        if doc['status']:
            data.stmtDate = datetime.datetime.fromisoformat(
                doc["data"][0].get('statementDate', None)).strftime('%d%m%Y')
        else:
            return {"status": False, "message": "No Latest Execution Found", "data": []}
    feedfileparams = feedfile_getsources.getSourcesParams
    feedfileparams.reconId = data.reconId
    resp = await feedfile_getsources.FeedFilegetSources(feedfileparams)
    print(resp)
    for sources in resp.get('data', []):
        finaldata = {'reconName': data.reconName, 'reconId': data.reconId, 'fileName': '', 'fileAvailable': 'No',
            'sourceName': sources, 'reconType': data.reconProcess, 'stmtDate': data.stmtDate, 'filePattern': ''}
        query = {"reconId": data.reconId, "source": sources}
        params = framework.queryparams.QueryParams()
        params.limit = 100
        params.skip = 0
        params.q = json.dumps(query)
        resp = await SourceReference_stdapi.SourceReference.get_all(params, framework.settings.dbName)
        if not resp.get('data', []):
            return {"status":False,"message": 'Please Provide Source Details', "data": []}
        resp = resp.get('data', [])[0]
        if resp:
            finaldata['filePattern'] = resp['filePattern']
            if resp.get('folderName', ''):
                finaldata['remotePathPending'] = os.path.join(framework.settings.mftpath,'sources',resp.get('folderName', ''), data.stmtDate)
            else:
                finaldata['remotePathPending'] = os.path.join(framework.settings.mftpath,'sources')
            print(finaldata)
            if os.path.exists(finaldata['remotePathPending']):
                for files in glob.glob(finaldata['remotePathPending'] + '/*'):
                    fileDetails = {'fileName': os.path.split(files)[1], 'source': sources}
                    finaldata['fileName'] = os.path.split(files)[1]
                    listOfFiles.append(fileDetails)
    if len(listOfFiles) > 0:
        return {"status": True, "message": "Success", "data": listOfFiles}
    else:
        return {"status": False,"message": "No Input files", "data": []}
