from recons_enum import *
from recons_model import *
import fastapi

router = fastapi.APIRouter(prefix='/recons')

@router.post('/downloadBalance', tags=['Recons'])
async def ReconsdownloadBalance(data: downloadBalanceParams):
    ...