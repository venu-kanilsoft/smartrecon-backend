from ReconExecDetailsLog_enum import *
from ReconExecDetailsLog_model import *
import fastapi

router = fastapi.APIRouter(prefix='/reconexecdetailslog')

@router.post('/getMaxReconExecutionDoc', tags=['ReconExecDetailsLog'])
async def ReconExecDetailsLoggetMaxReconExecutionDoc(data: getMaxReconExecutionDocParams):
    ...