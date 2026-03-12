from ReconExecDetailsLog_enum import *
from ReconExecDetailsLog_model import *
import fastapi

router = fastapi.APIRouter(prefix='/reconexecdetailslog')

@router.post('/get_latest_execution_details', tags=['ReconExecDetailsLog'])
async def ReconExecDetailsLogget_latest_execution_details(data: get_latest_execution_detailsParams):
    ...