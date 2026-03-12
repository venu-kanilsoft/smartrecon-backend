from recons_enum import *
from recons_model import *
import fastapi
import recons_stdapi
import json
import os
import pandas
import SystemAudit_stdapi
import traceback
import recons_overwrite_sync_postgres_parquet

router = fastapi.APIRouter(prefix='/recons')

@router.post('/authorize_force_match_records', tags=['Recons'])
async def Reconsauthorize_force_match_records(data: authorize_force_match_recordsParams):
    processedrecords = 0
    resp = await recons_stdapi._check_recon_status(data.reconId)
    if not resp['status']:
        return {"status": False, "message": resp['message'], "data": []}
    else:
        stmtdate = resp['data']
    # authorizedf = pandas.DataFrame(json.loads(data.records))
    # createdby = authorizedf['UPDATED_BY'].unique()
    # login_session = await framework.restapi.me()    
    tableName = f"{data.reconId}_unmatched"
    authorizedf = await recons_stdapi.getBulkRecords(data.records, tableName)
    print(authorizedf.columns)
    print(authorizedf)
    createdby = authorizedf['Json Data'].apply(lambda x: extract_key_value(x, 'UPDATED_BY')).tolist()
    print(createdby)
    login_session = await framework.restapi.me()
    if login_session.get('email', '') in createdby:
        return {"status":False, "message":'Selected records are sent for authorization by You, so Authorization not allowed', "data": []}
    sources = authorizedf['SOURCE'].unique().tolist()
    for source in sources:
        matchdf = authorizedf.loc[authorizedf['SOURCE'] == source]
        if not matchdf.empty:
            uniqueId = matchdf['_id'].tolist()
            linkids = matchdf['LINK_ID'].unique().tolist()
            processedrecords += len(matchdf)
            # try:
            listOfRecords = []
            # for eachId in uniqueId:
            # matchdf = await recons_stdapi.getRecords(eachId, tableName)
            # removing records from auth waiting and saving
            # matchdf['Json Data']['UPDATED_BY'] = login_session.get('email', '')
            # matchdf['Json Data']["RESOLUTION_COMMENTS"] = data.comments
            # matchdf['MATCHING_STATUS'] = "MATCHED"
            # matchdf['family'] = "matched"
            # matchdf['species'] = "matched"
            # matchdf['Json Data']['RECONCILIATION_STATUS'] = "RECONCILED"
            # matchdf['Json Data']['FORCEMATCH_AUTHORIZATION'] = "AUTHORIZED"
            # listOfRecords.append(matchdf)
            matchdf['Json Data']=matchdf['Json Data'].apply(lambda x: {**x, 'RECONCILIATION_STATUS': 'RECONCILED'})
            matchdf['Json Data']=matchdf['Json Data'].apply(lambda x: {**x, 'FORCEMATCH_AUTHORIZATION': 'AUTHORIZED'})
            matchdf['Json Data']=matchdf['Json Data'].apply(lambda x: {**x, 'UPDATED_BY': login_session.get('email', '')})
            matchdf['Json Data']=matchdf['Json Data'].apply(lambda x: {**x, 'RESOLUTION_COMMENTS': data.comments})
            matchdf['MATCHING_STATUS'] = "MATCHED"
            matchdf['family'] = "matched"
            matchdf['species'] = "matched"
            # resp = await recons_stdapi.updateRecords(listOfRecords, tableName)
            resp = await recons_stdapi.insertRecords(matchdf.to_dict(orient='records'), f"{data.reconId}_matched")
            await recons_stdapi.deleteRecords(uniqueId, tableName)
            #resp = await recons_stdapi.insertRecords(matchdf.to_dict(orient='records'), f"{data.reconId}_matched")
            # Updating in CSV Files
            srcauthfilename = os.path.join(framework.settings.mftpath, 'OUTPUT', data.reconId, stmtdate, source + '_authwaiting.csv')
            sourcedata = pandas.read_csv(srcauthfilename)
            matchdf = sourcedata[sourcedata['LINK_ID'].isin(linkids)]
            sourcedata = sourcedata[~sourcedata['LINK_ID'].isin(linkids)]
            sourcedata.to_csv(srcauthfilename, index=False)

            matchdf['UPDATED_BY'] = login_session.get('email', '')
            matchdf["RESOLUTION_COMMENTS"] = data.comments
            matchdf['MATCHING_STATUS'] = "MATCHED"
            matchdf['RECONCILIATION_STATUS'] = "RECONCILED"
            matchdf['FORCEMATCH_AUTHORIZATION'] = "AUTHORIZED"

            # saving the records to respective match sources
            srcmatchfilename = os.path.join(framework.settings.mftpath, 'OUTPUT', data.reconId, stmtdate, source + '.csv')
            if os.path.exists(srcmatchfilename):
                matcheddf = pandas.read_csv(srcmatchfilename)
                if not matcheddf.empty:
                    matchdf = pandas.concat([matcheddf, matchdf])
            matchdf.to_csv(srcmatchfilename, index=False)
            # except Exception as e:
            #     print(e)
            #     print(traceback.print_exc())
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
        audit = {'type': 'Force Match Authorization',
                    'msg': f'{processedrecords} force matched records authorized for {recondata.get("reconName", "")}',
                    'reason': 'Success', 'actionStatus': True, 'email': login_session.get('email', '')}
        status, msg = await SystemAudit_stdapi.create_auditLogs(audit)
        return {"status": True, "message": "Records Authorized Successfully", "data": []}
    else:
        audit = {'type': 'Force Match Authorization',
                    'msg': f'Authorization force match records failed due to {resp["message"]}',
                    'reason': 'Failed', 'actionStatus': False, 'email': login_session.get('email', '')}
        status, msg = await SystemAudit_stdapi.create_auditLogs(audit)
        return {"status": resp['status'], "message": resp['message'], "data": []}

def extract_key_value(json_str, key):
    try:
        if isinstance(json_str, str):
            json_obj = json.loads(json_str)
        else:
            json_obj = json_str
        return json_obj.get(key)
    except (ValueError, TypeError):
        return None