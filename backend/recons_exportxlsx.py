from recons_enum import *
from recons_model import *
import fastapi

router = fastapi.APIRouter(prefix='/recons')

@router.post('/exportXlsx', tags=['Recons'])
async def ReconsexportXlsx(data: exportXlsxParams):
    ...