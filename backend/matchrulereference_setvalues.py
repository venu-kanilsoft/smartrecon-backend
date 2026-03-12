from MatchRuleReference_enum import *
from MatchRuleReference_model import *
import fastapi

router = fastapi.APIRouter(prefix='/matchrulereference')

@router.post('/setValues', tags=['MatchRuleReference'])
async def MatchRuleReferencesetValues(data: setValuesParams):
    ...