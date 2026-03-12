from recons_enum import *
from recons_model import *
import json
import os
import fastapi
import reconexecdetailslog_getlatestexedetails
from datetime import datetime, date


router = fastapi.APIRouter(prefix='/recons')

@router.post('/dirCycle', tags=['Recons'])
async def ReconsdirCycle(data: dirCycleParams):
    listOfCycle = []
    ins = framework.postgresmodel.PostgresModel()
    dbName = framework.settings.dbName
    tableName = f"{dbName}_recon_exec_details_log"
    print('tableName', tableName)
    if not data.stmtdate:
        data1 = reconexecdetailslog_getlatestexedetails.getLatestExeDetailsParams
        data1.reconId = data.reconId
        doc = await reconexecdetailslog_getlatestexedetails.ReconExecDetailsLoggetLatestExeDetails(data1)
        if doc['status']:
            data.stmtdate = doc["data"][0].get('statementDate', None).strftime('%d-%m-%Y')
        else:
            return {"status": True, "message": "Success" , "data": []}
    stmtdate = datetime.strptime(data.stmtdate, '%d-%m-%Y')
    recon_exec_details_log = {"reconId": data.reconId,"jobStatus": "Success","_type_": "reconexecdetailslog","statementDate": stmtdate}
    params = framework.queryparams.QueryParams()
    params.limit = 100
    params.sort = json.dumps([{"statementDate": {"order": "desc"}}])
    params.q = json.dumps(recon_exec_details_log, default=jsondefault)
    try:
        resp = await ins.get_all(params, dbName, tableName)
        recon_exec_details_log = resp.get("data", [])
        if not recon_exec_details_log:
            return {"status": True, "message": "Success" , "data": []}
    except Exception as e:
        print(e)
        recon_exec_details_log = {"status": True, "message": "Success" , "data": []}

    query = {"_type_": "reconMetaInfoInc","reconId": data.reconId}
    params = framework.queryparams.QueryParams()
    params.limit = 10
    params.q = json.dumps(query)
    tableName = f"{dbName}_recon_meta_info"
    print('query', query)
    try:
        resp = await ins.get_all(params, dbName, tableName)
        resp = resp.get("data", [])
    except Exception:
        resp = []
    if resp:
        recon_meta_info = resp[0]
    else:
        recon_meta_info = []
    incList = []
    if recon_meta_info:
        for eachKey in recon_meta_info['incData']:
            if isinstance(eachKey, dict):
                incList.append(eachKey.get("incrementLoader", False))
        if True in incList:
            outpath = os.path.join(framework.settings.mftpath, 'OUTPUT', data.reconId, stmtdate.strftime('%d%m%Y'))
            outpath = outpath + '/'
            print(outpath)
            listOfCycle = [f for f in os.listdir(outpath) if os.path.isdir(outpath+f)]
            print(listOfCycle)
            # listOfCycle = ['cycle_' + str(i) for i in range(1, len(recon_exec_details_log) + 1)]

    return {"status": True, "message": "Success" , "data": listOfCycle}

def jsondefault(o):
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    
