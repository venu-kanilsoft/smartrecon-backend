from MatchRuleReference_enum import *
from MatchRuleReference_model import *
import fastapi

router = fastapi.APIRouter(prefix='/matchrulereference')

@router.post('/saveMatchRule', tags=['MatchRuleReference'])
async def MatchRuleReferencesaveMatchRule(data: saveMatchRuleParams):
    ...