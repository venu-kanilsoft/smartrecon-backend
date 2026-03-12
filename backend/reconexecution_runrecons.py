from reconexecution_enum import *
from reconexecution_model import *
import fastapi
import recons_stdapi
import reconexecution_runrecon
from dateutil.relativedelta import relativedelta

router = fastapi.APIRouter(prefix='/reconexecution')

@router.post('/runrecons', tags=['ReconExecution'])
async def ReconExecutionrunrecons(data: runreconsParams):
    if not data.reconids:
        return {"status":False, "message":"Please provide list of reconid(s)", "data": []}

    if not data.stmtdate:
        stmtdate = datetime.datetime.now().strftime('%d-%m-%Y')

    stmt_date = datetime.datetime.now()
    if data.stmtdate == "previous_month":
        stmt_date = stmt_date - relativedelta(days=int(0), months=int(1))
    elif data.stmtdate == "previous":
        stmt_date = stmt_date - datetime.timedelta(days=1)
    elif data.stmtdate == "daybeforeyesterday":
        stmt_date = stmt_date - datetime.timedelta(days=2)
    elif data.stmtdate == "threedaysago":
        stmt_date = stmt_date - datetime.timedelta(days=3)
    elif data.stmtdate == 'tatasky_monthly_recon':
        stmt_date = stmt_date - relativedelta(days=int(stmt_date.day - 1), months=int(1))
    data.stmtdate = stmt_date.strftime('%d-%m-%Y')

    for reconId in data.reconids:
        data1 = reconexecution_runrecon.reconexecution_model.runreconParams
        data1.reconId = reconId
        data1.stmtdate = data.stmtdate
        resp = await reconexecution_runrecon.ReconExecutionrunrecon(data1)

    return {"status": resp['status'], "message": 'Execution Started', "data": []}
