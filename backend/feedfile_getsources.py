from FeedFile_enum import *
from FeedFile_model import *
import fastapi
import recons_stdapi
import SourceReference_stdapi

router = fastapi.APIRouter(prefix='/feedfile')

@router.post('/getSources', tags=['FeedFile'])
async def FeedFilegetSources(data: getSourcesParams):
    sources = []
    # recondata = await recons_stdapi.Recons.get(data.reconId)
    recons_ins = recons_stdapi.Recons()
    newrecondef = await recons_ins.get(data.reconId, framework.settings.dbName)
    recondata =  newrecondef
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
        return {"status": True,"message": "Success", "data": sources, "reconName": recondata.get('reconName')}
    else:
        return {"status": False, "message": 'no sourcere details found in elastic', "data": [], "reconName": ""}
