
import framework.postgresmodel
import framework.queryparams
import framework.types
from Flows_enum import *
from Flows_model import *
import fastapi
router = fastapi.APIRouter()
















@router.post('/flows', response_model=Flows, tags=['Flows'])
async def create(inputObj: FlowsCreate):
    
    return await inputObj.create()





@router.put('/flows', response_model=Flows, tags=['Flows'])
async def update(inputObj: Flows):
    
    
    return await inputObj.update()


@router.get('/flows/{id}', response_model=Flows, tags=['Flows'])
async def get(id: str):
    return await Flows.get(id)


@router.get('/flows', response_model=FlowsGetResp, tags=['Flows'])
async def get_all(response: fastapi.Response, params = fastapi.Depends(framework.queryparams.QueryParams)):
    if params.download:
        response.headers['Content-Disposition'] = f'attachment; filename="flows.html"'
    return await Flows.get_all(params)


@router.delete('/flows/{id}', tags=['Flows'])
async def delete(id: str):
    return await Flows.delete(id)

