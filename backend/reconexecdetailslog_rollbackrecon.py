from ReconExecDetailsLog_enum import *
from ReconExecDetailsLog_model import *
import fastapi

router = fastapi.APIRouter(prefix='/reconexecdetailslog')

@router.post('/rollbackRecon', tags=['ReconExecDetailsLog'])
async def ReconExecDetailsLogrollbackRecon(data: rollbackReconParams):
    ...