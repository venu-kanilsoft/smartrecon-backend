
import framework.postgresmodel
import framework.queryparams
import framework.types
from SystemAudit_enum import *
from SystemAudit_model import *
import fastapi
router = fastapi.APIRouter()


@router.post('/systemaudit', response_model=SystemAudit, tags=['SystemAudit'])
async def create(inputObj: SystemAuditCreate):
    
    return await inputObj.create()





@router.put('/systemaudit', response_model=SystemAudit, tags=['SystemAudit'])
async def update(inputObj: SystemAudit):
    
    
    return await inputObj.update()


@router.get('/systemaudit/{id}', response_model=SystemAudit, tags=['SystemAudit'])
async def get(id: str):
    return await SystemAudit.get(id)


@router.get('/systemaudit', response_model=SystemAuditGetResp, tags=['SystemAudit'])
async def get_all(response: fastapi.Response, params = fastapi.Depends(framework.queryparams.QueryParams)):
    if params.download:
        response.headers['Content-Disposition'] = f'attachment; filename="systemaudit.html"'
    return await SystemAudit.get_all(params)


@router.delete('/systemaudit/{id}', tags=['SystemAudit'])
async def delete(id: str):
    return await SystemAudit.delete(id)



async def create_auditLogs(doc: dict):
    if not doc.get('email'):
        login_session = await framework.restapi.me()
        doc['email'] = login_session.get('email', '')
    data_object = SystemAudit().parse_obj(doc)
    await data_object.create(framework.settings.dbName)
    return True, "Created"