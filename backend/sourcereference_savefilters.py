from SourceReference_enum import *
from SourceReference_model import *
import fastapi

router = fastapi.APIRouter(prefix='/sourcereference')

@router.post('/saveFilters', tags=['SourceReference'])
async def SourceReferencesaveFilters(data: saveFiltersParams):
    ...