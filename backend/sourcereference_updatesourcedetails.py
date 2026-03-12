from SourceReference_enum import *
from SourceReference_model import *
import fastapi

router = fastapi.APIRouter(prefix='/sourcereference')

@router.post('/updateSourceDetails', tags=['SourceReference'])
async def SourceReferenceupdateSourceDetails(data: updateSourceDetailsParams):
    ...