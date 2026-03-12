import re
from FeedFile_enum import *
from FeedFile_model import *
import fastapi
import json
import datetime
import recons_stdapi
import FeedFile_stdapi
import feedfile_feedstatusmail
from dateutil.relativedelta import relativedelta

router = fastapi.APIRouter(prefix='/feedfile')

@router.post('/feed_status_scheduler', tags=['FeedFile'])
async def FeedFilefeed_status_scheduler(data: feed_status_schedulerParams):
    if not data.reconList:
        return False, 'please select atleast one recon'
    success = []
    failure = []
    stmt_date = datetime.datetime.now()
    if data.stmtdate == "previous":
        stmt_date = stmt_date - datetime.timedelta(days=1)
    elif data.stmtdate == "daybeforeyesterday":
        stmt_date = stmt_date - datetime.timedelta(days=2)
    elif data.stmtdate == "threedaysago":
        stmt_date = stmt_date - datetime.timedelta(days=3)
    elif data.stmtdate == "previous_month":
        stmt_date = stmt_date - relativedelta(days=int(0), months=int(1))
    elif data.stmtdate == 'tatasky_monthly_recon':
        stmt_date = stmt_date - relativedelta(days=int(stmt_date.day - 1), months=int(1))
    stmtdate = stmt_date.strftime('%d-%m-%Y')
    for recon in data.reconList:
        if isinstance(recon, str):
            # query the recons collection with recon id
            recons_ins = recons_stdapi.Recons()
            resp = await recons_ins.get(recon, framework.settings.dbName)
            resp = resp
            if not resp:
                failure.append(recon)
                continue
            recon = resp
        resp = await _feed_status_scheduler(recon.get('reconId'), recon.get('reconName'), recon.get('reconProcess'), stmtdate)
        if resp['status']:
            success.append(recon.get('reconId') + '-' + recon.get('reconName'))
        else:
            failure.append(recon.get('reconId') + '-' + recon.get('reconName'))
    return {"status": True, "message": f'Overall status:\nsuccess-{success}\nfailure-{failure}', "data": []}
    
async def _feed_status_scheduler(reconId, reconName, reconProcess, stmtdate=''):
    if not reconId:
        return {"status": False, "message": 'Please provide recon Id', "data": []}
    # reconsources = self.find_one({'reconId': reconId})
    query = {"reconId": reconId}
    params = framework.queryparams.QueryParams()
    params.limit = 100
    params.skip = 0
    params.q = json.dumps(query)
    resp = FeedFile_stdapi.FeedFile.get_all(params, framework.settings.dbName)

    if not resp.get('data', []):
        return {"status":False,"message": 'Please provide feed details', "data": []}
    if not stmtdate:
        stmtdate = datetime.datetime.now().strftime('%d-%m-%Y')
    data1 = feedfile_feedstatusmail.feedStatusMailParams
    data1.recon_id = reconId
    data1.reconName = reconName
    data1.reconProcess = reconProcess
    data1.stmtDate =  stmtdate
    resp = await feedfile_feedstatusmail.FeedFilefeedStatusMail(data1)
    return {"status": resp['status'], "message": resp['message'], "data": resp['data']}
