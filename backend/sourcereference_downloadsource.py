from SourceReference_enum import *
from SourceReference_model import *
import fastapi

router = fastapi.APIRouter(prefix='/sourcereference')

@router.post('/downloadSource', tags=['SourceReference'])
async def SourceReferencedownloadSource(data: downloadSourceParams):
    ...