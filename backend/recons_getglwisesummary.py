from recons_enum import *
from recons_model import *
import fastapi
import json
import reconexecdetailslog_getlatestexedetails


router = fastapi.APIRouter(prefix='/recons')

@router.post('/getGlWiseSummary', tags=['Recons'])
async def ReconsgetGlWiseSummary(data: getGlWiseSummaryParams):
    dbName = framework.settings.dbName
    if not data.stmtdate:
        data1 = reconexecdetailslog_getlatestexedetails.getLatestExeDetailsParams
        data1.reconId = data.reconId
        doc = await reconexecdetailslog_getlatestexedetails.ReconExecDetailsLoggetLatestExeDetails(data1)
        if doc['status']:
            data.stmtdate = datetime.datetime.fromisoformat(
                    doc["data"][0].get('statementDate', None)).strftime('%d-%m-%Y')
        else:
            return {"status": False, "message": "No Latest Execution Found", "data": []}
    ins = framework.postgresmodel.PostgresModel()
    index_statement_date = datetime.datetime.strptime(data.stmtdate, '%d-%m-%Y').strftime('%Y-%m-%d')
    tableName = f"{data.reconId}"
    reconsummary_query = {"family": "gl_recon_summary","species": "gl_recon_summary","GL_NUMBER": data.glnumber}
    params = framework.queryparams.QueryParams()
    params.limit = 10000
    params.q = json.dumps(reconsummary_query)
    try:
        resp = await ins.get_all(params, dbName, tableName)
        reconsummary_data = resp.get("data", [])
    except Exception:
        reconsummary_data = []
    return {"status": True, "message": "Success", "data": reconsummary_data}
