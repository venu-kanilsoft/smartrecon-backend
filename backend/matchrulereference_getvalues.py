from MatchRuleReference_enum import *
from MatchRuleReference_model import *
import fastapi

router = fastapi.APIRouter(prefix='/matchrulereference')

@router.post('/getValues', tags=['MatchRuleReference'])
async def MatchRuleReferencegetValues(data: getValuesParams):
    ...