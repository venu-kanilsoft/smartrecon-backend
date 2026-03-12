from recons_enum import *
from recons_model import *
import fastapi
import recons_stdapi
import datetime
import pandas
import json
import uuid
import os
import traceback
import SystemAudit_stdapi
import recons_overwrite_sync_postgres_parquet

router = fastapi.APIRouter(prefix='/recons')


@router.post('/force_match_records', tags=['Recons'])
async def Reconsforce_match_records(data: force_match_recordsParams):
    processedrecords = 0
    login_session = await framework.restapi.me()
    resp = await recons_stdapi._check_recon_status(data.reconId)
    if not resp['status']:
        return {"status": False, "message": resp['message'], "data": []}
    else:
        stmtdate = resp['data']

    tableName = f"{data.reconId}"
    tableName = f"{data.reconId}_unmatched"
    # forced_records_df = pandas.DataFrame(json.loads(data.records))
    forced_records_df = await recons_stdapi.getBulkRecords(data.records, tableName)
    linkid = str(uuid.uuid4().hex)
    sources = forced_records_df['SOURCE'].unique().tolist()
    for source in sources:
        sourceDF = forced_records_df.loc[forced_records_df['SOURCE'] == source]
        if not sourceDF.empty:
            try:
                uniqueId = sourceDF['_id'].tolist()
                linkids = sourceDF['LINK_ID'].unique().tolist()
                processedrecords += len(sourceDF)
                listOfRecords = []
                # for eachId in uniqueId:
                # forceMatchDf = await recons_stdapi.getRecords(eachId, tableName)
                # saving the removed records to authwaiting/submissionpending
                # forceMatchDf['Json Data']["MATCHING_EXECUTION_STATUS"] = "WAITING FOR AUTHORIZATION"
                # forceMatchDf['Json Data']["FORCEMATCH_AUTHORIZATION"] = "WAITING_FOR_AUTHORIZATION"
                # forceMatchDf['Json Data']['UPDATED_BY'] = login_session.get('email', '')
                # forceMatchDf['Json Data']['RESOLUTION_COMMENTS'] = data.comments
                # forceMatchDf['LINK_ID'] = linkid
                # forceMatchDf['family'] = "authwaiting"
                # forceMatchDf['species'] = "authwaiting"
                # forceMatchDf['Json Data']['MATCH LINK_ID'] = linkid
                sourceDF['Json Data'] = sourceDF['Json Data'].apply(lambda x: {**x, 'MATCHING_EXECUTION_STATUS': 'WAITING FOR AUTHORIZATION'})
                sourceDF['Json Data'] = sourceDF['Json Data'].apply(lambda x: {**x, 'FORCEMATCH_AUTHORIZATION': 'WAITING FOR AUTHORIZATION'})
                sourceDF['Json Data'] = sourceDF['Json Data'].apply(lambda x: {**x, 'UPDATED_BY': login_session.get('email', '')})
                sourceDF['Json Data'] = sourceDF['Json Data'].apply(lambda x: {**x, 'RESOLUTION_COMMENTS': data.comments})
                sourceDF['LINK_ID'] = linkid
                sourceDF['family'] = "authwaiting"
                sourceDF['species'] = "authwaiting"
                sourceDF['Json Data']=sourceDF['Json Data'].apply(lambda x: {**x, 'MATCH LINK_ID': linkid})
                # listOfRecords.append(forceMatchDf)
                resp = await recons_stdapi.updateRecords(sourceDF.to_dict(orient='records'), tableName)
                print("updated")
                srcfilename = os.path.join(framework.settings.mftpath, 'OUTPUT', data.reconId, stmtdate,
                                           source + '_UnMatched.csv')
                if not os.path.exists(srcfilename):
                    continue
                sourcedata = pandas.read_csv(srcfilename)
                forceMatchDf = sourcedata[sourcedata['LINK_ID'].isin(linkids)]
                sourcedata = sourcedata[~sourcedata['LINK_ID'].isin(linkids)]
                sourcedata.to_csv(srcfilename, index=False)
                # saving the removed records to authwaiting/submissionpending
                authfilename = os.path.join(framework.settings.mftpath, 'OUTPUT', data.reconId, stmtdate,
                                            source + '_authwaiting.csv')
                forceMatchDf["MATCHING_EXECUTION_STATUS"] = "WAITING FOR AUTHORIZATION"
                forceMatchDf["FORCEMATCH_AUTHORIZATION"] = "WAITING_FOR_AUTHORIZATION"
                forceMatchDf['UPDATED_BY'] = login_session.get('email', '')
                forceMatchDf['RESOLUTION_COMMENTS'] = data.comments
                forceMatchDf['LINK_ID'] = linkid
                # If the file already exists need to append the new records
                if os.path.exists(authfilename):
                    authdf = pandas.read_csv(authfilename)
                    if not authdf.empty:
                        forceMatchDf = pandas.concat([authdf, forceMatchDf])
                forceMatchDf.to_csv(authfilename, index=False)
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
        audit = {'type': 'Force Match',
                 'msg': f'{processedrecords} records force matched for {recondata.get("reconName", "")}',
                 'reason': 'Success', 'actionStatus': True, 'email': login_session.get('email', '')}
        status, msg = await SystemAudit_stdapi.create_auditLogs(audit)
        return {"status": True, "message": "Records Submitted for Authorization"}
    else:
        audit = {'type': 'Force Match', 'msg': f'Force match failed due to {resp["message"]}',
                 'reason': resp['status'], 'actionStatus': False, 'email': login_session.get('email', '')}
        status, msg = await SystemAudit_stdapi.create_auditLogs(audit)
        return {"status": resp['status'], "message": resp['message']}
