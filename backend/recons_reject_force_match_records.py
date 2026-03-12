from recons_enum import *
from recons_model import *
import fastapi
import recons_stdapi
import json
import os
import pandas
import SystemAudit_stdapi
import recons_overwrite_sync_postgres_parquet

router = fastapi.APIRouter(prefix='/recons')


@router.post('/reject_force_match_records', tags=['Recons'])
async def Reconsreject_force_match_records(data: reject_force_match_recordsParams):
    processedrecords = 0
    resp = await recons_stdapi._check_recon_status(data.reconId)
    if not resp['status']:
        return {"status": False, "message": resp['message'], "data": []}
    else:
        stmtdate = resp['data']

    tableName = f"{data.reconId}"
    tableName = f"{data.reconId}_unmatched"
    # rejectdf = pandas.DataFrame(json.loads(data.records))
    rejectdf = await recons_stdapi.getBulkRecords(data.records, data.reconId + '_unmatched')
    createdby = rejectdf['Json Data'].apply(lambda x: extract_key_value(x, 'UPDATED_BY')).tolist()
    login_session = await framework.restapi.me()
    if login_session.get('email', '') in createdby:
        return {"status": False,
                "message": 'Selected records are sent for authorization by You, so Rejection not allowed', "data": []}

    sources = rejectdf['SOURCE'].unique().tolist()
    for source in sources:
        sourceDF = rejectdf.loc[rejectdf['SOURCE'] == source]
        if not sourceDF.empty:
            try:
                uniqueId = sourceDF['_id'].tolist()
                linkids = sourceDF['LINK_ID'].tolist()
                processedrecords += len(sourceDF)
                #resp = await recons_stdapi._get_data(data.reconId, stmtdate, "authwaiting", source=source)
                #if not resp['status']:
                #    return {"status": resp['status'], "message": resp['message'], "data": []}
                #listOfRecords = []
                #for eachId in uniqueId:
                #unmatcheddf = await recons_stdapi.getRecords(eachId, tableName)
                # appending or saving to unmatched data
                #unmatcheddf['Json Data']['UPDATED_BY'] = login_session.get('email', '')
                #unmatcheddf['Json Data']['MATCHING_EXECUTION_STATUS'] = "MANUAL_REJECTED"
                #unmatcheddf['Json Data']["RESOLUTION_COMMENTS"] = data.comments
                #unmatcheddf['MATCHING_STATUS'] = "UNMATCHED"
                #unmatcheddf['family'] = "unmatched"
                #unmatcheddf['species'] = "unmatched"
                #unmatcheddf['Json Data']['RECONCILIATION_STATUS'] = "EXCEPTION"
                #unmatcheddf['Json Data']['FORCEMATCH_AUTHORIZATION'] = "AUTHORIZATION_REJECTION"
                #listOfRecords.append(unmatcheddf)
                sourceDF['Json Data']=sourceDF['Json Data'].apply(lambda x: {**x, 'MATCHING_EXECUTION_STATUS': 'MANUAL_REJECTED'})
                sourceDF['Json Data']=sourceDF['Json Data'].apply(lambda x: {**x, 'FORCEMATCH_AUTHORIZATION': 'AUTHORIZATION_REJECTION'})
                sourceDF['Json Data']=sourceDF['Json Data'].apply(lambda x: {**x, 'RECONCILIATION_STATUS': 'EXCEPTION'})
                sourceDF['Json Data']=sourceDF['Json Data'].apply(lambda x: {**x, 'UPDATED_BY': login_session.get('email', '')})
                sourceDF['Json Data']=sourceDF['Json Data'].apply(lambda x: {**x, 'RESOLUTION_COMMENTS': data.comments})
                sourceDF['family'] = "unmatched"
                sourceDF['species'] = "unmatched"
                resp = await recons_stdapi.updateRecords(sourceDF.to_dict(orient='records'), tableName)

                srcauthfilename = os.path.join(framework.settings.mftpath, 'OUTPUT', data.reconId, stmtdate,
                                               source + '_authwaiting.csv')
                # Reading data from auth file
                authdata = pandas.read_csv(srcauthfilename)
                unmatcheddf = authdata[authdata['LINK_ID'].isin(linkids)]

                # Saving updated data in auth file
                authdata = authdata[~authdata['LINK_ID'].isin(linkids)]
                authdata.to_csv(srcauthfilename, index=False)

                # appending or saving to unmatched data
                unmatcheddf['UPDATED_BY'] = login_session.get('email', '')
                unmatcheddf['MATCHING_EXECUTION_STATUS'] = "MANUAL_REJECTED"
                unmatcheddf["RESOLUTION_COMMENTS"] = data.comments
                unmatcheddf['MATCHING_STATUS'] = "UNMATCHED"
                unmatcheddf['RECONCILIATION_STATUS'] = "EXCEPTION"
                unmatcheddf['FORCEMATCH_AUTHORIZATION'] = "AUTHORIZATION_REJECTION"

                # adding the rejected records back to unmatched
                unmatchfp = os.path.join(framework.settings.mftpath, 'OUTPUT', data.reconId, stmtdate,
                                         source + '_UnMatched.csv')
                if os.path.exists(unmatchfp):
                    unmatchData = pandas.read_csv(unmatchfp)
                    if not unmatchData.empty:
                        unmatcheddf = pandas.concat([unmatchData, unmatcheddf])
                unmatcheddf.to_csv(unmatchfp, index=False)

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
        audit = {'type': 'Force Match Rejection',
                 'msg': f'{processedrecords} force matched records rejected for {recondata.get("reconName", "")}',
                 'reason': 'Success', 'actionStatus': True, 'email':login_session.get('email', '')}
        status, msg = await SystemAudit_stdapi.create_auditLogs(audit)
        return {"status": True, "message": "Records Rejected Successfully"}
    else:
        audit = {'type': 'Force Match Rejection',
                 'msg': f'Force match rejection failed due to {resp["message"]}',
                 'reason': 'Failed', 'actionStatus': False, 'email':login_session.get('email', '')}
        status, msg = await SystemAudit_stdapi.create_auditLogs(audit)
        return {"status": resp['status'], "message": resp['message']}

def extract_key_value(json_str, key):
    try:
        json_obj = json.loads(json_str)
        return json_obj.get(key)
    except (ValueError, TypeError):
        return None