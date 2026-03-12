from recons_enum import *
from recons_model import *
import fastapi
import pandas
import json
import os
import recons_stdapi
import SystemAudit_stdapi
import recons_overwrite_sync_postgres_parquet

router = fastapi.APIRouter(prefix='/recons')


@router.post('/authorize_rollback_records', tags=['Recons'])
async def Reconsauthorize_rollback_records(data: authorize_rollback_recordsParams):
    processedrecords = 0
    resp = await recons_stdapi._check_recon_status(data.reconId)
    if not resp['status']:
        return {"status": False, "message": resp['message'], "data": []}
    else:
        stmtdate = resp['data']

    tableName = f"{data.reconId}"
    tableName = f"{data.reconId}_matched"
    #rollbackdf = pandas.DataFrame(json.loads(data.records))
    #createdby = rollbackdf['UPDATED_BY'].unique()
    rollbackdf = await recons_stdapi.getBulkRecords(data.records, tableName)
    print(rollbackdf.columns)
    print(rollbackdf)
    createdby = rollbackdf['Json Data'].apply(lambda x: extract_key_value(x, 'UPDATED_BY')).tolist()
    login_session = await framework.restapi.me()

    print('tableName', tableName)
    if login_session.get('email', '') in createdby:
        return {"status": False,
                "message": 'Selected records are sent for rollback by You, so Rollback Authorization not allowed',
                "data": []}

    sources = rollbackdf['SOURCE'].unique().tolist()
    for source in sources:
        sourceDF = rollbackdf.loc[rollbackdf['SOURCE'] == source]
        if not sourceDF.empty:
            # try:
            listOfRecords = []
            uniqueId = sourceDF['_id'].tolist()
            linkids = sourceDF['LINK_ID'].tolist()
            processedrecords += len(sourceDF)
            #for eachId in uniqueId:
            #unmatchdf = await recons_stdapi.getRecords(eachId, tableName)
            #unmatchdf['Json Data']['UPDATED_BY'] = login_session.get('email', '')
            #unmatchdf['Json Data']["RESOLUTION_COMMENTS"] = data.comments
            #unmatchdf['family'] = "unmatched"
            #unmatchdf['species'] = "unmatched"
            #unmatchdf["MATCHING_STATUS"] = "UNMATCHED"
            #unmatchdf['Json Data']["RECONCILIATION_STATUS"] = "EXCEPTION"
            #listOfRecords.append(unmatchdf)
            sourceDF['Json Data']=sourceDF['Json Data'].apply(lambda x: {**x, 'RECONCILIATION_STATUS': 'EXCEPTION'})
            sourceDF['Json Data']=sourceDF['Json Data'].apply(lambda x: {**x, 'UPDATED_BY': login_session.get('email', '')})
            sourceDF['Json Data']=sourceDF['Json Data'].apply(lambda x: {**x, 'RESOLUTION_COMMENTS': data.comments})
            sourceDF['MATCHING_STATUS'] = "UNMATCHED"
            sourceDF['family'] = "unmatched"
            sourceDF['species'] = "unmatched"
            # resp = await recons_stdapi.updateRecords(listOfRecords, tableName)
            await recons_stdapi.deleteRecords(uniqueId, tableName)
            resp = await recons_stdapi.insertRecords(sourceDF.to_dict(orient='records'), f"{data.reconId}_unmatched")

            file_name = os.path.join(framework.settings.mftpath, 'OUTPUT', data.reconId, stmtdate,
                                        source + '_rollbackauthpending.csv')
            # reading from rollbackauth pending
            rollbackauthpending = pandas.read_csv(file_name)
            unmatchdf = rollbackauthpending[rollbackauthpending['LINK_ID'].isin(linkids)]

            # saving updated records to rollback auth pending
            rollbackauthpending = rollbackauthpending[~rollbackauthpending['LINK_ID'].isin(linkids)]
            rollbackauthpending.to_csv(file_name, index=False)

            unmatchdf['UPDATED_BY'] = login_session.get('email', '')
            unmatchdf["RESOLUTION_COMMENTS"] = data.comments
            unmatchdf["MATCHING_STATUS"] = "UNMATCHED"
            unmatchdf["RECONCILIATION_STATUS"] = "EXCEPTION"
            # saving the records to unmatched
            unmatchfilename = os.path.join(framework.settings.mftpath, 'OUTPUT', data.reconId, stmtdate,
                                            source + '_UnMatched.csv')
            if os.path.exists(unmatchfilename):
                unmatcheddf = pandas.read_csv(unmatchfilename)
                if not unmatcheddf.empty:
                    unmatchdf = pandas.concat([unmatcheddf, unmatchdf])
            unmatchdf.to_csv(unmatchfilename, index=False)

            # except Exception as e:
            #     return {"status": False, "message": e, "data": []}
    resp = await recons_stdapi._recomputereconsummary(data.reconId, stmtdate)
    recondata = await recons_stdapi.Recons.get(data.reconId)
    recondata = recondata

    sync_params = recons_overwrite_sync_postgres_parquet.overwrite_sync_postgres_parquetParams
    sync_params.reconId = data.reconId
    sync_params.exec_date = datetime.datetime.strptime(stmtdate, "%d%m%Y").strftime("%Y-%m-%d")
    sync_params.redis_queue = True
    await recons_overwrite_sync_postgres_parquet.Reconsoverwrite_sync_postgres_parquet(sync_params)

    if resp['status']:
        audit = {'type': 'Rollback Authorization',
                 'msg': f'{processedrecords} rollback records authorized for {recondata.get("reconName", "")}',
                 'reason': 'Success', 'actionStatus': True, 'email': login_session.get('email', '')}
        status, msg = await SystemAudit_stdapi.create_auditLogs(audit)
        return {"status": True, "message": "Records Authorized successfully for Rollback"}
    else:
        audit = {'type': 'Rollback Authorization',
                 'msg': f'Rollback authorization failed due to resp["message"]',
                 'reason': 'Failed', 'actionStatus': False, 'email': login_session.get('email', '')}
        status, msg = await SystemAudit_stdapi.create_auditLogs(audit)
        return {"status": resp['status'], "message": resp['message']}

def extract_key_value(json_str, key):
    try:
        json_obj = json.loads(json_str)
        return json_obj.get(key)
    except (ValueError, TypeError):
        return None