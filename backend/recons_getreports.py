from recons_enum import *
from recons_model import *
import fastapi
import json
import reconexecdetailslog_getlatestexedetails
import ReconMetaInfo_stdapi

router = fastapi.APIRouter(prefix='/recons')

@router.post('/getReports', tags=['Recons'])
async def ReconsgetReports(data: getReportsParams):
    dbName = framework.settings.dbName
    if not data.stmtdate:
        data1 = reconexecdetailslog_getlatestexedetails.getLatestExeDetailsParams
        data1.reconId = data.reconId
        resp = await reconexecdetailslog_getlatestexedetails.ReconExecDetailsLoggetLatestExeDetails(data1)
        recon_exec_data = resp.get('data', [])
        if not recon_exec_data:
            return {"status": False, "data": "Unable to find latest execution details"}
        recon_exec_data = recon_exec_data[0]
        #stmtdate = int(datetime.datetime.strptime(recon_exec_data['statementDate'], '%Y-%m-%dT%H:%M:%S').timestamp())
        stmtdate = int(recon_exec_data['statementDate'].timestamp())
    else:
        stmtdate = int(datetime.datetime.strptime(data.stmtdate, '%d-%m-%Y').timestamp())
    

    report_query = {"reconId": data.reconId,"stmtdate": stmtdate}
    if data.cyclewise:
        report_query = {"reconId": data.reconId,"stmtdate": stmtdate,"cycleWise": data.cyclewise}
    params = framework.queryparams.QueryParams()
    params.limit = 1
    params.q = json.dumps(report_query)
    params.sort = json.dumps({"updated": -1})
    dbName = framework.settings.dbName
    print('report_query', report_query)
    tableName = f"{dbName}_recon_meta_info"
    print('tableName :',tableName)
    reconmetadata = await ReconMetaInfo_stdapi.ReconMetaInfo().get_all(params, dbName, tableName)
    reconmetadata = reconmetadata.get('data',[])
    if reconmetadata:
        return {"status": True, "data": reconmetadata[0].get('reportDetails', [])}
    return {"status": True, "data": []}
