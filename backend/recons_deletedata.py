from recons_enum import *
from recons_model import *
import fastapi

router = fastapi.APIRouter(prefix='/recons')

@router.post('/deleteData', tags=['Recons'])
async def ReconsdeleteData(data: deleteDataParams):
    ...