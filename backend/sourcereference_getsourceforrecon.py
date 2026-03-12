from SourceReference_enum import *
from SourceReference_model import *
import fastapi

router = fastapi.APIRouter(prefix='/sourcereference')

@router.post('/getSourceForRecon', tags=['SourceReference'])
async def SourceReferencegetSourceForRecon(data: getSourceForReconParams):
    ...