from recons_enum import *
from recons_model import *
import fastapi
import reconexecdetailslog_getlatestexedetails
import json
import pandas

router = fastapi.APIRouter(prefix='/recons')

@router.post('/getGlSummary', tags=['Recons'])
async def ReconsgetGlSummary(data: getGlSummaryParams):
    dbName = framework.settings.dbName
    print('StatementDate :',data.stmtdate)
    if not data.stmtdate:
        data1 = reconexecdetailslog_getlatestexedetails.getLatestExeDetailsParams
        data1.reconId = data.reconId
        doc = await reconexecdetailslog_getlatestexedetails.ReconExecDetailsLoggetLatestExeDetails(data1)
        print('stmtDate :',doc["data"][0].get('statementDate', None))
        if doc['status']:
            data.stmtdate = datetime.datetime.fromisoformat(
                    doc["data"][0].get('statementDate', None)).strftime('%d-%m-%Y')
        else:
            return {"status": False, "message": "No Latest Execution Found", "data": []}
    ins = framework.postgresmodel.PostgresModel()
    tableName = f"{data.reconId}"
    reconsummary_query = {
        "family": "gl_recon_summary", "species": "gl_recon_summary",
        "EXECUTION_STATEMENTDATE": datetime.datetime.strptime(data.stmtdate, '%d-%m-%Y').isoformat()
    }
    params = framework.queryparams.QueryParams()
    params.limit = 10000
    params.q = json.dumps(reconsummary_query)
    try:
        resp = await ins.get_all(params, dbName, tableName)
        reconsummary_data = resp.get("data", [])
    except Exception:
        reconsummary_data = []
    reconsummary_data = pandas.DataFrame(reconsummary_data)
    if 'Json Data' in reconsummary_data.columns:
        reconsummary_data = reconsummary_data.join(pandas.json_normalize(reconsummary_data['Json Data'])).drop(
            columns=['Json Data'])
    reconsummary_data = reconsummary_data.dropna(axis=1, how='all')
    reconsummary_data = reconsummary_data.fillna("")
    return {"status": True, "message": "Success", "data": reconsummary_data.to_dict(orient='records')}
