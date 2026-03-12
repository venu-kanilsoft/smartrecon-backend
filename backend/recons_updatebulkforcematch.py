from recons_enum import *
from recons_model import *
import fastapi
import json
import os
import pandas
import datetime
import recons_stdapi
import jsonpickle
import redis_queue
import reconexecdetailslog_getlatestexedetails
import ReconMetaInfo_stdapi
import SystemAudit_stdapi
import SourceReference_stdapi

router = fastapi.APIRouter(prefix='/recons')


@router.post('/updateBulkForceMatch', tags=['Recons'])
async def ReconsupdateBulkForceMatch(data: updateBulkForceMatchParams):
    # data1 = reconexecdetailslog_getlatestexedetails.getLatestExeDetailsParams
    # data1.reconId = data.reconId
    # doc = await reconexecdetailslog_getlatestexedetails.ReconExecDetailsLoggetLatestExeDetails(data1)
    # if doc['status']:
    #     data.stmtdate = doc["data"][0].get('statementDate', None).strftime('%d-%m-%Y')
    # else:
    #     return {"status": False, "message": "No Latest Execution Found", "data": []}
    # print("data-->",data)
    # df = pandas.DataFrame(json.loads(data.records.__dict__['success']))
    # print('df columns ---->',df.columns)
    # df.to_csv('/tmp/data_df.csv')
    # dbName = framework.settings.dbName
    # ins = framework.postgresmodel.PostgresModel()
    # tableName = data.reconId + "_unmatched"
    # login_session = await framework.restapi.me()
    # reversal = False
    # for each_source in df['SOURCE'].unique().tolist():
    #     system_idx = df[df['SOURCE']==each_source]['System_Idx'].unique().tolist()
    #     query = {"SOURCE": each_source, "System_Idx": system_idx}
    #     params = framework.queryparams.QueryParams()
    #     params.limit = None
    #     params.q = json.dumps(query)
    #     try:
    #         resp = await ins.get_all(params, dbName, tableName)
    #     except Exception as e:
    #         print(e)
    #         return {"status": True, "message": e, "data": []}
    #     resp_df = pandas.DataFrame(resp["data"])
    #     uniqueId = resp_df['_id'].tolist()
    #     list_of_column = resp_df.columns.tolist()
    #     list_of_column_copy = resp_df.columns.tolist()
    #     list_of_column_copy.remove("Json Data")
    #     resp_df = resp_df.join(pandas.json_normalize(resp_df['Json Data'])).drop(columns=['Json Data'])
    #     resp_df['BULK_FORCEMATCH_UPDATEDBY'] = login_session.get('email', '')
    #     resp_df['BULK_FORCEMATCH_UPDATEDDATE'] = datetime.datetime.now().strftime('%d-%m-%Y')
    #     del resp_df['MATCHING_STATUS']
    #     if 'BULK_FORCEMATCH_COMMENT' in resp_df.columns:
    #         del resp_df['BULK_FORCEMATCH_COMMENT']
    #     if 'MATCH GROUP_ID' in resp_df.columns:
    #         del resp_df['MATCH GROUP_ID']
    #     resp_df = resp_df.merge(
    #         df[['System_Idx', 'MATCHING_STATUS', 'BULK_FORCEMATCH_COMMENT', 'MATCH GROUP_ID']],
    #         on='System_Idx', suffixes=("", "_y"), how='left'
    #     )
    #     if 'Reversal' in resp_df['MATCHING_STATUS'].unique().tolist():
    #         resp_df['RECONCILIATION_STATUS'] = "RECONCILED"
    #         resp_df['FORCEMATCH_AUTHORIZATION'] = "AUTHORIZED"
    #         family = "selfmatched"
    #         reversal = True
    #     elif data.matchrecords:
    #         resp_df['RECONCILIATION_STATUS'] = "EXCEPTION"
    #         resp_df['FORCEMATCH_AUTHORIZATION'] = ""
    #         family = "unmatched"
    #     else:
    #         resp_df['RECONCILIATION_STATUS'] = "RECONCILED"
    #         resp_df['FORCEMATCH_AUTHORIZATION'] = "AUTHORIZED"
    #         family = "matched"
    #     # adding the rejected records back to unmatched
    #     cols_to_json = list(set(resp_df.columns.tolist()) - set(list_of_column_copy))
    #     resp_df['family'] = family
    #     resp_df['species'] = family
    #     resp_df['Json Data'] = resp_df[cols_to_json].apply((lambda x: x.to_json()), axis=1)
    #     linkids = resp_df['System_Idx'].tolist()
    #     resp_df = resp_df[list_of_column]
    #     resp_df = resp_df.to_dict(orient='records')
    #     for i in range(0, len(resp_df)):
    #         resp_df[i]['Json Data'] = json.loads(resp_df[i]['Json Data'])
        
    #     print("Inserting :", resp_df)
    #     resp = await recons_stdapi.insertRecords(resp_df, f"{data.reconId}_matched")        
    #     await recons_stdapi.deleteRecords(uniqueId, tableName)
    #     # resp = await recons_stdapi.updateRecords(resp_df, tableName)
        
    #     mftpath = framework.settings.mftpath
    #     stmtDate = datetime.datetime.strptime(data.stmtdate, '%d-%m-%Y').strftime('%d%m%Y')

    #     if data.matchrecords:
    #         srcmatchfilename = os.path.join(mftpath, 'OUTPUT', data.reconId, str(stmtDate), each_source + '.csv')
    #         if os.path.exists(srcmatchfilename):
    #             continue
    #         matcheddf = pandas.read_csv(srcmatchfilename, dtype=str)
    #         forceMatchDf = matcheddf[matcheddf['System_Idx'].isin(linkids)]
    #         forceMatchDf['BULK_ROLLBACK_UPDATEDBY'] = login_session.get('email', '')
    #         forceMatchDf['BULK_ROLLBACK_UPDATEDDATE'] = datetime.datetime.now().strftime('%d-%m-%Y')
    #         forceMatchDf['RECONCILIATION_STATUS'] = "EXCEPTION"
    #         forceMatchDf['ROLLBACK_AUTHORIZATION'] = ""
    #         del forceMatchDf['MATCHING_STATUS']
    #         if 'BULK_FORCEMATCH_COMMENT' in forceMatchDf.columns:
    #             del forceMatchDf['BULK_FORCEMATCH_COMMENT']
    #         if 'MATCH GROUP_ID' in forceMatchDf.columns:
    #             del forceMatchDf['MATCH GROUP_ID']
    #         forceMatchDf = forceMatchDf.merge(
    #             df[['System_Idx', 'MATCHING_STATUS', 'BULK_FORCEMATCH_COMMENT', 'MATCH GROUP_ID']],
    #             on='System_Idx', suffixes=("", "_y"), how='left'
    #         )
    #         matcheddf = matcheddf[~matcheddf['System_Idx'].isin(linkids)]
    #         matcheddf.to_csv(srcmatchfilename, index=False)

    #         srcfilename = os.path.join(mftpath, 'OUTPUT', data.reconId, str(stmtDate), each_source + '_UnMatched.csv')
    #         if os.path.exists(srcfilename):
    #             sourcedata = pandas.read_csv(srcfilename, dtype=str)
    #             if not sourcedata.empty:
    #                 forceMatchDf = pandas.concat([sourcedata, forceMatchDf])
    #         forceMatchDf.to_csv(srcfilename, index=False)
    #     else:
    #         srcfilename = os.path.join(mftpath, 'OUTPUT', data.reconId, str(stmtDate), each_source + '_UnMatched.csv')
    #         if not os.path.exists(srcfilename):
    #             continue
    #         sourcedata = pandas.read_csv(srcfilename, dtype=str)
    #         forceMatchDf = sourcedata[sourcedata['System_Idx'].isin(linkids)]
    #         forceMatchDf['BULK_FORCEMATCH_UPDATEDBY'] = login_session.get('email', '')
    #         forceMatchDf['BULK_FORCEMATCH_UPDATEDDATE'] = datetime.datetime.now().strftime('%d-%m-%Y')
    #         forceMatchDf['RECONCILIATION_STATUS'] = "RECONCILED"
    #         forceMatchDf['FORCEMATCH_AUTHORIZATION'] = "AUTHORIZED"
    #         del forceMatchDf['MATCHING_STATUS']
    #         if 'BULK_FORCEMATCH_COMMENT' in forceMatchDf.columns:
    #             del forceMatchDf['BULK_FORCEMATCH_COMMENT']
    #         if 'MATCH GROUP_ID' in forceMatchDf.columns:
    #             del forceMatchDf['MATCH GROUP_ID']
    #         forceMatchDf = forceMatchDf.merge(
    #             df[['System_Idx', 'MATCHING_STATUS', 'BULK_FORCEMATCH_COMMENT', 'MATCH GROUP_ID']],
    #             on='System_Idx', suffixes=("", "_y"), how='left'
    #         )

    #         # Removing the records from unmatched data and saving
    #         sourcedata = sourcedata[~sourcedata['System_Idx'].isin(linkids)]
    #         sourcedata.to_csv(srcfilename, index=False)
    #         if reversal:
    #             srcmatchfilename = os.path.join(mftpath, 'OUTPUT', data.reconId, str(stmtDate),
    #                                             each_source + '_Self_Matched.csv')
    #             if os.path.exists(srcmatchfilename):
    #                 matcheddf = pandas.read_csv(srcmatchfilename, dtype=str)
    #                 if not matcheddf.empty:
    #                     forceMatchDf = pandas.concat([matcheddf, forceMatchDf])
    #             forceMatchDf.to_csv(srcmatchfilename, index=False)
    #         else:
    #             srcmatchfilename = os.path.join(mftpath, 'OUTPUT', data.reconId, str(stmtDate), each_source + '.csv')
    #             if os.path.exists(srcmatchfilename):
    #                 matcheddf = pandas.read_csv(srcmatchfilename, dtype=str)
    #                 if not matcheddf.empty:
    #                     forceMatchDf = pandas.concat([matcheddf, forceMatchDf])
    #             forceMatchDf.to_csv(srcmatchfilename, index=False)

    #     recon_meta_info = await getReports(data.reconId, data.stmtdate)
    #     if data.matchrecords:
    #         srcmatchfilename = os.path.join(mftpath, 'OUTPUT', data.reconId, str(stmtDate),
    #                                         each_source + '_BulkRollback.csv')
    #         if os.path.exists(srcmatchfilename):
    #             rollback_df = pandas.read_csv(srcmatchfilename, dtype=str)
    #             if not rollback_df.empty:
    #                 forceMatchDf = pandas.concat([rollback_df, forceMatchDf])
    #         forceMatchDf.to_csv(srcmatchfilename, index=False)
    #         if recon_meta_info:
    #             if not any(
    #                     d['displayName'] == f"{each_source} Bulk Rollback" for d in recon_meta_info['reportDetails']):
    #                 recon_meta_info['reportDetails'].append(
    #                     {"displayName": f"{each_source} Bulk Rollback", "filename": f"{each_source}_BulkRollback.csv",
    #                      "source": f"{each_source}"})
    #                 recon_meta = ReconMetaInfo_stdapi.ReconMetaInfo()
    #                 data_object = recon_meta.parse_obj(recon_meta_info)
    #                 await data_object.update(dbName)

    #     else:
    #         srcmatchfilename = os.path.join(mftpath, 'OUTPUT', data.reconId, str(stmtDate), each_source + '_BulkForceMatch.csv')
    #         if os.path.exists(srcmatchfilename):
    #             forcematch_df = pandas.read_csv(srcmatchfilename, dtype=str)
    #             if not forcematch_df.empty:
    #                 forceMatchDf = pandas.concat([forcematch_df, forceMatchDf])
    #         # Shrihari
    #         if "BULK_FORCEMATCH_UPDATEDBY" in forceMatchDf.columns:
    #             forceMatchDf = forceMatchDf[forceMatchDf['BULK_FORCEMATCH_UPDATEDBY'].fillna('') != '']
    #         forceMatchDf.to_csv(srcmatchfilename, index=False)
            
    #         if recon_meta_info:
    #             if not any(
    #                     d['displayName'] == f"{each_source} Bulk ForceMatch" for d in recon_meta_info['reportDetails']):
    #                 recon_meta_info['reportDetails'].append({"displayName": f"{each_source} Bulk ForceMatch",
    #                                                          "filename": f"{each_source}_BulkForceMatch.csv",
    #                                                          "source": f"{each_source}"})
    #                 recon_meta = ReconMetaInfo_stdapi.ReconMetaInfo()
    #                 data_object = recon_meta.parse_obj(recon_meta_info)
    #                 await data_object.update(dbName)
    #             if reversal and not any(
    #                     d['displayName'] == f"{each_source} Self Match" for d in recon_meta_info['reportDetails']):
    #                 recon_meta_info['reportDetails'].append(
    #                     {"displayName": f"{each_source} Self Match", "filename": f"{each_source}_Self_Matched.csv",
    #                      "source": f"{each_source}"})
    #                 recon_meta = ReconMetaInfo_stdapi.ReconMetaInfo()
    #                 data_object = recon_meta.parse_obj(recon_meta_info)
    #                 await data_object.update(dbName)

    # resp = await recons_stdapi._recomputereconsummary(data.reconId, str(stmtDate))
    # status, msg = await customReport(data.reconId, str(stmtDate))
    # recondata = await recons_stdapi.Recons.get(data.reconId)
    # recondata = recondata
    # processedrecords = len(df)
    # if data.matchrecords:
    #     types = "Bulk Rollback Records"
    # else:
    #     types = "Bulk Force Match Records"
    # if resp['status']:
    #     audit = {'type': types,
    #              'msg': f'{processedrecords} {types} for {recondata.get("reconName", "")}',
    #              'reason': 'Success', 'actionStatus': True,
    #              'remarksupdatedby': login_session.get('email', ''),
    #              'remarksupdatedate': datetime.datetime.now()}
    #     status, msg = await SystemAudit_stdapi.create_auditLogs(audit)
    #     return {"status": True, "message": f"{types} Successfully Updated"}
    # else:
    #     audit = {'type': types,
    #              'msg': f'{types} failed due to {resp["message"]}',
    #              'reason': 'Failed', 'actionStatus': False,
    #              'remarksupdatedby': login_session.get('email', ''),
    #              'remarksupdatedate': datetime.datetime.now()}
    #     status, msg = await SystemAudit_stdapi.create_auditLogs(audit)
    #     return {"status": resp['status'], "message": resp['message']}
    login_session = await framework.restapi.me()
    createdBy = login_session.get('email', '')
    data1 = reconexecdetailslog_getlatestexedetails.getLatestExeDetailsParams
    data1.reconId = data.reconId
    doc = await reconexecdetailslog_getlatestexedetails.ReconExecDetailsLoggetLatestExeDetails(data1)
    if doc['status']:
        data.stmtdate = doc["data"][0].get('statementDate', None).strftime('%d-%m-%Y')
    else:
        return {"status": False, "message": "No Latest Execution Found", "data": []}
    fmt_stmtdate = datetime.datetime.strptime(data.stmtdate, '%d-%m-%Y').strftime('%d-%b-%Y')
    file_path = f'/tmp/{data.reconId}_forcematch.csv'
    
    print('data ------->',data)
    print("records :", data.records.success)
    tableName = f"{data.reconId}_unmatched"
    df = await recons_stdapi.getBulkRecords(data.records.success, tableName)
    df = df.join(pandas.json_normalize(df['Json Data'])).drop(columns=['Json Data'])
    df["BULK_FORCEMATCH_COMMENT"] = ""
    df['MATCHING_STATUS'] = "MATCHED"
    df["MATCH GROUP_ID"] = ""
    print("-"*100)
    print("df :", df)
    print("-"*100)
    #df = pandas.DataFrame(json.loads(data.records.__dict__['success']))
    df.to_csv(file_path,index = False)

    
    # createdBy = flask.session['sessionData']['email']
    # login_session = await framework.restapi.me()
    # createdBy = login_session.get('email', '')
    

    sysdfp = os.path.join('/etc/systemd/system', data.reconId + '_forcematch.service')    
    if os.path.exists(sysdfp):        
        return {"status": False, "message": "Forcematch is already in progress or a stale job exists."}

    #engine_scripts_path = framework.settings.engine_scripts_path
    engine_scripts_path = framework.settings.polars_engine_path
    if not engine_scripts_path:
        engine_scripts_path = "/data/ngerecon/smartrecon/reconengine/scripts_polars"
    cmd = f"{engine_scripts_path}/bulkforcematchexec.sh {data.reconId} {fmt_stmtdate} {file_path} {createdBy}"
    with open(sysdfp, 'w') as f:
        lines = list()
        lines.append('[Unit]\n')
        lines.append('Description=Recon Job Service\n\n')
        lines.append('[Service]\n')
        lines.append('Type=simple\n')
        lines.append(f'WorkingDirectory={engine_scripts_path}\n')
        lines.append('ExecStart=%s\n' % cmd)
        lines.append('ExecStop=/bin/rm -rf %s\n' % sysdfp)
        f.writelines(lines)

    os.system('systemctl daemon-reload')
    os.system('systemctl start "%s.service"' % f"{data.reconId}_forcematch")

    recondata = await recons_stdapi.Recons.get(data.reconId)
    recondata = recondata
    doc = {'type': 'Recon Execution', 'msg': f'ForcematchExecution initiated statementdate:{fmt_stmtdate} for {recondata["reconName"]}',
                     'reason': 'Success', 'actionStatus': True, 'email': createdBy, 'reconId': data.reconId}
    status, message = await SystemAudit_stdapi.create_auditLogs(doc=doc)
    return {"status": True, "message": "ForcematchExecution is in progress please check status in Jobs"}


async def getReports(reconId: str, stmtdate: str):
    stmtdate = int(datetime.datetime.strptime(stmtdate, '%d-%m-%Y').timestamp())
    report_query = {"reconId": reconId, "stmtdate": stmtdate}
    params = framework.queryparams.QueryParams()
    params.limit = 1
    params.q = json.dumps(report_query)
    params.sort = json.dumps({"updated": -1})
    dbName = framework.settings.dbName
    print('report_query', report_query)
    reconmetadata = await ReconMetaInfo_stdapi.ReconMetaInfo().get_all(params, dbName)
    reconmetadata = reconmetadata.get('data', [])
    if reconmetadata:
        reconmetadata = reconmetadata[0]
        return reconmetadata
    return {}


async def customReport(reconId, stmtdate):
    sourceList = []
    login_session = await framework.restapi.me()
    createdBy = login_session.get('email', '')

    # fetch recon data
    recons_ins = recons_stdapi.Recons()
    recondata = await recons_ins.get(reconId, framework.settings.dbName)

    reconsources = recondata.get('sources', [])
    reconName = recondata.get('reconName', '')
    reconProcess = recondata.get('reconProcess', '')
    if not reconsources:
        return False, "Sources are not configured."

    source_ref_ins = SourceReference_stdapi.SourceReference()
    sourceIdNameMap = {}
    for src in reconsources:
        # finding the source reference of this source
        sourceref = await source_ref_ins.get(src, framework.settings.dbName)
        if not sourceref:
            continue
        sourceList.append(sourceref.get('source', ''))
        sourceIdNameMap[src] = sourceref.get('source', '')

    doc = {
        'sourceIdNameMap': sourceIdNameMap, 'reconProcess': reconProcess, 'reconId': reconId,
        'sourceName': sourceList, 'stmtdate': stmtdate,
        'reconName': reconName, "createdBy": createdBy, 'op': "customreport"
    }
    print(doc)
    await redis_queue._RedisQueue('assetProcessor').put(
        jsonpickle.dumps({"tenant": framework.ctx['tenant'], "data": doc}))
    return True, "Reports are regenerating in background"
