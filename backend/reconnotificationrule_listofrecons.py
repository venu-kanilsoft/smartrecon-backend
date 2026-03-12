from reconnotificationrule_enum import *
from reconnotificationrule_model import *
import fastapi

router = fastapi.APIRouter(prefix='/reconnotificationrule')

@router.post('/listOfRecons', tags=['ReconNotificationRule'])
async def ReconNotificationRulelistOfRecons(data: listOfReconsParams):
    ...