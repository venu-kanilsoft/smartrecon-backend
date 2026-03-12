from SourceReference_enum import *
from SourceReference_model import *
import fastapi

router = fastapi.APIRouter(prefix='/sourcereference')

@router.post('/loadSourceRef', tags=['SourceReference'])
async def SourceReferenceloadSourceRef(data: loadSourceRefParams):
    ...