
import framework.postgresmodel
import framework.queryparams
import framework.types
from ReconExecDetailsLog_enum import *
from ReconExecDetailsLog_model import *
import fastapi
router = fastapi.APIRouter()




@router.post('/reconexecdetailslog', response_model=ReconExecDetailsLog, tags=['ReconExecDetailsLog'])
async def create(inputObj: ReconExecDetailsLogCreate):
    
    return await inputObj.create()





@router.put('/reconexecdetailslog', response_model=ReconExecDetailsLog, tags=['ReconExecDetailsLog'])
async def update(inputObj: ReconExecDetailsLog):
    
    
    return await inputObj.update()


@router.get('/reconexecdetailslog/{id}', response_model=ReconExecDetailsLog, tags=['ReconExecDetailsLog'])
async def get(id: str):
    return await ReconExecDetailsLog.get(id)


@router.get('/reconexecdetailslog', response_model=ReconExecDetailsLogGetResp, tags=['ReconExecDetailsLog'])
async def get_all(response: fastapi.Response, params = fastapi.Depends(framework.queryparams.QueryParams)):
    if params.download:
        response.headers['Content-Disposition'] = f'attachment; filename="reconexecdetailslog.html"'
    return await ReconExecDetailsLog.get_all(params)


@router.delete('/reconexecdetailslog/{id}', tags=['ReconExecDetailsLog'])
async def delete(id: str):
    return await ReconExecDetailsLog.delete(id)

