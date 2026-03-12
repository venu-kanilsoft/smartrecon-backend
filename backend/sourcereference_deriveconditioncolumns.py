from SourceReference_enum import *
from SourceReference_model import *
import fastapi

router = fastapi.APIRouter(prefix='/sourcereference')

@router.post('/deriveConditionColumns', tags=['SourceReference'])
async def SourceReferencederiveConditionColumns(data: deriveConditionColumnsParams):
    ...