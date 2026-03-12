from Flows_enum import *
from Flows_model import *
import fastapi

router = fastapi.APIRouter(prefix='/flows')

@router.post('/generateFlow', tags=['Flows'])
async def FlowsgenerateFlow(data: generateFlowParams):
    ...