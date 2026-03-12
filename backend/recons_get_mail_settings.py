from recons_enum import *
from recons_model import *
import fastapi
import json

router = fastapi.APIRouter(prefix='/recons')

@router.post('/get_mail_settings', tags=['Recons'])
async def Reconsget_mail_settings(data: get_mail_settingsParams):
    mailsettings = {}
    ins = framework.postgresmodel.PostgresModel()
    query = {'query': {'bool': {'must': [{'match': {'family.keyword': "integrations"}}, {'match': {'species.keyword': "ticketing"}}, {'match': {'reconId.keyword': str(data.reconId)}}]}}}
    params = framework.queryparams.QueryParams()
    params.limit = 10000
    params.q = json.dumps(query)
    try:
        resp = await ins.get_all(params, framework.settings.dbName)
        data = resp.get("data", [])
    except Exception as e:
        return {"status": False, "message": e, "data": []}
    return {"status": True, "message": "Success", "data": data}
    status, integration_data = ins.get_all(query)
    if not status or not integration_data.get('data'):
        # no integration data or some read error. Set default mail settings
        # mailsettings = self.mclient['emailsettings'].find_one()
        mailsettings = {}
    notification_method = ''
    for integration in integration_data.get('data', []):
        notification_method = integration.get('product', '')
        cred_id = integration.get('credId')
        status, creds = credentials.Credentials().getCredentials(notification_method, keyid=cred_id)
        if not status or not creds:
            logger.error("Unable to find the credentials")
            continue
        mailsettings = creds.get('params')
        if mailsettings:
            break
    return mailsettings,notification_method