
import framework.postgresmodel
import framework.queryparams
import framework.types
from CustomReport_enum import *
from CustomReport_model import *
import fastapi
import jinja2
import json
import pandas
router = fastapi.APIRouter()




@router.post('/customreport', response_model=CustomReport, tags=['CustomReport'])
async def create(inputObj: CustomReportCreate):
    
    return await inputObj.create()





@router.put('/customreport', response_model=CustomReport, tags=['CustomReport'])
async def update(inputObj: CustomReport):
    
    
    return await inputObj.update()


@router.get('/customreport/{id}', response_model=CustomReport, tags=['CustomReport'])
async def get(id: str):
    return await CustomReport.get(id)


@router.get('/customreport', response_model=CustomReportGetResp, tags=['CustomReport'])
async def get_all(response: fastapi.Response, params = fastapi.Depends(framework.queryparams.QueryParams)):
    if params.download:
        response.headers['Content-Disposition'] = f'attachment; filename="customreport.html"'
    return await CustomReport.get_all(params)


@router.delete('/customreport/{id}', tags=['CustomReport'])
async def delete(id: str):
    return await CustomReport.delete(id)


async def _generate_template(self, table_headers, table_data, block_data, stats_counts={}):
    """
    Generate report table

    :param table_headers: table header info
    :param table_data: result data
    :returns: table html
    """
    file_loader = jinja2.FileSystemLoader(self.reportTemplatePath)
    env = jinja2.Environment(loader=file_loader,
                                autoescape=jinja2.select_autoescape(enabled_extensions=('xml'),
                                                                    default_for_string=True))
    template = env.get_template('table_report.html')
    report_data = {"table_headers": table_headers,
                    "table_data": table_data,
                    "block_data": block_data,
                    "stats_counts": stats_counts}
    template = template.render(report_data=report_data)
    template += "<br>"
    return True, template

async def getBlockDetails(self, blockName):
    """
    Get component  details
    :param blockName: component name
    :returns: component details
    """
    file_name = os.path.join(self.reportTemplatePath + "/tableWidgets", blockName + ".json")
    if not os.path.exists(file_name):
        file_name = os.path.join(self.reportTemplatePath + "/graphWidgets", blockName + ".json")
        if not os.path.exists(file_name):
            return False, "Block Details Not Available"
    with open(file_name) as fopen:
        return True, json.load(fopen)


async def writeToExcel(self, excelWriter=None, dataframe=None, exportType=False, key=""):
    if exportType:
        dataframe.to_excel(
            excelWriter, sheet_name=key, index=False, engine="xlsxwriter"
        )
        worksheet = excelWriter.sheets[key]  # pull worksheet object
        for idx, col in enumerate(dataframe):  # loop through all columns
            series = dataframe[col]
            max_len = (
                max(
                    (
                        series.astype(str).map(len).max(),  # len of largest item
                        len(str(series.name)),  # len of column name/header
                    )
                )
                + 1
            )  # adding a little extra space
            worksheet.set_column(idx, idx, max_len)  # set column width
    else:
        row = 0
        spaces = 1
        header_row = pandas.DataFrame([{"header": key}])
        header_row.to_excel(
            excelWriter,
            sheet_name=key,
            startrow=row,
            startcol=0,
            index=False,
            header=None,
        )
        row += 1
        dataframe.to_excel(
            excelWriter, sheet_name=key, startrow=row, startcol=0, index=False
        )
        row = row + len(dataframe.index) + spaces + 1
