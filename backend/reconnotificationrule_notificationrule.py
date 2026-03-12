from reconnotificationrule_enum import *
from reconnotificationrule_model import *
import fastapi

router = fastapi.APIRouter(prefix='/reconnotificationrule')

@router.post('/notificationRule', tags=['ReconNotificationRule'])
async def ReconNotificationRulenotificationRule(data: notificationRuleParams):
    ...