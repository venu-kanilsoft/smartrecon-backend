from MatchRuleReference_enum import *
from MatchRuleReference_model import *
import fastapi

router = fastapi.APIRouter(prefix='/matchrulereference')

@router.post('/getSelectedColumns', tags=['MatchRuleReference'])
async def MatchRuleReferencegetSelectedColumns(data: getSelectedColumnsParams):
    ...