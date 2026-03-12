from FeedFile_enum import *
from FeedFile_model import *
import fastapi
import json
import re
import sys
import pandas
import FeedFile_stdapi
import feedfile_getfeedfilestatus
import framework
sys.path.append(framework.settings.engine_scripts_path)
import sendgridApi
import emailApi

router = fastapi.APIRouter(prefix='/feedfile')

@router.post('/feedStatusMail', tags=['FeedFile'])
async def FeedFilefeedStatusMail(data: feedStatusMailParams):
    if not data.stmtDate:
        data.stmtDate = datetime.datetime.now().strftime('%d-%m-%Y')
    html=''
    query = {"reconId": data.reconId}
    params = framework.queryparams.QueryParams()
    params.limit = 100
    params.skip = 0
    params.q = json.dumps(query)
    resp = await FeedFile_stdapi.FeedFile.get_all(params, framework.settings.dbName)

    if not resp.get('data', []):
        return {"status": False, "message": "Please provide feeddata", "data": []}
    maildata = resp.get('data', [])[0]
    if not 'emailId' in maildata.keys():
        return {"status": False, "message": "Please provide email id to send mail", "data": []}
    # mailsettings = {}
    # doc = FeedFile_stdapi.getFeedFileStatus(data.recon_id, data.reconName, data.reconProcess, data.stmtDate)
    data1 = feedfile_getfeedfilestatus.getFeedFileStatusParams
    #data1.reconId = data.recon_id
    data1.reconId = data.reconId
    data1.reconName = data.reconName
    data1.reconProcess = data.reconProcess
    data1.stmtDate = data.stmtDate
    #data1.stmtDate = data.stmtDate.strftime('%d-%m-%Y')
    doc = await feedfile_getfeedfilestatus.FeedFilegetFeedFileStatus(data1)
    print("doc",doc)
    # convert string response to dict
    if isinstance(doc['data'], str):
        try:
            doc = json.loads(doc['data'])
            print(doc)
        except Exception as e:
            return {"status": False, "message": "Feed file status received in an unknown format", "data": []}
    df = pandas.DataFrame(doc)
    html = df.to_html(index=False, na_rep='', justify='center')
    stmtdate = datetime.datetime.strptime(str(data.stmtDate),'%d-%m-%Y')
    #html = re.sub(r'<td>Yes</td>', '<td bgcolor="#3D7D24 ">Yes</td>', html)
    html = re.sub(r'<td>Yes</td>', '<td style="color: #fff" bgcolor="#3D7D24">Yes</td>', html)
    html = re.sub(r'<td>No</td>', '<td style="color: #fff" bgcolor="#FF0000">No</td>', html)
    html = re.sub(r'<tr>', '<tr style="text-align: center;">', html)
    html = re.sub(r'<th>', '<th bgcolor="#BEBBBB">', html)
    deatils  = "<html>" \
                "<body>" \
                "<p>Dear Sir," \
                "<br>Files present on " + stmtdate.strftime('%d/%b/%Y') + " date, for %s Recon</p></body></html>" % data.reconName
    deatils += html
    deatils += "<p>Thanks and Regards," \
                "<br>Algofusion Technologies</p>"
    users = maildata['emailId']
    # if notification_method == 'sendgrid':
    #     status, resp = sendgridApi.sendemail('Feed Files Status',deatils,users,attachFiles=[],isHtml=True,mailsettings=mailsettings)
    # else:
    notify_type,mailsettings = await _reconMap(data.reconId)
    print('mail API -->',eval(str(notify_type).lower()+'Api'))
    status, resp = eval(str(notify_type).lower()+'Api').sendemail('Feed Files Status',deatils,users,attachFiles=[],isHtml=True,mailsettings=mailsettings)
    return {"status": True,"message": "Feed status mail sent successfully", "data": []}


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
    print('framework',framework.settings.dbName)
    integration_data = await ins.get_all(params, framework.settings.dbName)
    print('integration_data', integration_data)
    if integration_data.get("data"):
        # no integration data or some read error. Set default mail settings
        mailsettings = {}
    notification_method = ""
    for integration in integration_data.get("data", []):
        notification_method = integration.get("integrationName", "")
        cred_id = integration.get("credentialId")
        ins.Config.collection_name = "email"
        cred_query = {"_id": cred_id}
        params = framework.queryparams.QueryParams()
        params.limit = 10000
        params.skip = 0
        params.q = json.dumps(cred_query)
        cred_data = await ins.get_all(params, framework.settings.dbName)
        print('cred_data',cred_data)
        if not cred_data['data']:
            logger.error("Unable to find the credentials")
            return notification_method, {}
            # continue
        mailsettings = cred_data['data'][0]
        print('mailsettings -->',mailsettings)
        if 'password' in mailsettings.keys():
            passwd = mailsettings['password']
            passwd_obj = framework.types.Secret(str(cred_data['data'][0]['password']))
            print('passwd_obj -->',passwd_obj)
            mailsettings['password'] = passwd_obj.get_secret()
        if 'api' in mailsettings.keys():
            passwd = mailsettings['api']
            passwd_obj = framework.types.Secret(str(cred_data['data'][0]['api']))
            mailsettings['api'] = passwd_obj.get_secret()
        # passwd = mailsettings['password']
        # passwd_obj = framework.types.Secret(str(cred_data['data'][0]['password']))
        # mailsettings['password'] = passwd_obj.get_secret(framework.settings.dbName)
        return notification_method, mailsettings
