
import framework.postgresmodel
import framework.queryparams
import framework.types
from reconexecution_enum import *
from reconexecution_model import *
import fastapi
router = fastapi.APIRouter()


@router.post('/reconexecution', response_model=ReconExecution, tags=['ReconExecution'])
async def create(inputObj: ReconExecutionCreate):
    
    return await inputObj.create()





@router.put('/reconexecution', response_model=ReconExecution, tags=['ReconExecution'])
async def update(inputObj: ReconExecution):
    
    
    return await inputObj.update()


@router.get('/reconexecution/{id}', response_model=ReconExecution, tags=['ReconExecution'])
async def get(id: str):
    return await ReconExecution.get(id)


@router.get('/reconexecution', response_model=ReconExecutionGetResp, tags=['ReconExecution'])
async def get_all(response: fastapi.Response, params = fastapi.Depends(framework.queryparams.QueryParams)):
    if params.download:
        response.headers['Content-Disposition'] = f'attachment; filename="reconexecution.html"'
    return await ReconExecution.get_all(params)


@router.delete('/reconexecution/{id}', tags=['ReconExecution'])
async def delete(id: str):
    return await ReconExecution.delete(id)

