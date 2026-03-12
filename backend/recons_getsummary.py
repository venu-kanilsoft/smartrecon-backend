from recons_enum import *
from recons_model import *
import fastapi
import framework
import json
import pandas
import recons_stdapi
import reconexecdetailslog_getlatestexedetails

router = fastapi.APIRouter(prefix='/recons')

@router.post('/getSummary', tags=['Recons'])
async def ReconsgetSummary(data: getSummaryParams):
    dbName = framework.settings.dbName
    if not data.stmtdate:
        data1 = reconexecdetailslog_getlatestexedetails.getLatestExeDetailsParams
        data1.reconId = data.reconId
        doc = await reconexecdetailslog_getlatestexedetails.ReconExecDetailsLoggetLatestExeDetails(data1)
        if doc['status']:
            data.stmtdate = doc["data"][0].get('statementDate', None).strftime('%d-%m-%Y')
        else:
            return {"status": False, "message": "No Latest Execution Found", "data": []}
    #if data.cyclewise:
    #    resp = await recons_stdapi._recomputereconsummary(data.reconId, datetime.datetime.strptime(data.stmtdate, '%d-%m-%Y').strftime('%d%m%Y'), data.cyclewise)
    #else:    
    # resp = await recons_stdapi._recomputereconsummary(data.reconId, datetime.datetime.strptime(data.stmtdate, '%d-%m-%Y').strftime('%d%m%Y'))
    ins = framework.postgresmodel.PostgresModel()
    index_statement_date = datetime.datetime.strptime(data.stmtdate, '%d-%m-%Y').strftime('%Y-%m-%d')
    tableName = f"{data.reconId}"
    tableName = "recon_summary"
    print('tableName', tableName)
    reconsummary_query = {"family": "recon_summary", "RECON_ID": data.reconId, "EXECUTION_STATEMENTDATE": datetime.datetime.strptime(data.stmtdate, '%d-%m-%Y').isoformat()}
    if data.cyclewise:
        reconsummary_query = {"species": str('recon_summary') + '_' + str('cyclewise'),"CycleWise": data.cyclewise}
    params = framework.queryparams.QueryParams()
    params.limit = 1000
    params.q = json.dumps(reconsummary_query)
    try:
        resp = await ins.get_all(params, dbName, tableName)
        print("The raw resp:", resp)
        reconsummary_data = resp.get("data", [])
        if not resp.get("data", []):
            return {"status": False, "message": "No Data Found For " + str(data.stmtdate) + " StatementDate", "data": []}
    except Exception:
        reconsummary_data = []
    print("reconsummary_data 1: ", reconsummary_data)
    reconsummary_data = pandas.DataFrame(reconsummary_data)
    print("reconsummary_data 2: ", reconsummary_data)
    # reconsummary_data = reconsummary_data.join(pandas.json_normalize(reconsummary_data['Json Data'])).drop(columns=['Json Data'])
    reconsummary_data['Statement Date'] = reconsummary_data['STATEMENT_DATE']
    reconsummary_data = reconsummary_data.dropna(axis=1, how='all')
    return {"status": True, "message": "Success", "data": reconsummary_data.to_dict(orient='records')}
