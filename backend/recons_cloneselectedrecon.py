from recons_enum import *
from recons_model import *
import fastapi

router = fastapi.APIRouter(prefix='/recons')

@router.post('/cloneSelectedRecon', tags=['Recons'])
async def ReconscloneSelectedRecon(data: cloneSelectedReconParams):
    ...