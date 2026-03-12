from SourceReference_enum import *
from SourceReference_model import *
import fastapi

router = fastapi.APIRouter(prefix='/sourcereference')

@router.post('/skipRows', tags=['SourceReference'])
async def SourceReferenceskipRows(data: skipRowsParams):
    ...