from SourceReference_enum import *
from SourceReference_model import *
import fastapi

router = fastapi.APIRouter(prefix='/sourcereference')

@router.post('/deriveColumns', tags=['SourceReference'])
async def SourceReferencederiveColumns(data: deriveColumnsParams):
    ...