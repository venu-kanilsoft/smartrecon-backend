from recons_enum import *
from recons_model import *
import fastapi

router = fastapi.APIRouter(prefix='/recons')

@router.post('/processRecon', tags=['Recons'])
async def ReconsprocessRecon(data: processReconParams):
    ...