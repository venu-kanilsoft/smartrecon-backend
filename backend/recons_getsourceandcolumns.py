from recons_enum import *
from recons_model import *
import fastapi
import json
import SourceReference_stdapi

router = fastapi.APIRouter(prefix='/recons')

@router.post('/getSourceAndColumns', tags=['Recons'])
async def ReconsgetSourceAndColumns(data: getSourceAndColumnsParams):
    query = {"reconId": data.reconId}
    params = framework.queryparams.QueryParams()
    params.limit = 100
    params.skip = 0
    params.q = json.dumps(query)
    sourceins = SourceReference_stdapi.SourceReference()
    resp = await sourceins.get_all(params, framework.settings.dbName)
    resp = resp.get('data', [])
    doc = {}
    for each_source_ref in resp:
        doc[each_source_ref['source']] = []
        feeddetails = each_source_ref.get('feedDetails')
        for fd in feeddetails:
            if not isinstance(fd, dict):
                fd = fd.__dict__
            doc[each_source_ref['source']].append(fd['UIDisplayName'])
        doc[each_source_ref['source']] += each_source_ref['derivedColumns']
        doc[each_source_ref['source']] += ["SOURCE","STATEMENT_DATE", "System_Idx", "CARRY_FORWARD", "AGEING", "MATCHING_STATUS", "EXECUTION_STATEMENTDATE"]
    return {"status": True, "message": "Success", "data": doc}
