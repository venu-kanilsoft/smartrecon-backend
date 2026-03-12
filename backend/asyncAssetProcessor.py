import os
import sys
import gzip
import json
import base64
import pandas
import asyncio
import datetime
import framework
import traceback
import jsonpickle
import cybercns_model
# import assetProcessor
import redis_queue
import reconexecution_uploadinputdata
import recons_updateconsolidatedreport
import recons_overwrite_sync_postgres_parquet
import recons_sync_postgres_parquet
sys.path.append(framework.settings.engine_scripts_path)
import customReport

async def worker():
    rq_ins = redis_queue._RedisQueue("assetProcessor")
    while True:
        msg = await rq_ins.get()
        try:
            msgBody = jsonpickle.loads(msg)
            print("msgBody -------->",msgBody)
            data = msgBody["data"]
            if data['op'] == 'updateconsolidatedreport':
                data1 = recons_updateconsolidatedreport.updateConsolidatedReportParams
                data1.reconId = data['reconId']
                data1.stmtdate = data['stmtdate']
                data1.runbackground = False
                await recons_updateconsolidatedreport.ReconsupdateConsolidatedReport(data1)
            if data['op'] == 'Overwrite_Sync_Postgres_Parquet':
                sync_params = recons_overwrite_sync_postgres_parquet.overwrite_sync_postgres_parquetParams
                sync_params.reconId = data['reconId']
                sync_params.exec_date = data['exec_date']
                sync_params.redis_queue = False
                await recons_overwrite_sync_postgres_parquet.Reconsoverwrite_sync_postgres_parquet(sync_params)
            if data['op'] == 'Sync_Postgres_Parquet':
                sync_params = recons_sync_postgres_parquet.sync_postgres_parquetParams
                sync_params.reconId = data['reconId']
                sync_params.redis_queue = False
                await recons_sync_postgres_parquet.Reconssync_postgres_parquet(sync_params)
            
            if data['op']=='customreport':
                print('INTO THE CUSTOM REPORT CONDITION')
                outpath = os.path.join(framework.settings.mftpath, 'OUTPUT',data['reconId'],data['stmtdate'])
                payload = {}
                payload['results'] = {}
                payload['reconId'] = data['reconId']
                payload['reconName'] = data['reconName']
                payload['reconProcess'] = data['reconProcess']
                payload['sourceIdNameMap'] = data['sourceIdNameMap']
                payload['createdBy'] = data['createdBy']
                payload['RedisQueue'] = 'customreport'
                payload['statementDate'] = datetime.datetime.strptime(str(data['stmtdate']), '%d%m%Y')
                for source in data['sourceName']:
                    payload['results'][source] = pandas.DataFrame()
                    df = pandas.DataFrame()
                    if os.path.exists(os.path.join(outpath, source +'_UnMatched.csv')):
                        df = pandas.read_csv(os.path.join(outpath, source +'_UnMatched.csv'))
                        payload['results'][source] = pandas.concat([payload['results'][source],df])
                    if os.path.exists(os.path.join(outpath, source +'.csv')):
                        df = pandas.read_csv(os.path.join(outpath, source +'.csv'))
                        payload['results'][source] = pandas.concat([payload['results'][source],df])
                await customReport.CustomReports().customReports(payload)
            
        except Exception as e:
            print("Exception In Worker Thread: %s Traceback: %s" % (e, traceback.format_exc()))


def RunAsyncWorker():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(worker())
    loop.close()

if __name__ == "__main__":
    RunAsyncWorker()
