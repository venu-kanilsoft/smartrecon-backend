from SourceReference_enum import *
from SourceReference_model import *
import fastapi

router = fastapi.APIRouter(prefix='/sourcereference')

@router.post('/deleteSource', tags=['SourceReference'])
async def SourceReferencedeleteSource(data: deleteSourceParams):
    ...