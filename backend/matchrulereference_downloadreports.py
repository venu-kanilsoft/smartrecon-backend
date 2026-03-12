from MatchRuleReference_enum import *
from MatchRuleReference_model import *
import fastapi

router = fastapi.APIRouter(prefix='/matchrulereference')

@router.post('/downloadReports', tags=['MatchRuleReference'])
async def MatchRuleReferencedownloadReports(data: downloadReportsParams):
    ...