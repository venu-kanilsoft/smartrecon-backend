from CustomReport_enum import *
from CustomReport_model import *
import fastapi

router = fastapi.APIRouter(prefix='/customreport')

@router.post('/getDailySettlementRpt', tags=['CustomReport'])
async def CustomReportgetDailySettlementRpt(data: getDailySettlementRptParams):
    ...