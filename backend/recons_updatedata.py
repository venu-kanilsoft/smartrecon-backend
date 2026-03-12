from recons_enum import *
from recons_model import *
import fastapi
import pandas
import json
import datetime
import reconexecdetailslog_getlatestexedetails
import recons_stdapi

router = fastapi.APIRouter(prefix='/recons')

@router.post('/updateData', tags=['Recons'])
async def ReconsupdateData(data: updateDataParams):
    ins = framework.postgresmodel.PostgresModel()
    dbName = framework.settings.dbName
    login_session = await framework.restapi.me()
    filenamemapping = {'matched': '.csv', 'unmatched': '_UnMatched.csv', 'authwaiting': '_authwaiting.csv',
                        'rollbackwaiting': '_rollbackauthpending.csv', 'reversal': '_Self_Matched.csv'}
    if not data.stmtdate:
        data1 = reconexecdetailslog_getlatestexedetails.getLatestExeDetailsParams
        data1.reconId = data.reconId
        doc = await reconexecdetailslog_getlatestexedetails.ReconExecDetailsLoggetLatestExeDetails(data1)
        if doc['status']:
            data.stmtdate = datetime.datetime.fromisoformat(
                    doc["data"][0].get('statementDate', None)).strftime('%d%m%Y')
        else:
            return {"status": False, "message": "No Latest Execution Found", "data": []}
    else:
        data.stmtdate = datetime.datetime.strptime(data.stmtdate, '%d-%m-%Y').strftime('%d%m%Y')
    index_statement_date = datetime.datetime.strptime(data.stmtdate, "%d%m%Y").strftime("%Y-%m-%d")
    tableName = f"{data.reconId}"
    records_df = pandas.DataFrame(json.loads(data.records))
    sources = records_df['SOURCE'].unique().tolist()
    for source in sources:
        sourceDF = records_df.loc[records_df['SOURCE'] == source]
        if not sourceDF.empty:
            # linkids = sourceDF['LINK_ID'].tolist()
            system_idx = sourceDF['System_Idx'].tolist()
            
            resp = await recons_stdapi._get_data(data.reconId, data.stmtdate, data.operations, source=source, ui_data=True)
            if not resp['status']:
                return {"status": resp['status'], "message": resp['message'], "data": []}

            # Reading the original source data
            sourcedata = pandas.DataFrame(resp['data'])
            # updateDataDf = sourcedata[sourcedata['LINK_ID'].isin(linkids)]
            updateDataDf = sourcedata[sourcedata['System_Idx'].isin(system_idx)]
            for system in system_idx:
                updateDataDf.loc[updateDataDf['System_Idx'] == system, 'Ops Remarks'] = records_df.loc[records_df['System_Idx'] == system]['Ops Remarks']
                updateDataDf.loc[updateDataDf['System_Idx'] == system, 'Recon Remarks'] = records_df.loc[records_df['System_Idx'] == system]['Recon Remarks']
            updateDataDf['Remarks UpdatedBy'] = login_session.get('email', '')
            updateDataDf['Remarks Updated DateTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if '_id' in updateDataDf.columns:
                del updateDataDf['_id']
            if 'id' in updateDataDf.columns:
                del updateDataDf['id']
            status = await ins.insert_df(
                                updateDataDf,
                                "System_Idx",
                                family=data.operations,
                                species=data.operations,
                                indexName=tableName,
                            )
        else:
            return {"status":False, "message":"Records Not Found", "data":[]}
    return {"status": True, "message": "Successfully Updated Record", "data": []}
