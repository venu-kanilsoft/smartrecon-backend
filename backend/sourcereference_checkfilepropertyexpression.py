from SourceReference_enum import *
from SourceReference_model import *
import fastapi

router = fastapi.APIRouter(prefix='/sourcereference')

@router.post('/checkFilePropertyExpression', tags=['SourceReference'])
async def SourceReferencecheckFilePropertyExpression(data: checkFilePropertyExpressionParams):
    ...