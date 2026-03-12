from recons_enum import *
from recons_model import *
import fastapi
import recons_stdapi
import pandas
import json
import os
import traceback
import SystemAudit_stdapi
import recons_overwrite_sync_postgres_parquet

router = fastapi.APIRouter(prefix='/recons')


@router.post('/rollback_matched_records', tags=['Recons'])
async def Reconsrollback_matched_records(data: rollback_matched_recordsParams):
    processedrecords = 0
    resp = await recons_stdapi._check_recon_status(data.reconId)
    if not resp['status']:
        return {"status": False, "message": resp['message'], "data": []}
    else:
        stmtdate = resp['data']
    login_session = await framework.restapi.me()
    tableName = f"{data.reconId}"
    tableName = f"{data.reconId}_matched"
    #rollbackdf = pandas.DataFrame(json.loads(data.records))
    rollbackdf = await recons_stdapi.getBulkRecords(data.records, tableName)
    sources = rollbackdf['SOURCE'].unique().tolist()
    for source in sources:
        sourceDF = rollbackdf.loc[rollbackdf['SOURCE'] == source]
        if not sourceDF.empty:
            try:
                uniqueId = sourceDF['_id'].tolist()
                linkids = sourceDF['LINK_ID'].tolist()
                processedrecords += len(sourceDF)

                # Reading matching records
                listOfRecords = []
                #for eachId in uniqueId:
                #rbdf = await recons_stdapi.getRecords(eachId, tableName)
                #rbdf['Json Data']['UPDATED_BY'] = login_session.get('email', '')
                #rbdf['Json Data']['MATCHING_EXECUTION_STATE'] = "ROLLBACK_AUTH_WAITING"
                #rbdf['Json Data']['MATCHING_EXECUTION_STATUS'] = "WAITING FOR ROLLBACK AUTH"
                #rbdf['Json Data']['AUTHORIZATION_STATUS'] = "AUTHORIZED"
                #rbdf['family'] = "rollbackwaiting"
                #rbdf['species'] = "rollbackwaiting"
                #rbdf['Json Data']['FORCEMATCH_AUTHORIZATION'] = "ROLLBACK_AUTHORIZATION_PENDING"
                #rbdf['Json Data']["RESOLUTION_COMMENTS"] = data.comments
                #listOfRecords.append(rbdf)
                sourceDF['Json Data']=sourceDF['Json Data'].apply(lambda x: {**x, 'MATCHING_EXECUTION_STATUS': 'WAITING FOR ROLLBACK AUTH'})
                sourceDF['Json Data']=sourceDF['Json Data'].apply(lambda x: {**x, 'MATCHING_EXECUTION_STATE': 'ROLLBACK_AUTH_WAITING'})
                sourceDF['Json Data']=sourceDF['Json Data'].apply(lambda x: {**x, 'AUTHORIZATION_STATUS': 'AUTHORIZED'})
                sourceDF['Json Data']=sourceDF['Json Data'].apply(lambda x: {**x, 'FORCEMATCH_AUTHORIZATION': 'ROLLBACK_AUTHORIZATION_PENDING'})
                sourceDF['Json Data']=sourceDF['Json Data'].apply(lambda x: {**x, 'UPDATED_BY': login_session.get('email', '')})
                sourceDF['Json Data']=sourceDF['Json Data'].apply(lambda x: {**x, 'RESOLUTION_COMMENTS': data.comments})
                #sourceDF['LINK_ID'] = linkid
                sourceDF['family'] = "rollbackwaiting"
                sourceDF['species'] = "rollbackwaiting"
                resp = await recons_stdapi.updateRecords(sourceDF.to_dict(orient='records'), tableName)
                print(resp)
                filename = os.path.join(framework.settings.mftpath, 'OUTPUT', data.reconId, stmtdate, source + '.csv')
                # Reading matching records
                srcdata = pandas.read_csv(filename)
                rbdf = srcdata[srcdata['LINK_ID'].isin(linkids)]

                # removing roll back records from matched and saving
                srcdata = srcdata[~srcdata['LINK_ID'].isin(linkids)]
                srcdata.to_csv(filename, index=False)

                rbdf['UPDATED_BY'] = login_session.get('email', '')
                rbdf['MATCHING_EXECUTION_STATE'] = "ROLLBACK_AUTH_WAITING"
                rbdf['MATCHING_EXECUTION_STATUS'] = "WAITING FOR ROLLBACK AUTH"
                rbdf['AUTHORIZATION_STATUS'] = "AUTHORIZED"
                rbdf['FORCEMATCH_AUTHORIZATION'] = "ROLLBACK_AUTHORIZATION_PENDING"
                rbdf["RESOLUTION_COMMENTS"] = data.comments

                # saving the records to roll back auth waiting
                rollbackauthpend = os.path.join(framework.settings.mftpath, 'OUTPUT', data.reconId, stmtdate,
                                                source + '_rollbackauthpending.csv')
                if os.path.exists(rollbackauthpend):
                    rollbackauthdf = pandas.read_csv(rollbackauthpend)
                    if not rollbackauthdf.empty:
                        rollbackdf = pandas.concat([rollbackauthdf, rollbackdf])
                rbdf.to_csv(rollbackauthpend, index=False)

            except Exception as e:
                print(e)
                print(traceback.format_exc())
                return {"status": False, "message": e, "data": []}

    resp = await recons_stdapi._recomputereconsummary(data.reconId, stmtdate)
    recondata = await recons_stdapi.Recons.get(data.reconId)
    recondata = recondata

    sync_params = recons_overwrite_sync_postgres_parquet.overwrite_sync_postgres_parquetParams
    sync_params.reconId = data.reconId
    sync_params.exec_date = datetime.datetime.strptime(stmtdate, "%d%m%Y").strftime("%Y-%m-%d")
    sync_params.redis_queue = True
    await recons_overwrite_sync_postgres_parquet.Reconsoverwrite_sync_postgres_parquet(sync_params)

    if resp['status']:
        audit = {'type': 'Rollback',
                 'msg': f'{processedrecords} records rollbacked for {recondata.get("reconName", "")}',
                 'reason': 'Success', 'actionStatus': True, 'email':login_session.get('email', '')}
        status, msg = await SystemAudit_stdapi.create_auditLogs(audit)
        return {"status": True, "message": "Records Submitted for Roll Back"}
    else:
        audit = {'type': 'Rollback', 'msg': f'Rollback records failed due to {resp["message"]}',
                 'reason': 'Falied', 'actionStatus': False, 'email':login_session.get('email', '')}
        status, msg = await SystemAudit_stdapi.create_auditLogs(audit)
        return {"status": resp['status'], "message": resp['message']}
