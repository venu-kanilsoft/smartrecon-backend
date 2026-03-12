from recons_enum import *
from recons_model import *
import fastapi

router = fastapi.APIRouter(prefix='/recons')

@router.post('/saveRecon', tags=['Recons'])
async def ReconssaveRecon(data: saveReconParams):
    ...