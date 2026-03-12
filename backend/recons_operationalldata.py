from recons_enum import *
from recons_model import *
import fastapi
import json

router = fastapi.APIRouter(prefix='/recons')

@router.post('/operationAllData', tags=['Recons'])
async def ReconsoperationAllData(data: operationAllDataParams):
    dbName = framework.settings.dbName
    ins = framework.postgresmodel.PostgresModel()
    index_statement_date = datetime.datetime.strptime(data.stmtdate, '%d-%m-%Y').strftime('%Y-%m-%d')
    tableName = f"{data.reconId}"
    query = {
            "query": {
                "exists": {
                "field": "SOURCE"
                }
            }
        }
    params = framework.queryparams.QueryParams()
    params.limit = 10001
    params.q = json.dumps(query)
    try:
        resp = await ins.get_all(params, dbName, tableName)
        print(resp)
        return {"status": True, "message": "Success", "data": resp.get("data", [])}
    except Exception as e:
        return {"status": True, "message": e, "data": []}
