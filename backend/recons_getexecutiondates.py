from recons_enum import *
from recons_model import *
import datetime
import fastapi
import json
import ReconExecDetailsLog_stdapi

router = fastapi.APIRouter(prefix='/recons')

@router.post('/getExecutionDates', tags=['Recons'])
async def ReconsgetExecutionDates(data: getExecutionDatesParams):
    recon_exec_ins = ReconExecDetailsLog_stdapi.ReconExecDetailsLog()
    dbName = framework.settings.dbName
    recon_exec_details_log = {"reconId": data.reconId,"jobStatus": "Success"}
    params = framework.queryparams.QueryParams()
    params.limit = 1000
    params.sort = json.dumps({"statementDate": -1})
    params.q = json.dumps(recon_exec_details_log)
    try:
        resp = await recon_exec_ins.get_all(params, dbName)
        execlist = resp.get("data", [])
        if not execlist:
            return {"status": False, "message": "No Latest Execution Found", "data": []}
    except Exception as e:
        execlist = {"status": False, "message": e, "data": []}
    dateslist = []
    for el in execlist:
        dateslist.append(el['statementDate'].strftime('%d/%m/%Y'))
    return {"status": True, "message": "Success" , "data": dateslist}
