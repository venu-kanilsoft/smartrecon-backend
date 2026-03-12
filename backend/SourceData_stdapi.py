
import framework.postgresmodel
import framework.queryparams
import framework.types
from SourceData_enum import *
from SourceData_model import *
import fastapi
router = fastapi.APIRouter()


@router.post('/sourcedata', response_model=SourceData, tags=['SourceData'])
async def create(inputObj: SourceDataCreate):
    
    return await inputObj.create()





@router.put('/sourcedata', response_model=SourceData, tags=['SourceData'])
async def update(inputObj: SourceData):
    
    
    return await inputObj.update()


@router.get('/sourcedata/{id}', response_model=SourceData, tags=['SourceData'])
async def get(id: str):
    return await SourceData.get(id)


@router.get('/sourcedata', response_model=SourceDataGetResp, tags=['SourceData'])
async def get_all(response: fastapi.Response, params = fastapi.Depends(framework.queryparams.QueryParams)):
    if params.download:
        response.headers['Content-Disposition'] = f'attachment; filename="sourcedata.html"'
    return await SourceData.get_all(params)


@router.delete('/sourcedata/{id}', tags=['SourceData'])
async def delete(id: str):
    return await SourceData.delete(id)

