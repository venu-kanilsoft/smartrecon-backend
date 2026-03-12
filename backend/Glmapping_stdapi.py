
import framework.postgresmodel
import framework.queryparams
import framework.types
from Glmapping_enum import *
from Glmapping_model import *
import fastapi
router = fastapi.APIRouter()


@router.post('/glmapping', response_model=Glmapping, tags=['Glmapping'])
async def create(inputObj: GlmappingCreate):
    
    return await inputObj.create()





@router.put('/glmapping', response_model=Glmapping, tags=['Glmapping'])
async def update(inputObj: Glmapping):
    
    
    return await inputObj.update()


@router.get('/glmapping/{id}', response_model=Glmapping, tags=['Glmapping'])
async def get(id: str):
    return await Glmapping.get(id)


@router.get('/glmapping', response_model=GlmappingGetResp, tags=['Glmapping'])
async def get_all(response: fastapi.Response, params = fastapi.Depends(framework.queryparams.QueryParams)):
    if params.download:
        response.headers['Content-Disposition'] = f'attachment; filename="glmapping.html"'
    return await Glmapping.get_all(params)


@router.delete('/glmapping/{id}', tags=['Glmapping'])
async def delete(id: str):
    return await Glmapping.delete(id)

