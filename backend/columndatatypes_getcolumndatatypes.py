from ColumnDataTypes_enum import *
from ColumnDataTypes_model import *
import fastapi

router = fastapi.APIRouter(prefix='/columndatatypes')

@router.post('/getColumnDataTypes', tags=['ColumnDataTypes'])
async def ColumnDataTypesgetColumnDataTypes(data: getColumnDataTypesParams):
    ...