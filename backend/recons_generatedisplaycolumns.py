from recons_enum import *
from recons_model import *
import fastapi

router = fastapi.APIRouter(prefix='/recons')

@router.post('/generateDisplayColumns', tags=['Recons'])
async def ReconsgenerateDisplayColumns(data: generateDisplayColumnsParams):
    ...