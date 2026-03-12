from recons_enum import *
from recons_model import *
import fastapi

router = fastapi.APIRouter(prefix='/recons')

@router.post('/processQueueRemarks', tags=['Recons'])
async def ReconsprocessQueueRemarks(data: processQueueRemarksParams):
    ...