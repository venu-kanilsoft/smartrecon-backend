import pandas
from recons_enum import *
from recons_model import *
import fastapi
import recons_stdapi
import pandas
import json
import os
import SystemAudit_stdapi
import recons_overwrite_sync_postgres_parquet

router = fastapi.APIRouter(prefix='/recons')


@router.post('/reject_rollback_records', tags=['Recons'])
async def Reconsreject_rollback_records(data: reject_rollback_recordsParams):
    processedrecords = 0
    resp = await recons_stdapi._check_recon_status(data.reconId)
    if not resp['status']:
        return {"status": False, "message": resp['message'], "data": []}
    else:
        stmtdate = resp['data']

    tableName = f"{data.reconId}"
    tableName = f"{data.reconId}_matched"
    #rejectdf = pandas.DataFrame(json.loads(data.records))
    #createdby = rejectdf['UPDATED_BY'].unique()
    rejectrollbackdf = await recons_stdapi.getBulkRecords(data.records, data.reconId)
    createdby = rejectrollbackdf['Json Data'].apply(lambda x: extract_key_value(x, 'UPDATED_BY')).tolist()
    login_session = await framework.restapi.me()
    if login_session.get('email', '') in createdby:
        return {"status": False,
                "message": 'Selected records are sent for rollback by You, so Rollback Rejection not allowed',
                "data": []}

    #rejectrollbackdf = pandas.DataFrame(json.loads(data.records))
    #createdby = rejectrollbackdf['UPDATED_BY'].unique()
    sources = rejectrollbackdf['SOURCE'].unique().tolist()
    for source in sources:
        sourceDF = rejectrollbackdf.loc[rejectrollbackdf['SOURCE'] == source]
        if not sourceDF.empty:
            try:
                uniqueId = sourceDF['_id'].tolist()
                linkids = sourceDF['LINK_ID'].tolist()
                processedrecords += len(sourceDF)
                #resp = await recons_stdapi._get_data(data.reconId, stmtdate, "rollbackwaiting", source=source)
                #if not resp['status']:
                #    return {"status": resp['status'], "message": resp['message'], "data": []}
                #listOfRecords = []
                #for eachId in uniqueId:
                #matchdf = await recons_stdapi.getRecords(eachId, tableName)
                #matchdf['Json Data']['UPDATED_BY'] = login_session.get('email', '')
                #matchdf["MATCHING_STATUS"] = "MATCHED"
                #matchdf['family'] = "matched"
                #matchdf['species'] = "matched"
                #matchdf['Json Data']["RESOLUTION_COMMENTS"] = data.comments
                #matchdf['Json Data']["RECONCILIATION_STATUS"] = "RECONCILED"
                #matchdf['Json Data']["AUTHORIZATION_STATUS"] = "AUTHORIZED"
                #matchdf['Json Data']["FORCEMATCH_AUTHORIZATION"] = "AUTHORIZED"
                #listOfRecords.append(matchdf)
                matchdf['Json Data']=matchdf['Json Data'].apply(lambda x: {**x, 'RECONCILIATION_STATUS': 'RECONCILED'})
                matchdf['Json Data']=matchdf['Json Data'].apply(lambda x: {**x, 'AUTHORIZATION_STATUS': 'AUTHORIZED'})
                matchdf['Json Data']=matchdf['Json Data'].apply(lambda x: {**x, 'FORCEMATCH_AUTHORIZATION': 'AUTHORIZED'})
                matchdf['Json Data']=matchdf['Json Data'].apply(lambda x: {**x, 'UPDATED_BY': login_session.get('email', '')})
                matchdf['Json Data']=matchdf['Json Data'].apply(lambda x: {**x, 'RESOLUTION_COMMENTS': data.comments})
                matchdf['MATCHING_STATUS'] = "MATCHED"
                matchdf['family'] = "matched"
                matchdf['species'] = "matched"
                resp = await recons_stdapi.updateRecords(matchdf.to_dict(orient='records'), tableName)

                file_name = os.path.join(framework.settings.mftpath, 'OUTPUT', data.reconId, stmtdate,
                                         source + '_rollbackauthpending.csv')
                # reading from rollbackauth pending
                srcrollbackauthpend = pandas.read_csv(file_name)
                matchdf = srcrollbackauthpend[srcrollbackauthpend['LINK_ID'].isin(linkids)]

                # moving records to matched
                srcrollbackauthpend = srcrollbackauthpend[~srcrollbackauthpend['LINK_ID'].isin(linkids)]
                srcrollbackauthpend.to_csv(file_name, index=False)

                matchdf['UPDATED_BY'] = login_session.get('email', '')
                matchdf["MATCHING_STATUS"] = "MATCHED"
                matchdf["RESOLUTION_COMMENTS"] = data.comments
                matchdf["RECONCILIATION_STATUS"] = "RECONCILED"
                matchdf["AUTHORIZATION_STATUS"] = "AUTHORIZED"
                matchdf["FORCEMATCH_AUTHORIZATION"] = "AUTHORIZED"
                # saving the records to matched
                matchfilename = os.path.join(framework.settings.mftpath, 'OUTPUT', data.reconId, stmtdate,
                                             source + '.csv')
                if os.path.exists(matchfilename):
                    matcheddf = pandas.read_csv(matchfilename)
                    if not matcheddf.empty:
                        matchdf = pandas.concat([matcheddf, matchdf])
                matchdf.to_csv(matchfilename, index=False)

            except Exception as e:
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
        audit = {'type': 'Rolback Rejection',
                 'msg': f'{processedrecords} rollback records rejected for {recondata.get("reconName", "")}',
                 'reason': 'Success', 'actionStatus': True, 'email':login_session.get('email', '')}
        status, msg = await SystemAudit_stdapi.create_auditLogs(audit)
        return {"status": True, "message": "Records Rejected successfully from Rollback"}
    else:
        audit = {'type': 'Rolback Rejection',
                 'msg': f'Rollback rejection failed due to {resp["message"]}',
                 'reason': 'Failed', 'actionStatus': False, 'email':login_session.get('email', '')}
        status, msg = await SystemAudit_stdapi.create_auditLogs(audit)
        return {"status": resp['status'], "message": resp['message']}

def extract_key_value(json_str, key):
    try:
        json_obj = json.loads(json_str)
        return json_obj.get(key)
    except (ValueError, TypeError):
        return None