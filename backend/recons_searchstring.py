from recons_enum import *
from recons_model import *
import fastapi
import pandas
import json
import reconexecdetailslog_getlatestexedetails
import recons_stdapi
import SourceReference_stdapi
from dateutil.relativedelta import relativedelta

router = fastapi.APIRouter(prefix='/recons')

@router.post('/searchString', tags=['Recons'])
async def ReconssearchString(data: searchStringParams):
    dbName = framework.settings.dbName
    recons_ins = recons_stdapi.Recons()
    recons_resp = await getAllData(recons_ins)
    recons=[]
    for val in recons_resp:
        if str(data.search_string).lower() in val.get('reconProcess').lower() or str(data.search_string).lower() in val.get('reconName').lower() or str(data.search_string).lower() in val.get('reconId').lower():
            recons.append(val)
    return {"status":True, "message":"Success", "data":recons}

async def getSources(reconId):
    sources = []
    recondata = await recons_stdapi.Recons.get(reconId)
    recondata = recondata
    if not recondata:
        return {"status": False, "message":"Unable to find recon details", "data": []}
    reconsources = recondata.get('sources', [])
    if not reconsources:
        return {"status": False, "message": "Sources are not configured.", "data": []}
    for src in reconsources:
        resp = await SourceReference_stdapi.SourceReference.get(src)
        sourceref = resp
        if not sourceref:
            continue
        sources.append(sourceref.get('source', ''))
    if len(sources)>0:
        return {"status": True,"message": "Success", "data": sources}
    else:
        return {"status": False, "message": 'no sourcere details found in elastic', "data": []}
    
async def getAllData(connection, query={}, skip=0, limit=200, fields=None, sort={"updated": -1}):
    params = framework.queryparams.QueryParams()
    params.limit = limit
    params.q = json.dumps(query)
    params.sort = json.dumps(sort)
    params.fields = fields
    resp = await connection.get_all(params, framework.settings.dbName)
    return resp['data']