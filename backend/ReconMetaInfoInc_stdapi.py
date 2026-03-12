
import framework.postgresmodel
import framework.queryparams
import framework.types
from ReconMetaInfoInc_enum import *
from ReconMetaInfoInc_model import *
import fastapi
router = fastapi.APIRouter()




@router.post('/reconmetainfoinc', response_model=ReconMetaInfoInc, tags=['ReconMetaInfoInc'])
async def create(inputObj: ReconMetaInfoIncCreate):
    
    return await inputObj.create()





@router.put('/reconmetainfoinc', response_model=ReconMetaInfoInc, tags=['ReconMetaInfoInc'])
async def update(inputObj: ReconMetaInfoInc):
    
    
    return await inputObj.update()


@router.get('/reconmetainfoinc/{id}', response_model=ReconMetaInfoInc, tags=['ReconMetaInfoInc'])
async def get(id: str):
    return await ReconMetaInfoInc.get(id)


@router.get('/reconmetainfoinc', response_model=ReconMetaInfoIncGetResp, tags=['ReconMetaInfoInc'])
async def get_all(response: fastapi.Response, params = fastapi.Depends(framework.queryparams.QueryParams)):
    if params.download:
        response.headers['Content-Disposition'] = f'attachment; filename="reconmetainfoinc.html"'
    return await ReconMetaInfoInc.get_all(params)


@router.delete('/reconmetainfoinc/{id}', tags=['ReconMetaInfoInc'])
async def delete(id: str):
    return await ReconMetaInfoInc.delete(id)

