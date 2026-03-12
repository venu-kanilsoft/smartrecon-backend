from CustomReport_enum import *
from CustomReport_model import *
import fastapi
import framework
import datetime
import reconexecdetailslog_getlatestexedetails
import pandas
import json
import jinja2
import CustomReport_stdapi

router = fastapi.APIRouter(prefix='/customreport')

@router.post('/generateReport', tags=['CustomReport'])
async def CustomReportloadReport(data: generateReportParams):
    payload = json.loads(data.records)
    outputPath = os.path.join(framework.settings.mftpath, 'downloads')
    if not os.path.exists(outputPath):
        os.makedirs(outputPath)
    writer = pandas.ExcelWriter(
                outputPath + "ConsolidatedReport.xlsx", engine="xlsxwriter"
            )
    
    for key, dataRecord in payload.items():
        CustomReport_stdapi.writeToExcel(
                        writer,
                        dataRecord,
                        data.sheetWise,
                        key,
                    )
            