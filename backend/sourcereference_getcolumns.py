from SourceReference_enum import *
from SourceReference_model import *
import fastapi

router = fastapi.APIRouter(prefix='/sourcereference')

@router.post('/getColumns', tags=['SourceReference'])
async def SourceReferencegetColumns(data: getColumnsParams):
    ...