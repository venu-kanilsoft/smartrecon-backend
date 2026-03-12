from SourceReference_enum import *
from SourceReference_model import *
import fastapi

router = fastapi.APIRouter(prefix='/sourcereference')

@router.post('/addSourceRef', tags=['SourceReference'])
async def SourceReferenceaddSourceRef(data: addSourceRefParams):
    ...