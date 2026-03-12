from recons_enum import *
from recons_model import *
import fastapi

router = fastapi.APIRouter(prefix='/recons')

@router.post('/getDisplayColumns', tags=['Recons'])
async def ReconsgetDisplayColumns(data: getDisplayColumnsParams):
    ...