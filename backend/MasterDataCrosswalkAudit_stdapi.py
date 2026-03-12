
import framework.postgresmodel
import framework.queryparams
import framework.types
from MasterDataCrosswalkAudit_enum import *
from MasterDataCrosswalkAudit_model import *
import fastapi
router = fastapi.APIRouter()


@router.post('/masterdatacrosswalkaudit', response_model=MasterDataCrosswalkAudit, tags=['MasterDataCrosswalkAudit'])
async def create(inputObj: MasterDataCrosswalkAuditCreate):
    
    return await inputObj.create()





@router.put('/masterdatacrosswalkaudit', response_model=MasterDataCrosswalkAudit, tags=['MasterDataCrosswalkAudit'])
async def update(inputObj: MasterDataCrosswalkAudit):
    
    
    return await inputObj.update()


@router.get('/masterdatacrosswalkaudit/{id}', response_model=MasterDataCrosswalkAudit, tags=['MasterDataCrosswalkAudit'])
async def get(id: str):
    return await MasterDataCrosswalkAudit.get(id)


@router.get('/masterdatacrosswalkaudit', response_model=MasterDataCrosswalkAuditGetResp, tags=['MasterDataCrosswalkAudit'])
async def get_all(response: fastapi.Response, params = fastapi.Depends(framework.queryparams.QueryParams)):
    if params.download:
        response.headers['Content-Disposition'] = f'attachment; filename="masterdatacrosswalkaudit.html"'
    return await MasterDataCrosswalkAudit.get_all(params)


@router.delete('/masterdatacrosswalkaudit/{id}', tags=['MasterDataCrosswalkAudit'])
async def delete(id: str):
    return await MasterDataCrosswalkAudit.delete(id)

