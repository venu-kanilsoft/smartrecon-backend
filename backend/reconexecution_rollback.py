from reconexecution_enum import *
from reconexecution_model import *
import fastapi
import json
import ReconExecDetailsLog_stdapi
import os
import SystemAudit_stdapi

router = fastapi.APIRouter(prefix="/reconexecution")


@router.post("/rollback", tags=["ReconExecution"])
async def ReconExecutionrollback(data: rollbackParams):
    # Rollbacked By
    login_session = await framework.restapi.me()
    rollbackedBy = login_session.get('email', '')

    # checking if there are any previous executions
    query = {"reconId": data.reconId,"jobStatus": "Success"}
    params = framework.queryparams.QueryParams()
    params.limit = 100
    params.fields = None
    params.skip = 0
    # params.sort = json.dumps(sort)
    params.q = json.dumps(query)
    resp = await ReconExecDetailsLog_stdapi.ReconExecDetailsLog.get_all(params)
    count = resp.get("count", 0)

    if count == 0:
        print("No Successful executions to Rollback")
        return {"status": False, "message": "No Successful executions to Rollback", "data": []}
    
    execdata = resp.get("data", [])[0]
    engine_scripts_path = framework.settings.engine_scripts_polars
    if not engine_scripts_path:
        engine_scripts_path = "/data/ngerecon/smartrecon/reconengine/scripts"
    print('engine_scripts_path :',engine_scripts_path)
    cmd = f"{engine_scripts_path}/reconrollback.sh {data.reconId} {rollbackedBy}"
    os.system(cmd)
    audit = {'type': 'Recon Rollback', 'msg': f'Recon rollback for {execdata.get("reconName", "")}', 'reason': 'Success',
                     'actionStatus': True}
    status, message = await SystemAudit_stdapi.create_auditLogs(audit)
    return {"status": True, "message": "Recon Roll back success", "data": []}

