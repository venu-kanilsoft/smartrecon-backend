from SourceReference_enum import *
from SourceReference_model import *
import fastapi

router = fastapi.APIRouter(prefix='/sourcereference')

@router.post('/loadSampleFile', tags=['SourceReference'])
async def SourceReferenceloadSampleFile(data: loadSampleFileParams):
    ...