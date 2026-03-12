from ReconExecDetailsLog_enum import *
from ReconExecDetailsLog_model import *
import fastapi
import framework
import json
import ReconExecDetailsLog_stdapi

router = fastapi.APIRouter(prefix='/reconexecdetailslog')

@router.post('/getLatestExeDetails', tags=['ReconExecDetailsLog'])
async def ReconExecDetailsLoggetLatestExeDetails(data: getLatestExeDetailsParams):
    recon_exec_ins = ReconExecDetailsLog_stdapi.ReconExecDetailsLog()
    dbName = framework.settings.dbName
    recon_exec_details_log = {"reconId": data.reconId, "jobStatus": "Success"}
    params = framework.queryparams.QueryParams()
    params.limit = 1
    params.sort = json.dumps({"updated": -1})
    params.q = json.dumps(recon_exec_details_log)
    try:
        resp = await recon_exec_ins.get_all(params, dbName)
        recon_exec_details_log = resp.get("data", [])
        if not recon_exec_details_log:
            return {"status": False, "message": "No Latest Execution Found", "data": []}
    except Exception as e:
        print(e)
        recon_exec_details_log = []
    return {"status": True, "message": "Success" , "data": recon_exec_details_log}
