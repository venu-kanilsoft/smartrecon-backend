from reconnotificationrule_enum import *
from reconnotificationrule_model import *
import sys
import json
import pandas
import zipfile
import fastapi
import datetime
import reconnotificationrule_stdapi
import recons_getsummary
import recons_getreports
import reconexecdetailslog_getlatestexedetails
sys.path.append(framework.settings.engine_scripts_path)
import sendgridApi
import emailApi

router = fastapi.APIRouter(prefix='/reconnotificationrule')

@router.post('/manualTrigger', tags=['ReconNotificationRule'])
async def ReconNotificationRulemanualTrigger(data: manualTriggerParams):
    notification_method, mailsettings = await _reconMap(data.reconId)
    age = 100
    if mailsettings:
        mailsettings['sendSummaryMail']=False
        integrations_query = {"reconId": str(data.reconId)}
        params = framework.queryparams.QueryParams()
        params.limit = 10000
        params.skip = 0
        params.q = json.dumps(integrations_query)

        resp = await reconnotificationrule_stdapi.ReconNotificationRule.get_all(params, framework.settings.dbName)
        maildata = resp.get('data', [])
        if maildata:
            maildata = maildata[0]
        filepath = ''
        if maildata:
            data1 = recons_getsummary.getSummaryParams
            data1.reconId = data.reconId
            data1.stmtdate = data.stmtDate
            data1.cyclewise = None
            resp = await recons_getsummary.ReconsgetSummary(data1)
            if not resp.get('status', False) and not resp.get('data', []):
                return {"status": False, "message": resp.get('message', ''), "data": []}
            summary = resp.get('data', [])
            if summary:
                tousers = []
                ccusers = []
                valuedict = maildata['levels']
                sendmail = False
                for condition in valuedict:
                    start = condition.get('ageingstart', 1)
                    end = condition.get('ageingend', 1)
                    
                    if int(start) <= int(age) or int(end) <= int(age):
                        tousers.append(condition.get('mailTo', ''))
                        ccusers.append(condition.get('cc', ''))
            data1 = reconexecdetailslog_getlatestexedetails.getLatestExeDetailsParams
            data1.reconId = data.reconId
            resp = await reconexecdetailslog_getlatestexedetails.ReconExecDetailsLoggetLatestExeDetails(data1)
            recon_exec_data = resp.get('data', [])
            if not recon_exec_data:
                return {"status": False, "data": "Unable to find latest execution details"}
            execdoc = recon_exec_data[0]
            stmtdate = int(execdoc['statementDate'].timestamp())
            data1 = recons_getreports.getReportsParams
            data1.reconId = data.reconId
            data1.stmtdate = data.stmtDate
            data1.cyclewise = None
            resp = await recons_getreports.ReconsgetReports(data1)
            reportDetails = resp.get('data', [])
            if execdoc:
                report_display = []
                final_reports = []
                lateststmtdate=datetime.datetime.fromtimestamp(execdoc['stmtDate']).strftime('%d%m%Y')
                reports = maildata.get('reports',[])
                if len(reports) > 0:
                    for rep in reports:
                        report_display.append(rep.get('displayname', ''))
                for report in reportDetails:
                    for filename in report_display:
                        if report.get('displayname', '') == filename:
                            if report.get('displayname', '') not in final_reports:
                                final_reports.append(report.get('filename', ''))
                date = execdoc['statementDate'].strftime('%d%m%Y')
                outPath = os.path.join(framework.settings.mftpath, 'OUTPUT', data.reconId,date)
                if os.path.exists(outPath) and len(reports) > 0:
                    path = os.path.join(framework.settings.mftpath, 'OUTPUT', data.reconId,date)
                    date = execdoc['statementDate'].strftime('%d%m%Y')
                    zipObj = zipfile.ZipFile(path + '/' + data.reconId + '-' + date + '.zip', 'w')
                    retval = os.getcwd()
                    os.chdir(outPath)
                    for file in os.listdir(outPath):
                        if file in final_reports:
                            zipObj.write(file)
                    zipObj.close()
                    os.chdir(retval)
                    filepath = [path + '/' + data.reconId + '-' + date + '.zip']
                if filepath :
                    final_data = []
                    summary = pandas.DataFrame(summary)
                    if '_type_' in summary.columns:
                        del summary['_type_']
                    if 'id' in summary.columns:
                        del summary['id']
                    if '_id' in summary.columns:
                        del summary['_id']
                    if 'family' in summary.columns:
                        del summary['family']
                    if 'species' in summary.columns:
                        del summary['species']
                    if 'u' in summary.columns:
                        del summary['u']
                    if 'updated' in summary.columns:
                        del summary['updated']
                    if 'c' in summary.columns:
                        del summary['c']
                    body = eval(str(notification_method).lower()+'Api').read_template(f'{framework.settings.engine_scripts_path}IDFC_mail_templates/summarytemplate.html', {'reconId':str(data.reconId),'reconName':str(data.reconName),'exeId': execdoc.get('reconExecutionId', 100), 'stmtDate': execdoc['statementDate'].strftime('%d-%m-%Y'), 'data':summary})
                    subject = 'Daily Recon Job Summary for %s - %s' % (data.reconId, lateststmtdate)
                    (status,msg)=eval(str(notification_method).lower()+'Api').sendemail(subject, body, tousers + ccusers, attachFiles=filepath, isHtml=True, mailsettings=mailsettings)
                else:
                    subject = 'Daily Recon Job Summary for %s - %s' % (data.reconId, lateststmtdate)
                    body = eval(str(notification_method).lower()+'Api').read_template(f'{framework.settings.engine_scripts_path}IDFC_mail_templates/Nilexceptiontemplate.html',{'Recon_Name':data.reconName})
                    (status,msg)=eval(str(notification_method).lower()+'Api').sendemail(subject, body, tousers + ccusers, isHtml=True, mailsettings=mailsettings)
                return {"status":status, "message":msg, "data": []}
            return {"status":False, "message":"No latest execution", "data":[]}
        return {"status":False, "message":"No data in automailer", "data":[]}
    return {"status":False, "message":"Please add Email settings", "data":[]}


async def _get_recepients(reconId):
    """
    get the mail recepients for that recon ID

    Parameters
    ----------
    reconId : str
        Recon ID

    Returns
    ----------
    dict
        dict containing comma-separated "to_users" and "cc_users"
        e.g: {"to_users": "x@example.com,y@example.com"}
    """
    to_users = ""
    cc_users = ""
    # TODO: change the function to obtain the mail recepients from opendistro config for the recon ID
    # automailer_details = list(self.mclient['automailer'].find({"RECON_ID": reconId}))
    ins = framework.postgresmodel.PostgresModel()
    ins.Config.collection_name = "notifications"
    notification_query = {"reconId": str(reconId)}
    params = framework.queryparams.QueryParams()
    params.limit = 10000
    params.skip = 0
    params.q = json.dumps(notification_query)
    try:
        integration_data = await ins.get_all(params, framework.settings.dbName)
    except Exception as e:
        integration_data = {"data": [], "count": 0, "total": 0}
    
    return integration_data


async def _reconMap(reconId):
    mailsettings = {}
    notification_details = {}
    ins = framework.postgresmodel.PostgresModel()
    ins.Config.collection_name = "integrations"
    integrations_query = {"reconId": str(reconId)}
    params = framework.queryparams.QueryParams()
    params.limit = 10000
    params.skip = 0
    params.q = json.dumps(integrations_query)
    integration_data = await ins.get_all(params, framework.settings.dbName)
    print(integration_data)
    if integration_data.get("data"):
        # no integration data or some read error. Set default mail settings
        mailsettings = {}
    notification_method = ""
    for integration in integration_data.get("data", []):
        notification_method = integration.get("integrationName", "")
        ins.Config.collection_name = notification_method.lower()
        cred_id = integration.get("credentialId")
        cred_query = {"_id": cred_id}
        params = framework.queryparams.QueryParams()
        params.limit = 10000
        params.skip = 0
        params.q = json.dumps(cred_query)
        cred_data = await ins.get_all(params, framework.settings.dbName)
        if not cred_data['data']:
            # logger.error("Unable to find the credentials")
            return notification_method, {}
            # continue
        mailsettings = cred_data['data'][0]
        if 'password' in mailsettings.keys():
            passwd = mailsettings['password']
            passwd_obj = framework.types.Secret(str(cred_data['data'][0]['password']))
            mailsettings['password'] = passwd_obj.get_secret()
        if 'api' in mailsettings.keys():
            passwd = mailsettings['api']
            passwd_obj = framework.types.Secret(str(cred_data['data'][0]['api']))
            mailsettings['api'] = passwd_obj.get_secret()
        return notification_method, mailsettings
    return "", {}
