
import framework.postgresmodel
import framework.queryparams
import framework.types
from ColumnDataTypes_enum import *
from ColumnDataTypes_model import *
import fastapi
router = fastapi.APIRouter()




@router.post('/columndatatypes', response_model=ColumnDataTypes, tags=['ColumnDataTypes'])
async def create(inputObj: ColumnDataTypesCreate):
    
    return await inputObj.create()





@router.put('/columndatatypes', response_model=ColumnDataTypes, tags=['ColumnDataTypes'])
async def update(inputObj: ColumnDataTypes):
    
    
    return await inputObj.update()


@router.get('/columndatatypes/{id}', response_model=ColumnDataTypes, tags=['ColumnDataTypes'])
async def get(id: str):
    return await ColumnDataTypes.get(id)


@router.get('/columndatatypes', response_model=ColumnDataTypesGetResp, tags=['ColumnDataTypes'])
async def get_all(response: fastapi.Response, params = fastapi.Depends(framework.queryparams.QueryParams)):
    if params.download:
        response.headers['Content-Disposition'] = f'attachment; filename="columndatatypes.html"'
    return await ColumnDataTypes.get_all(params)


@router.delete('/columndatatypes/{id}', tags=['ColumnDataTypes'])
async def delete(id: str):
    return await ColumnDataTypes.delete(id)

