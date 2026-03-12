
import framework.postgresmodel
import framework.queryparams
import framework.types
from reconnotificationrule_enum import *
from reconnotificationrule_model import *
import fastapi
router = fastapi.APIRouter()








@router.post('/reconnotificationrule', response_model=ReconNotificationRule, tags=['ReconNotificationRule'])
async def create(inputObj: ReconNotificationRuleCreate):
    
    return await inputObj.create()





@router.put('/reconnotificationrule', response_model=ReconNotificationRule, tags=['ReconNotificationRule'])
async def update(inputObj: ReconNotificationRule):
    
    
    return await inputObj.update()


@router.get('/reconnotificationrule/{id}', response_model=ReconNotificationRule, tags=['ReconNotificationRule'])
async def get(id: str):
    return await ReconNotificationRule.get(id)


@router.get('/reconnotificationrule', response_model=ReconNotificationRuleGetResp, tags=['ReconNotificationRule'])
async def get_all(response: fastapi.Response, params = fastapi.Depends(framework.queryparams.QueryParams)):
    if params.download:
        response.headers['Content-Disposition'] = f'attachment; filename="reconnotificationrule.html"'
    return await ReconNotificationRule.get_all(params)


@router.delete('/reconnotificationrule/{id}', tags=['ReconNotificationRule'])
async def delete(id: str):
    return await ReconNotificationRule.delete(id)

