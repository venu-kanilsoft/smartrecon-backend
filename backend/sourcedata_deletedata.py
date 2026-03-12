from SourceData_enum import *
from SourceData_model import *
import fastapi

router = fastapi.APIRouter(prefix='/sourcedata')

@router.post('/deleteData', tags=['SourceData'])
async def SourceDatadeleteData(data: deleteDataParams):
    ...