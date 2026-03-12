
import framework.postgresmodel
import framework.queryparams
import framework.types
from ForceMatchCond_enum import *
from ForceMatchCond_model import *
import fastapi
router = fastapi.APIRouter()




@router.post('/forcematchcond', response_model=ForceMatchCond, tags=['ForceMatchCond'])
async def create(inputObj: ForceMatchCondCreate):
    
    return await inputObj.create()





@router.put('/forcematchcond', response_model=ForceMatchCond, tags=['ForceMatchCond'])
async def update(inputObj: ForceMatchCond):
    
    
    return await inputObj.update()


@router.get('/forcematchcond/{id}', response_model=ForceMatchCond, tags=['ForceMatchCond'])
async def get(id: str):
    return await ForceMatchCond.get(id)


@router.get('/forcematchcond', response_model=ForceMatchCondGetResp, tags=['ForceMatchCond'])
async def get_all(response: fastapi.Response, params = fastapi.Depends(framework.queryparams.QueryParams)):
    if params.download:
        response.headers['Content-Disposition'] = f'attachment; filename="forcematchcond.html"'
    return await ForceMatchCond.get_all(params)


@router.delete('/forcematchcond/{id}', tags=['ForceMatchCond'])
async def delete(id: str):
    return await ForceMatchCond.delete(id)

