from recons_enum import *
from recons_model import *
import fastapi
import json
import os
import pandas
import numpy as np
import datetime
import recons_stdapi
import redis_queue
import jsonpickle
from typing import Optional
import reconexecdetailslog_getlatestexedetails
import ReconMetaInfo_stdapi
import SystemAudit_stdapi
import SourceReference_stdapi


router = fastapi.APIRouter(prefix='/recons')

@router.post('/updateConsolidatedReport', tags=['Recons'])

async def ReconsupdateConsolidatedReport(data: updateConsolidatedReportParams):
    data1 = reconexecdetailslog_getlatestexedetails.getLatestExeDetailsParams
    data1.reconId = data.reconId
    doc = await reconexecdetailslog_getlatestexedetails.ReconExecDetailsLoggetLatestExeDetails(data1)
    if doc['status']:
        data.stmtdate = datetime.datetime.fromisoformat(
                doc["data"][0].get('statementDate', None)).strftime('%d-%m-%Y')
    else:
        return {"status": False, "message": "No Latest Execution Found", "data": []}
    if data.runbackground:
        doc = {}
        doc['reconId'] = data.reconId
        doc['stmtdate'] = data.stmtdate
        doc['runbackground'] = False
        doc['op'] = 'updateconsolidatedreport'
        await redis_queue._RedisQueue('assetProcessor').put(jsonpickle.dumps({"tenant": framework.ctx['tenant'], "data": doc}))
        return {"status": True, "message": "ConsolodatedReport is getting updated in background", "data": []}
    outputPath = os.path.join(framework.settings.mftpath, 'OUTPUT', data.reconId, datetime.datetime.strptime(data.stmtdate, '%d-%m-%Y').strftime('%d%m%Y'))
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"reconId": data.reconId}},
                ]
            }
        }
    }
    params = framework.queryparams.QueryParams()
    params.limit = 100
    params.skip = 0
    params.q = json.dumps(query)
    sourceins = SourceReference_stdapi.SourceReference()
    resp = await sourceins.get_all(params, framework.settings.dbName)
    resp = resp.get('data', [])
    sourceName = []
    for each_source_ref in resp:
        sourceName.append(each_source_ref['source'])
    writer = pandas.ExcelWriter(outputPath + "/ConsolidatedReport.xlsx", engine="xlsxwriter")
    for each_source in sourceName:
        all_data = pandas.DataFrame()
        if os.path.exists(os.path.join(outputPath, each_source + '.csv')):
            match_df = pandas.read_csv(os.path.join(outputPath, each_source + '.csv'), dtype=str)
            #all_data = all_data.append(match_df)
            all_data = pandas.concat([all_data,match_df],ignore_index = True)
            del match_df
        if os.path.exists(os.path.join(outputPath, each_source + '_UnMatched.csv')):
            un_match_df = pandas.read_csv(os.path.join(outputPath, each_source + '_UnMatched.csv'), dtype=str)
            #all_data = all_data.append(un_match_df)
            all_data = pandas.concat([all_data,un_match_df],ignore_index = True)
            del un_match_df
        all_data = all_data.reset_index(drop=True)
        all_data.to_excel(writer, sheet_name=each_source, index=False)
        if os.path.exists(os.path.join(outputPath, each_source + '_Filtered.csv')):
            filter_df = pandas.read_csv(os.path.join(outputPath, each_source + '_Filtered.csv'), dtype=str)
            filter_df.to_excel(writer, sheet_name=each_source + '_Filtered', index=False)
    if os.path.exists(os.path.join(outputPath, 'recon_summary.csv')):
        recon_summary = pandas.read_csv(os.path.join(outputPath, 'recon_summary.csv'), dtype=str)
        recon_summary.to_excel(writer, sheet_name='recon_summary', index=False)
    writer.save()
    return {"status": True, "message": "ConsolidatedReport Updated", "data": []}
