import fastapi
import re
import os
import yaml
import json
from fastapi.param_functions import Depends
import httpx
import sys
import uuid
import redis
import framework
import typing
import pydantic
import random
import string
import jinja2
import base64
from starlette.types import Scope
import mailApi
import keyCloakManager
import framework.settings
logger = framework.Logger.getInstance('keycloakusermgmt')
import testmailApi

router = fastapi.APIRouter()
KEYCLOAK_URL = "https://localhost:8443"
KEYCLOAK_ADMIN = framework.settings.keycloak_admin
KEYCLOAK_ADMIN_PASSWORD = framework.settings.keycloak_password


def keycloak(method, url, data=None):
    with httpx.Client(verify=False, timeout=180) as client:
        login_data = {
                "client_id": "admin-cli",
                "username": KEYCLOAK_ADMIN,
                "password": KEYCLOAK_ADMIN_PASSWORD,
                "grant_type": "password"
        }

        loginUrl = f'{KEYCLOAK_URL}/auth/realms/master/protocol/openid-connect/token'
        master_login_resp = client.post(loginUrl, data=login_data, timeout=180)
        print('Keycloak Login response:', master_login_resp.text)
        auth_resp = master_login_resp.json()

        url = f'{KEYCLOAK_URL}/auth/admin/realms/{url}'
        headers = {
            "Authorization": f'Bearer {auth_resp["access_token"]}'
        }
        if data:
            resp = client.request(method.upper(), url, headers=headers, json=data, timeout=180)
        else:
            resp = client.request(method.upper(), url, headers=headers, timeout=180)
        if int(resp.status_code / 100) != 2:
            logger.info('Error:', method, url, resp.status_code, resp.text)
            return resp.text

        return resp.json() if resp.text else ''


def get_realm() -> str:
    return framework.ctx['tenant']


def get_client():
    realm = get_realm()
    client_details = keycloak('get', f'{realm}/clients?clientId={realm}client')
    return client_details[0]


def GetAcls():
    rpt = framework.context.context.get('rpt', {})
    data = {"includes": [x.strip() for x in rpt.get('includes', '').split(',') if x.strip()],
            'excludes': [x.strip() for x in rpt.get('excludes', '').split(',') if x.strip()]}
    return data


class Role(pydantic.BaseModel):
    id:str
    name:str
    composite:bool
    clientRole:bool
    containerId:str


class RoleCreate(pydantic.BaseModel):
    name: str
    resourceAccess: typing.Dict[str, typing.List[typing.Dict[str, str]]]


class UserSpec(pydantic.BaseModel):
    enabled: bool = True
    attributes:typing.Dict = {}
    groups: typing.List = []
    emailVerified:bool = True
    email: str
    id: str = ''
    firstName: str
    lastName: str
    username: str = ''
    role: Role


class KeycloakIdentity(pydantic.BaseModel):
    alias: str
    config: typing.Dict = {}
    enabled:bool = True
    providerId: str


@router.get("/kidentityproviders/available", tags=['IdentityProviders'])
def get_available_providers(request: fastapi.Request, realm: str=fastapi.Depends(get_realm)):
    fname = '/data/cybercns/cyberbase/keycloakidentityproviders.yml'
    if not os.path.exists(fname):
        return []
    with open(fname, "rb") as fh:
        data = yaml.safe_load(fh)

    hosturl = request.base_url.hostname
    # Adding Redirect URL
    for d in data:
        alias = d['parameters']['alias']
        d['redirect_uri'] = f'https://{hosturl}/auth/realms/{realm}/broker/{alias}/endpoint'

    return data


@router.get("/kidentityproviders", tags=['IdentityProviders'])
def get_identities(realm: str=fastapi.Depends(get_realm)):
    resp = keycloak("get", f'{realm}/identity-provider/instances')
    for r in resp:
        alias = r.get('alias', '')
        r['redirect_uri'] = f"https://{realm}.mycybercns.com/auth/realms/{realm}/broker/{alias}/endpoint"
    return resp


@router.get("/kidentityproviders/{alias}", tags=['IdentityProviders'])
def get_identity(alias: str, realm: str=fastapi.Depends(get_realm)):
    resp = keycloak("get", f'{realm}/identity-provider/instances/{alias}')
    return resp


@router.post("/kidentityproviders", tags=['IdentityProviders'])
def create_identity(request: fastapi.Request, identity: KeycloakIdentity, realm: str=fastapi.Depends(get_realm)):
    iddata = identity.dict()
    iddata['config']['syncMode'] = 'IMPORT'
    iddata['firstBrokerLoginFlowAlias'] = 'CCNS'
    resp = keycloak("post", f'{realm}/identity-provider/instances', iddata)

    # Creating Mapper to assign default role
    alias = iddata.get('alias', '')
    mapdata = {'name': 'Default Read-Only Role', 'identityProviderMapper': 'oidc-hardcoded-role-idp-mapper',
               'identityProviderAlias': alias, 'config': {'syncMode': 'INHERIT', 'role': 'norole'}}
    mapper_url = f'{realm}/identity-provider/instances/{alias}/mappers'
    mapresp = keycloak('post', mapper_url, mapdata)

    return True, 'Identity Created'


@router.put("/kidentityproviders", tags=['IdentityProviders'])
def update_identity(request: fastapi.Request, identity: KeycloakIdentity, realm: str=fastapi.Depends(get_realm)):
    alias = identity.alias
    iddata = identity.dict()
    resp = keycloak("put", f'{realm}/identity-provider/instances/{alias}', iddata)
    return True, 'Identity Updated'


@router.delete("/kidentityproviders/{alias}", tags=['IdentityProviders'])
def delete_identity(alias: str, realm: str=fastapi.Depends(get_realm)):
    resp = keycloak("delete", f'{realm}/identity-provider/instances/{alias}')
    return True, "Deleted"


@router.get("/kusers", tags=['Users'])
def get_users(query: typing.Optional[str]=None, realm: str =fastapi.Depends(get_realm)):
    search_params = f'{realm}/users'
    if query:
        search_params = search_params + "?" + query
    resp = keycloak("get", search_params)
    for user in resp:
        user["roles"] = _get_user_role(user["id"], realm)
    return resp


@router.post("/kusers", tags=['Users'])
def create_user(request: fastapi.Request, usr: UserSpec, realm: str=fastapi.Depends(get_realm)):
    # checking if user can be created
    cookie_id = request.cookies.get('framework', None)
    if cookie_id:
        r = redis.Redis(db=4)
        cookie = r.hget("CookieStore", cookie_id)
        r.close()
        if cookie:
            if isinstance(cookie, bytes):
                cookie = cookie.decode()
            rpt = json.loads(base64.urlsafe_b64decode(cookie.split('.')[1] + '=====').decode())
            includes = rpt.get('includes', '')
            excludes = rpt.get('excludes', '')
            if includes or excludes:
                return False, "User can't be created"

    # Create user
    usr.username = usr.email
    usrrecord = usr.dict()
    regex_str = re.compile('[@_!#$%^&*()<>?/\|}{~:]')
    if (regex_str.search(usrrecord['firstName']) != None) | (regex_str.search(usrrecord['lastName']) != None):
        return {"status":False, "message":"Only AlphaNumberic is allowed", "data": []}
    if not usrrecord['firstName']:
        return {"status":False, "message":"First Name is invalid", "data": []}
    if not usrrecord['lastName']:
        return {"status":False, "message":"Last Name is invalid", "data": []}
    if not usrrecord['email']:
        return {"status":False, "message":"Email Name in invalid", "data": []}
    email_regex_str = re.compile('[!#$%^&*()<>?/\|}{~:]')
    if (email_regex_str.search(usrrecord['email']) != None):
        return {"status":False, "message":"Only AlphaNumberic is allowed", "data":[]}
    if usrrecord['firstName'] == "":
        return {"status":False, "message":"First name is empty", "data":[]}
    if usrrecord['lastName'] == "":
        return {"status":False, "message":"Last name is empty", "data":[]}
    if usrrecord['role']['id'] == '':
        return {"status":False, "message":"Role name is empty", "data":[]}
    if usrrecord['role']['name'] == '':
        return {"status":False, "message":"Role name is empty","data":[]}
    if usrrecord['email'] == '':
        return {"status":False, "message":"Email name is empty", "data":[]}

    del usrrecord['role']
    # Adding default required actions for user
    usrrecord['requiredActions'] = ["CONFIGURE_TOTP", "UPDATE_PASSWORD", "VERIFY_EMAIL"]
    resp = keycloak("post", f'{realm}/users', usrrecord)

    createdusr = keycloak("get", f'{realm}/users?email={usr.email}')

    # Set user password
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    creds = {"type": "password", "value": password, "temporary": True}
    passwd = keycloak('put',f'{realm}/users/{createdusr[0]["id"]}/reset-password', creds)
    userdata = {"reset_link": f"https://{request.url.hostname}", "email": usr.email, "password": password}
    print(userdata)
    _sendPasswordResetLink(userdata)
    
    # Set the role for the user
    _update_user_role(createdusr[0]["id"], usr.role, realm)

    #create the user in database for the dataleak
    databaseuserdata = {"email": usr.email, "attributes": usr.attributes}
    # _createDatabaseUser(databaseuserdata, realm)
    return True, "User created successfully"


@router.put("/kusers", tags=['Users'])
def update_user(request: fastapi.Request, usr: UserSpec, realm: str =fastapi.Depends(get_realm)):
    userid = usr.id
    usr.username = usr.email
    usrrecords = usr.dict()
    regex_str = re.compile('[@_!#$%^&*()<>?/\|}{~:]')
    if (regex_str.search(usrrecords['firstName']) != None) | (regex_str.search(usrrecords['lastName']) != None):
        return {"status":False, "message":"Only AlphaNumberic is allowed", "data": []}
    if not usrrecords['firstName']:
        return {"status":False, "message":"First Name is invalid", "data": []}
    if not usrrecords['lastName']:
        return {"status":False, "message":"Last Name is invalid", "data": []}
    if not usrrecords['email']:
        return {"status":False, "message":"Email Name in invalid", "data": []}
    email_regex_str = re.compile('[_!#$%^&*()<>?/\|}{~:]')
    if (email_regex_str.search(usrrecords['email']) != None):
        return {"status":False, "message":"Only AlphaNumberic is allowed", "data":[]}
    if usrrecords['firstName'] == "":
        return {"status":False, "message":"First name is empty", "data":[]}
    if usrrecords['lastName'] == "":
        return {"status":False, "message":"Last name is empty", "data":[]}
    if usrrecords['role']['id'] == '':
        return {"status":False, "message":"Role name is empty", "data":[]}
    if usrrecords['role']['name'] == '':
        return {"status":False, "message":"Role name is empty","data":[]}
    if usrrecords['email'] == '':
        return {"status":False, "message":"Email name is empty", "data":[]}

    canchange = True
    # Logged in user can't update role and attributes for himself
    cookie_id = request.cookies.get('framework', None)
    if cookie_id:
        r = redis.Redis(db=4)
        cookie = r.hget("CookieStore", cookie_id)
        r.close()
        if cookie:
            if isinstance(cookie, bytes):
                cookie = cookie.decode()
            rpt = json.loads(base64.urlsafe_b64decode(cookie.split('.')[1] + '=====').decode())
            includes = rpt.get('includes', '')
            excludes = rpt.get('excludes', '')
            if includes or excludes:
                canchange = False

    usrrecord = {"firstName": usr.firstName, "lastName": usr.lastName}
    if getattr(usr, 'attributes', None) and canchange:
        usrrecord['attributes'] = usr.attributes

    resp = keycloak("put", f'{realm}/users/{userid}', usrrecord)

    # Update user role
    if canchange:
        _update_user_role(userid, usr.role, realm)

    # update the user in database for the dataleak
    databaseuserdata = {"email": usr.email, "attributes": usr.attributes}
    _updateDatabaseUser(databaseuserdata, realm)
    return True, "User updated successfully"


@router.delete("/kusers/{userid}", tags=['Users'])
def delete_user(userid: str, realm: str =fastapi.Depends(get_realm)):
    resp = keycloak("delete", f'{realm}/users/{userid}')
    return resp


@router.get("/kusers/getLoginAuditStatus", tags=['LoginAudit'])
def get_login_audit_status(realm: str =fastapi.Depends(get_realm)):
    resp = keycloak("get", f'{realm}/events/config')
    if resp.get('eventsEnabled'):
        return True, "Audit Logs Enabled"
    return False, "Audit Logs Not Enabled"


@router.get("/kusers/enableLoginAudit", tags=['LoginAudit'])
def enable_login_audit(realm: str =fastapi.Depends(get_realm)):
    json = {"eventsEnabled": True, "eventsListeners": ["jboss-logging"],
            "enabledEventTypes": ["LOGIN", "LOGIN_ERROR", "LOGOUT_ERROR", "DELETE_ACCOUNT", "DELETE_ACCOUNT_ERROR"],
            "adminEventsEnabled": False, "adminEventsDetailsEnabled": False, "eventsExpiration": 5184000}
    resp = keycloak("put", f'{realm}/events/config',json)
    return True, "Enabled"


@router.get("/kusers/loginEvents", tags=['LoginEvents'])
def get_login_events(pagenum:int,realm: str =fastapi.Depends(get_realm)):
    resp = keycloak("get", f'{realm}/events?first='+str(pagenum))
    print('resp --->',resp)
    return resp


@router.get("/kroles", tags=['Roles'])
def get_roles(query: typing.Optional[str]=None, realm: str =fastapi.Depends(get_realm)):
    search_params = f'{realm}/roles'
    if query:
        search_params = search_params + "?" + query
    roles = keycloak("get", search_params)
    resp = []
    if roles:
        resp = list(filter(lambda role: (role["name"].lower() not in ['uma_authorization', 'offline_access', f'default-roles-{realm}', 'agent']
                                         and not (role['name'].lower().startswith('default-roles-') and realm in role['name'].lower())), roles))
    return resp


@router.post("/kroles", tags=['Roles'])
def create_role(role: RoleCreate, client=fastapi.Depends(get_client), realm: str =fastapi.Depends(get_realm)):
    # Get the client id
    client_id = client["id"]

    # checking if this role name can be created
    rolename = role.name.lower()
    if rolename in ['admin', 'itadmin', 'readonly', 'norole', 'agent']:
        return False, "This role name can't be used"

    # Create Realm role
    resp = keycloak("post", f'{realm}/roles', {'name': role.name})
    role_details = keycloak("get", f'{realm}/roles/{role.name}')
    logger.info('Creating Role:%s ClientId:%s' % (role_details, client_id))

    # Create Resources with type set to role name
    for resource, scopes in role.resourceAccess.items():
      if scopes:
        resource_spec = {
            "scopes": scopes,
            "attributes":{},
            "uris":[],
            "name": f'{resource}_{role.name}',
            "ownerManagedAccess":"",
            "displayName": f'{resource}_{role.name}',
            "type": role.name
        }
        resp = keycloak('post', f'{realm}/clients/{client_id}/authz/resource-server/resource', resource_spec)

    # Create Role policy
    policy = {
        "type":"role",
        "logic":"POSITIVE",
        "decisionStrategy":"UNANIMOUS",
        "name": f'{role.name}_policy',
        "roles":[{"id":role_details["id"]}]
        }
    resp = keycloak('post', f'{realm}/clients/{client_id}/authz/resource-server/policy/role', policy)
    policy_details = keycloak('get', f'{realm}/clients/{client_id}/authz/resource-server/policy?first=0&max=20&name={role.name}&permission=false')
    logger.info('Policy:', policy_details)

    # Create Permission with the Role policy
    permission = {
        "type":"resource",
        "logic":"POSITIVE",
        "decisionStrategy":"UNANIMOUS",
        "resourceType": role.name,
        "name": f'{role.name}_permission',
        "policies":[policy_details[0]["id"]]
        }
    permission_details = keycloak('post', f'{realm}/clients/{client_id}/authz/resource-server/permission/resource', permission)
    logger.info('Permission:', permission_details)

    return True, 'Role created successfully'


@router.put("/kroles", tags=['Roles'])
def update_role(role: RoleCreate, client=fastapi.Depends(get_client), realm: str =fastapi.Depends(get_realm)):
    #Get the client id
    client_id = client["id"]

    # checking if this role name can be updated
    rolename = role.name.lower()
    if rolename in ['admin', 'itadmin', 'readonly', 'norole', 'agent']:
        return False, "This role can't be updated"

    logger.info("Updating role:%s clientid:%s" % (role.name, client_id))

    # Delete All Resource and Create the Resource
    resp = keycloak("get", f'{realm}/clients/{client_id}/authz/resource-server/resource?deep=false&type={role.name}')
    for res in resp:
        keycloak("delete", f'{realm}/clients/{client_id}/authz/resource-server/resource/{res["_id"]}')

    for resource, scopes in role.resourceAccess.items():
      if scopes:
        resource_spec = {
            "scopes": scopes,
            "attributes":{},
            "uris":[],
            "name": f'{resource}_{role.name}',
            "ownerManagedAccess":"",
            "displayName": f'{resource}_{role.name}',
            "type": role.name
        }
        resp = keycloak('post', f'{realm}/clients/{client_id}/authz/resource-server/resource', resource_spec)
    return True, 'Role updated successfully'


@router.delete("/kroles/{role}", tags=['Roles'])
def delete_role(role:str, client=fastapi.Depends(get_client), realm: str =fastapi.Depends(get_realm)):
    if role in ['admin', 'itadmin', 'readonly', 'norole', 'agent']:
        return False, "This role can't be deleted"

    # Get the client id
    client_id = client["id"]
    logger.info('Deleting Role:%s ClientId:%s' % (role, client_id))

    # Delete permission
    permission = keycloak('get', f'{realm}/clients/{client_id}/authz/resource-server/permission?first=0&max=20&name={role}_permission')
    if permission:
        resp = keycloak('delete', f'{realm}/clients/{client_id}/authz/resource-server/permission/{permission[0]["id"]}')

    # Delete Policy
    policy = keycloak('get', f'{realm}/clients/{client_id}/authz/resource-server/policy?&name={role}_policy&permission=false')
    if policy:
        resp = keycloak('delete', f'{realm}/clients/{client_id}/authz/resource-server/policy/{policy[0]["id"]}')

    # Delete All Resource and Create the Resource
    resources = keycloak("get", f'{realm}/clients/{client_id}/authz/resource-server/resource?deep=false&type={role}')
    for res in resources:
        keycloak("delete", f'{realm}/clients/{client_id}/authz/resource-server/resource/{res["_id"]}')

    # Delete Realm Role
    resp = keycloak('delete', f'{realm}/roles/{role}')

    return True, "Deleted"


@router.get("/kroles/{role}", tags=['Roles'])
def get_role_details(role: str, client=fastapi.Depends(get_client), realm=fastapi.Depends(get_realm)):
    resource_resp = keycloak("get", f'{realm}/clients/{client["id"]}/authz/resource-server/resource?deep=true&type={role}')
    return {resource['name']: resource.get('scopes', []) for resource in resource_resp if resource}


class ApiClientCreate(pydantic.BaseModel):
    name: str
    role: Role

class ApiClient(pydantic.BaseModel):
    name: str
    clientId: str
    role: Role

@router.get("/kapiclients", tags=["ApiClients"])
def get_api_clients(client=fastapi.Depends(get_client), realm=fastapi.Depends(get_realm)):
    clients = _get_api_clients(realm)
    finalClients = []
    for client in clients:
        status, role = get_api_client_role(clientId=client['clientId'], realm=realm)
        if status:
            client['role'] = role
        else:
            continue
        if role == "agent":
            continue
        finalClients.append(client)
    return True, finalClients


@router.get("/kapiclients/{clientId}", tags=["ApiClients"])
def get_api_client_secret(clientId: str, client=fastapi.Depends(get_client), realm=fastapi.Depends(get_realm)):
    client_data = _get_api_clients(realm, clientId)
    if not client_data:
        return False, "Client Not Available"
    resource_resp = keycloak("get", f'{realm}/clients/{client_data[0]["id"]}/client-secret')
    return True, resource_resp['value']


@router.post("/kapiclients", tags=['ApiClients'])
def create_api_client(clientData: ApiClientCreate, client=fastapi.Depends(get_client), realm: str =fastapi.Depends(get_realm)):
    return keyCloakManager.KeyClockSecret().create_client(str(uuid.uuid4()), realm, role_assign=clientData.role.name, clientName=clientData.name, isApiClient=True)


@router.post("/kapiclients/{id}/getApiKey", tags=['ApiClients'])
def generate_apiKey(clientData: ApiClientCreate, client=fastapi.Depends(get_client), realm: str =fastapi.Depends(get_realm)):
    apiClients = _get_api_clients(realm)
    clientId = str(uuid.uuid4())
    for client in apiClients:
        if client['name'] == clientData.name:
            clientId = client['clientId']
            break
    return keyCloakManager.KeyClockSecret().create_client(clientId, realm, role_assign=clientData.role.name, clientName=clientData.name, isApiClient=True)



@router.post("/kapiclients/{clientId}/getclientrole", tags=['ApiClients'])
def get_api_client_role(clientId: str, client=fastapi.Depends(get_client), realm: str =fastapi.Depends(get_realm)):
    client_data = _get_api_clients(realm, clientId)
    if not client_data:
        return False, "Client Not Available"

    service_account_user = keycloak("get", f'{realm}/clients/{client_data[0]["id"]}/service-account-user')
    service_account_id = service_account_user['id']
    composite_roles = keycloak("get", f'{realm}/users/{service_account_id}/role-mappings/realm/composite')
    return True, composite_roles[0]['name']


@router.put("/kapiclients", tags=['ApiClients'])
def update_api_client(clientData: ApiClient, client=fastapi.Depends(get_client), realm: str =fastapi.Depends(get_realm)):
    client_data = _get_api_clients(realm, clientData.clientId)
    if not client_data:
        return False, "Client Not Available"
    return keyCloakManager.KeyClockSecret().create_client(clientData.clientId, realm, role_assign=clientData.role.name, clientName=clientData.name, isApiClient=True)


@router.delete("/kapiclients/{clientId}", tags=['ApiClients'])
def delete_api_client(clientId: str, client=fastapi.Depends(get_client), realm: str =fastapi.Depends(get_realm)):
    client_data = _get_api_clients(realm, clientId)
    if not client_data:
        return False, "Client Not Available"
    return True, keycloak("delete", f'{realm}/clients/{client_data[0]["id"]}')


def _get_api_clients(realm: str, clientId: typing.Optional[str]= None):
    url = f'{realm}/clients'
    if clientId and len(clientId) > 0:
        url += f"?clientId={clientId}&search=true"
    resource_resp = keycloak("get", url)
    clients = [{"name": resource['name'], "clientId": resource["clientId"], "role": "", "clientSecret": "", 'id': resource['id']}
               for resource in resource_resp if
               resource.get('name') and 'cyberapiclient' in resource.get("description", "").lower()]
    return clients


def _getClientDetails(realm, clients):
    pass

def _get_user_role(user:str, realm: str):
    return keycloak("get", f'{realm}/users/{user}/role-mappings')


def _update_user_role(userid: str, role: Role, realm: str):
    # Delete All Role Mappings
    attached_roles = keycloak('get', f'{realm}/users/{userid}/role-mappings/realm')
    #for r in attached_roles:
    keycloak('delete', f'{realm}/users/{userid}/role-mappings/realm', attached_roles)
    return keycloak("post", f'{realm}/users/{userid}/role-mappings/realm', [role.dict()])


def _sendPasswordResetLink(userdata):
    smartreconpath = framework.settings.smartrecon_path
    print(smartreconpath)
    data = open(f"{smartreconpath}password_reset.html", encoding="utf-8").read()
    template = jinja2.Template(data)
    final = template.render(userdata)
    logger.info("Sending Email " + userdata['email'])
    print("Sending Email")
    #status, msg = mailApi.sendemail("Welcome to CyberCNS", final, userdata['email'], fromuser="CyberCNS<support@cybercns.com>",
    #                  attachFiles=[], isHtml=True)
    testmailApi.sendemail(toEmail=userdata['email'], body=final, subject="Welcome to the Recon Application", attachFiles=[], isHtml=True)
    print("Email Sent")


def _createDatabaseUser(userdata, realm_name, password="lingsunku#123"):
    print(f"the user data which is coming inside create database user is {userdata}")
    print(f"the realm_name which is coming inside create database user is {realm_name}")
    dlsquery =  {"bool":  {}}
    if userdata.get('attributes')['includes']:
        includes = userdata.get('attributes')['includes']
        dlsquery["bool"] = {"should": []}
        for company in includes.split(','):
            dlsquery['bool']['should'].append({"match": {"companyRef.id": company}})
            dlsquery['bool']['should'].append({"match": {"_id": company }})
    if userdata.get('attributes')['excludes']:
        dlsquery["bool"] = {"must_not": []}
        exculdes = userdata.get('attributes')['excludes']
        for company in exculdes.split(','):
            dlsquery['bool']['must_not'].append({"match": {"companyRef.id": company}})
            dlsquery['bool']['must_not'].append({"match": {"_id": company }})
    if not userdata.get('attributes').get('includes') and not userdata.get('attributes').get('excludes'):
        dlsquery = ""
    dburl = framework.settings.db_urls["elastic"][0]
    ELASTIC_URL = f"{dburl.scheme}://{dburl.user}:{dburl.password}@{dburl.host}:{dburl.port}/"
    # data = {"description": "Tenant for " + realm_name}
    with httpx.Client(verify=False) as client:
        # response = client.put(f'{ELASTIC_URL}_opendistro/_security/api/tenants/{realm_name}', json=data)
        # if str(response.status_code).startswith("2"):
            data = {
                "cluster_permissions": [
                    "cluster_composite_ops",
                    "indices_monitor",
                    "cluster:admin/opendistro/reports/menu/download"
                ],
                "index_permissions": [{
                    "index_patterns": [
                        f'{realm_name}*'
                    ],
                    "dls": json.dumps(dlsquery),
                    "fls": [],
                    "masked_fields": [],
                    "allowed_actions": [
                        "read",
                        "cluster:admin/opendistro/reports/instance/create",
                        "cluster:admin/opendistro/reports/instance/get",
                        "cluster:admin/opendistro/reports/definition/delete",
                        "cluster:admin/opendistro/reports/definition/create",
                        "cluster:admin/opendistro/reports/definition/list",
                        "cluster:admin/opendistro/reports/definition/get",
                        "cluster:admin/opendistro/reports/definition/on_demand",
                        "cluster:admin/opendistro/reports/definition/update"
                    ]
                }],
                "tenant_permissions": [{
                    "tenant_patterns": [
                        f'{realm_name}'
                    ],
                    "allowed_actions": [
                        "kibana_all_write"
                    ]
                }]
            }
            if not dlsquery:
                data['index_permissions'][0]['dls'] = ''
            response = client.put(f'{ELASTIC_URL}_opendistro/_security/api/roles/{userdata["email"]}_role', json=data)
            if str(response.status_code).startswith("2"):
                data = {
                    "password": password,
                    "opendistro_security_roles": [f"{userdata['email']}_role"],
                    "backend_roles": [],
                    "attributes": {
                        "realm": f'{realm_name}'
                    }
                }
                client.put(f'{ELASTIC_URL}_opendistro/_security/api/internalusers/{userdata["email"]}_kibana', json=data)
                data = {
                    "backend_roles": [],
                    "hosts": [],
                    "users": [f"{userdata['email']}_kibana"]
                }
                client.put(f'{ELASTIC_URL}_opendistro/_security/api/rolesmapping/{userdata["email"]}_role',json=data)


def _updateDatabaseUser(userdata, realm_name):
    dburl = framework.settings.db_urls["elastic"][0]
    ELASTIC_URL = f"{dburl.scheme}://{dburl.user}:{dburl.password}@{dburl.host}:{dburl.port}/"
    with httpx.Client(verify=False) as client:
        roleresponse = client.delete(f'{ELASTIC_URL}_opendistro/_security/api/roles/{userdata["email"]}_role')
        if str(roleresponse.status_code).startswith("2"):
            userresponse = client.delete(f'{ELASTIC_URL}_opendistro/_security/api/internalusers/{userdata["email"]}_kibana')
            if str(userresponse.status_code).startswith("2"):
                _createDatabaseUser(userdata, realm_name)
                return True, "Succesfully Updated"
            else:
                return False, userresponse.text
        else:
            return False, roleresponse.text

def _deleteDatabaseUser(userdata, realm_name):
    dburl = framework.settings.db_urls["elastic"][0]
    ELASTIC_URL = f"{dburl.scheme}://{dburl.user}:{dburl.password}@{dburl.host}:{dburl.port}/"
    with httpx.Client(verify=False) as client:
        roleresponse = client.delete(f'{ELASTIC_URL}_opendistro/_security/api/roles/{userdata["email"]}_role')
        if str(roleresponse.status_code).startswith("2"):
            userresponse = client.delete(f'{ELASTIC_URL}_opendistro/_security/api/internalusers/{userdata["email"]}_kibana')
            if str(userresponse.status_code).startswith("2"):
                return True, "Succesfully Deleted"
            else:
                return False, userresponse.text
        else:
            return False, roleresponse.text

