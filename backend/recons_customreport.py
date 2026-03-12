from recons_enum import *
from recons_model import *
import fastapi

router = fastapi.APIRouter(prefix='/recons')

@router.post('/customReport', tags=['Recons'])
async def ReconscustomReport(data: customReportParams):
    ...