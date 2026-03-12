
import framework.postgresmodel
import framework.queryparams
import framework.types
from GlBalance_enum import *
from GlBalance_model import *
import fastapi
router = fastapi.APIRouter()


@router.post('/glbalance', response_model=GlBalance, tags=['GlBalance'])
async def create(inputObj: GlBalanceCreate):
    
    return await inputObj.create()





@router.put('/glbalance', response_model=GlBalance, tags=['GlBalance'])
async def update(inputObj: GlBalance):
    
    
    return await inputObj.update()


@router.get('/glbalance/{id}', response_model=GlBalance, tags=['GlBalance'])
async def get(id: str):
    return await GlBalance.get(id)


@router.get('/glbalance', response_model=GlBalanceGetResp, tags=['GlBalance'])
async def get_all(response: fastapi.Response, params = fastapi.Depends(framework.queryparams.QueryParams)):
    if params.download:
        response.headers['Content-Disposition'] = f'attachment; filename="glbalance.html"'
    return await GlBalance.get_all(params)


@router.delete('/glbalance/{id}', tags=['GlBalance'])
async def delete(id: str):
    return await GlBalance.delete(id)

