from FeedFile_enum import *
from FeedFile_model import *
import os
import json
import fastapi
import datetime
import pysftp
from dateutil.relativedelta import relativedelta
import reconexecution_runrecon
import ReconExecDetailsLog_stdapi
import FeedFile_stdapi
import SourceReference_stdapi
from time import sleep

cnopts = pysftp.CnOpts()
cnopts.hostkeys = None

router = fastapi.APIRouter(prefix='/feedfile')

@router.post('/monitorFeedPath', tags=['FeedFile'])
async def FeedFilemonitorFeedPath(data: monitorFeedPathParams):
    if not data.reconids:
        return {"status":False, "message":"Please provide list of reconid(s)", "data": []}

    for reconId in data.reconids:
        lastexec = await _elastic_find_one(
                ReconExecDetailsLog_stdapi.ReconExecDetailsLog(),
                {"reconId": reconId, "jobStatus": "Success"},
                sort=[{"stmtDate": {"order": "desc"}}],
                limit=1,
            )
        reconName = lastexec.get('reconName', '')
        data.stmtdate = datetime.datetime.fromisoformat(
            lastexec["statementDate"]
            ) + relativedelta(
                days=int(0), months=int(0)
            )
        data.stmtdate = data.stmtdate.strftime('%d-%m-%Y')
        feeddata = await _elastic_find_one(
            FeedFile_stdapi.FeedFile,
            {"reconId": reconId},
            limit=1,
        )
        if not feeddata:
            return {"status":False, "message":"Please provide Feed details for %s Recon" % reconName, "data": []}
        feeddata_resp = await getSouceFeedFilePattern(feeddata, data.stmtdate)

    return {"status": feeddata_resp['status'], "message": 'Execution Started', "data": []}


async def getSouceFeedFilePattern(feeddata, stmtDate):
    if 'sftp' in feeddata.keys():
        source_data = feeddata['sftp']
        for source in source_data:
            pemkey = None if (source['pemkey'] == '') or (source['pemkey'] == None) else os.path.join(framework.settings.mftpath,'sftppemkey',source['pemkey'])
            password = None if source['password'] == '' else source['password']
            host = source['host']
            username = source['userName']
            port = None if source['port'] == '' else source['port']
            stmtdate = datetime.datetime.strptime(str(stmtDate),'%d-%m-%Y')
            stmtdate = stmtdate + relativedelta(days=int(source['tdate']),months=int(source['tmonth']))
            source['filePattern'] =  stmtdate.strftime(source['filePattern'])
            
            if (source['dateFolderPattern'] != '') and ('dateFoldertdate' in source.keys()) and ('dateFoldertmonth' in source.keys()):
                stmtdate = datetime.datetime.strptime(str(stmtDate),'%d-%m-%Y')
                stmtdate = stmtdate + relativedelta(days=int(source['dateFoldertdate']),months=int(source['dateFoldertmonth']))
                datefolder = stmtdate.strftime(source['dateFolderPattern'])
                source['remotePath'] = os.path.join(source['remotePath'], datefolder)
            sftp = pysftp.Connection(host=host, username=username, port=int(port), password=password,private_key=pemkey, cnopts=cnopts)
            if sftp.exists(source['remotePath']):
                resp = await getLatestFile(host, username, port, password, pemkey, feeddata, source['remotePath'], source['filePattern'], source['sourceName'], stmtDate) 
            continue
        return {"status": True, "message": "Success", "data": []}
    else:
        return {"status": True, "message": "No Sftp details.", "data": []}

async def getSourceWiseLocalPath(reconId, source):
    search_doc = {"reconId": reconId, "source": source}
    query = {
        "query": {
            "bool": {
                "must": [{"match": {key: value}} for key, value in search_doc.items()]
            }
        }
    }
    params = framework.queryparams.QueryParams()
    params.limit = 100
    params.fields = []
    params.skip = 0
    # params.sort = json.dumps(sort)
    params.q = json.dumps(query)
    try:
        resp = await SourceReference_stdapi.SourceReference.get_all(params)
    except Exception as e:
        print(f"Error in get_all: {e}")
        return {}
    if resp.get('data', []):
        data = resp.get('data', [])[0]
    else:
        data = {}
    return data


async def getLatestFile(host, username, port, password, pemkey, feeddata, remote_dir, filepattern, source, stmtDate):
    sftp = pysftp.Connection(host=host, username=username, port=int(port), password=password,private_key=pemkey, cnopts=cnopts)
    for add, rem in changemon(sftp, remote_dir):
        for fileName in add:
            if fileName.startswith(filepattern):
                data = await getSourceWiseLocalPath(feeddata['reconId'], source)
                localpath = os.path.join(framework.settings.mftpath, 'sources', data.get('folderName', ''), datetime.datetime.strptime(stmtDate, '%d-%m-%Y').strftime('%d%m%Y'))
                if not os.path.exists(localpath):
                    os.makedirs(localpath)
                sftp.get(os.path.join(remote_dir,fileName),os.path.join(localpath,fileName))
                if os.path.exists(os.path.join(localpath,fileName)):
                    return await FeedFile_stdapi.loadInputData(payload={'reconId': feeddata['reconId'], 'reconName': feeddata['reconName'], 'statementDate': datetime.datetime.strptime(stmtDate, '%d-%m-%Y')})
    return {"status": False, "message": "No latest file found from last min", "data": []}
        

def changemon(sftp, remote_dir=''):
    ls_prev = set()
    count = 0
    while True:
        count += 1
        ls = set(sftp.listdir(remote_dir))
        add, rem = ls-ls_prev, ls_prev-ls

        if add or rem: yield add, rem

        ls_prev = ls
        sleep(5)
        if count == 5:
            return add, rem


async def _elastic_find_one(connection_object, search_doc, sort=[], limit=1000):
    """
    custom elastic equivalent of find_one() in mongo.
    Similar param scheme except for "connection_object"
    """
    query = {
        "query": {
            "bool": {
                "must": [{"match": {key: value}} for key, value in search_doc.items()]
            }
        }
    }
    params = framework.queryparams.QueryParams()
    params.limit = limit
    params.fields = []
    params.skip = 0
    params.sort = json.dumps(sort)
    params.q = json.dumps(query)
    try:
        resp = await connection_object.get_all(params, framework.settings.dbName)
        doc = resp.get("data", [])
    except Exception as e:
        print(f"Error in get_all: {e}")
        doc = []
    if not doc:
        return {}
    return doc[0]