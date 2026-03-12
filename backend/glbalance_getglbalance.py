from GlBalance_enum import *
from GlBalance_model import *
import GlBalance_stdapi
import fastapi
import json
import pandas
import reconexecdetailslog_getlatestexedetails

router = fastapi.APIRouter(prefix='/glbalance')

@router.post('/getGlBalance', tags=['GlBalance'])
async def GlBalancegetGlBalance(data: getGlBalanceParams):
    dbName = framework.settings.dbName
    if not data.stmtdate:
        data1 = reconexecdetailslog_getlatestexedetails.getLatestExeDetailsParams
        data1.reconId = data.recon_id
        doc = await reconexecdetailslog_getlatestexedetails.ReconExecDetailsLoggetLatestExeDetails(data1)
        if doc['status']:
            data.stmtdate = doc["data"][0].get('statementDate', None).strftime('%d-%m-%Y')
        else:
            return {"status": False, "message": "No Latest Execution Found", "data": []}
    glbalance_query = {"reconId": data.recon_id,"AccountNumber": data.accnum,"stmtDate": datetime.datetime.strptime(data.stmtdate, '%d-%m-%Y').strftime('%d%m%Y')}
    params = framework.queryparams.QueryParams()
    params.limit = 1000
    params.q = json.dumps(glbalance_query)
    resp = await GlBalance_stdapi.GlBalance.get_all(params, framework.settings.dbName)

    doc = resp.get('data', [])
    df = pandas.DataFrame(doc, dtype='str')
    if not df.empty:
        if data.stmtdate:
            stmtdate = datetime.datetime.strptime(data.stmtdate, '%d-%m-%Y').strftime('%d%m%Y')
            df = df[df['stmtDate'] == stmtdate]
            df = df.drop_duplicates(subset=['reconId','reconName','stmtDate','AccountNumber','OPENING_BAL','CLOSING_BAL'])
            df['stmtDate'] = df['stmtDate'].apply(lambda x: datetime.datetime.strptime(x, '%d%m%Y').strftime('%d-%m-%Y'))
    return {"status":True, "message": "Success", "data": df.to_json(orient='records')}
