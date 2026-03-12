import framework
import os
import json
import uuid
import glob
import time
import httpx
import boto3
import base64
import string
import random
import mailApi
import asyncio
import Helpers
import requests
import datetime
import pandas as pd
import framework.settings
from jinja2 import Template
import framework.postgresmodel


def getDNSEntry(domainName):
    # alias id the server ip
    hostedZoneId = ""
    awsapikey = ""
    awsseckey = ""
    max_records = 1000
    # Checking DNS Entry
    # print(domainName)
    client = boto3.client('route53', aws_access_key_id=awsapikey, aws_secret_access_key=awsseckey)
    dns_records = []
    dns_in_iteration = client.list_resource_record_sets(HostedZoneId=hostedZoneId)
    dns_records.extend(dns_in_iteration['ResourceRecordSets'])
    # Looping over DNS Records
    while len(dns_records) < max_records and 'NextRecordName' in dns_in_iteration.keys():
        next_record_name = dns_in_iteration['NextRecordName']
        # print('listing next set: ' + next_record_name)
        dns_in_iteration = client.list_resource_record_sets(HostedZoneId=hostedZoneId, StartRecordName=next_record_name)
        dns_records.extend(dns_in_iteration['ResourceRecordSets'])
    # Verifying any of the record matches the DNS
    for record in dns_records:
        if record['Name'].lower() == domainName.lower() + ".":
            return record
    return {}


def createDNSEntry(domainName, alias):
    # alias id the server ip
    hostedZoneId = ""
    awsapikey = ""
    awsseckey = ""
    print("Creating DNS for:%s" % domainName)
    client = boto3.client('route53', aws_access_key_id=awsapikey, aws_secret_access_key=awsseckey)
    changes = []
    oldEntry = getDNSEntry(domainName)
    if oldEntry:
        changes.append({
            'Action': 'DELETE',
            'ResourceRecordSet': {
                'Name': oldEntry['Name'],
                'Type': oldEntry.get('Type', 'A'),  # or AAAA
                'TTL': oldEntry.get('TTL', 15),
                'ResourceRecords': oldEntry.get('ResourceRecords', [])
            }
        })
    changes.append({
                    'Action': 'CREATE',
                    'ResourceRecordSet': {
                        'Name': domainName,
                        'Type': 'A',
                        'TTL': 60,
                        'ResourceRecords': [
                            {'Value': alias},
                        ],
                    }
                })
    response = client.change_resource_record_sets(
        HostedZoneId=hostedZoneId,
        ChangeBatch={
            'Comment': 'Adding domain: %s' % domainName,
            'Changes': changes
        }
    )
    respStatusCode = response.get('ResponseMetadata', {}).get('HTTPStatusCode', 0)
    if respStatusCode == 200:
        return True, "Domain Created successfully"
    return False, "Domain creation failed"


def get_random_string(length=4):
    # Random string with the combination of lower and upper case
    letters = string.ascii_letters
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

def getPassword(passwordKey, defaultpassword):
    password=""
    with open("/etc/environment") as f:
        lines = f.read().strip().splitlines()
        for line in lines:
            if line.startswith(passwordKey):
                temp_pass = line.split(passwordKey+"=")[-1].strip().replace('"', "")
                status, out, err = Helpers.execute(
                    f"echo {temp_pass} | openssl enc -base64 -d -aes-256-cbc -nosalt -pass pass:KasaBisatotwo1"
                    )
                if not status:
                    password=out.decode().strip()
                break
    return password if password else defaultpassword


def ListDiff(list1, list2):
    return list(set(list1) - set(list2)) + list(set(list2) - set(list1))


class KeyClockSecret():
    def __init__(self,authenticationParams={}):
        if hasattr(framework.settings, 'db_urls') and framework.settings.db_urls.get("elastic"):
            dburl = framework.settings.db_urls["elastic"][0]
            self.ELASTIC_URL = f"{dburl.scheme}://{dburl.user}:{dburl.password}@{dburl.host}:{dburl.port}/"
        else:
            self.ELASTIC_URL = "https://admin:admin@localhost:9200/"
        self.KEYCLOAK_URL = authenticationParams.get("server_url", "https://localhost:8443/auth/")
        self.KEYCLOAK_ADMIN = framework.settings.keycloak_admin
        self.KEYCLOAK_ADMIN_PASSWORD = framework.settings.keycloak_password
        self.login_data = {
            "client_id": "admin-cli",
            "username": self.KEYCLOAK_ADMIN,
            "password": self.KEYCLOAK_ADMIN_PASSWORD,
            "grant_type": "password"
        }
        self.clientmap = {'includes': {"name": "includes", "protocol": "openid-connect",
                                       "protocolMapper": "oidc-usermodel-attribute-mapper",
                                       "config": {"access.token.claim": "true", "aggregate.attrs": "",
                                                  "claim.name": "includes", "id.token.claim": "true",
                                                  "jsonType.label": "String", "multivalued": "",
                                                  "user.attribute": "includes", "userinfo.token.claim": "true"}},
                          'excludes': {"name": "excludes", "protocol": "openid-connect",
                                       "protocolMapper": "oidc-usermodel-attribute-mapper",
                                       "config": {"access.token.claim": "true", "aggregate.attrs": "",
                                                  "claim.name": "excludes", "id.token.claim": "true",
                                                  "jsonType.label": "String", "multivalued": "",
                                                  "user.attribute": "excludes", "userinfo.token.claim": "true"}}}

    async def create_msp(self, realm_name, email, firstname="admin", lastname="admin"):
        if framework.ctx["tenant"] != "beta":
            return False, "Not Supported"
        return await self.configure_msp(realm_name, email, firstname, lastname)

    def updateflowdata(self, flowdata):
        smartreconpath = framework.settings.smartrecon_path
        df = pd.read_csv(f"{smartreconpath}recon_auth_flow.csv")
        flowdf = pd.DataFrame(flowdata)
        
        del flowdf['requirement']
        df = df[['displayName', 'requirement']]
        mergedf = flowdf.merge(df, on='displayName')
        mergedf = mergedf[['requirement', 'id']]
        return mergedf.to_dict(orient='records')

    # todo:- need to remove unwanted print statements
    async def configure_msp(self, realm_name, email, firstname="admin", lastname="admin"):
        externalIp = requests.get('https://checkip.amazonaws.com').text.strip()
        # createDNSEntry(f'{realm_name}.mycybercns.com', externalIp)
        with httpx.Client(verify=False) as client:
            # Create Realm
            loginUrl = f'{self.KEYCLOAK_URL}realms/master/protocol/openid-connect/token'
            print('logindata:',self.login_data)
            print('loginUrl:',loginUrl)
            master_login_resp = client.post(loginUrl, data=self.login_data, timeout=60)
            print('Keycloak Login response:', master_login_resp.text)
            auth_resp = master_login_resp.json()
            # print(auth_resp)
            headers = {
                "Authorization": f'Bearer {auth_resp["access_token"]}'
            }
            r = {
                "realm": realm_name,
                "notBefore": 0,
                "enabled": True,
                "sslRequired": "all",
                "bruteForceProtected": True,
                "failureFactor": 10,
                "eventsEnabled": False
            }
            count = 0
            while count < 3:
                try:
                    create_realm = client.post(self.KEYCLOAK_URL+"admin/realms", json=r, headers=headers)
                    if int(create_realm.status_code / 100) != 2:
                        print("Error in creating new msp %s %s" % (create_realm.status_code, create_realm.text))
                    break
                except Exception as e:
                    print("Exception in creating realm %s" % e)
                    print("Waiting for 10 seconds before retry")
                    count += 1
                    time.sleep(30)
                    # return False, "Error in creating new msp"
            realm_resp = client.get(self.KEYCLOAK_URL+f"admin/realms/{realm_name}", headers=headers)
            if int(realm_resp.status_code / 100) != 2:
                return False, "Error in getting msp details after configuration"
            realm_resp = realm_resp.json()
            # todo:- Need to add smtp creds for email
            realm_resp.update({"rememberMe": True, "resetPasswordAllowed": True,
                            "smtpServer": {'password': 'LordShiva4321',
                                           'replyToDisplayName': '', 'starttls': 'true', 'auth': 'true', 'port': '587',
                                           'host': 'smtp.gmail.com', 'from': 'support@netalytics.co',
                                           'ssl': 'false', 'user': 'support@netalytics.co', 'displayName': 'SmartRecon'}})
            realm_resp = client.put(self.KEYCLOAK_URL + f"admin/realms/{realm_name}", headers=headers, json=realm_resp)
            if int(realm_resp.status_code / 100) != 2:
                print("Error in updating realm smtp details status:%s resp:%s" % (realm_resp.status_code,
                                                                                        realm_resp.text))

            # Configuring Default Authentication Parameters
            requiredActions = [{"alias": "CONFIGURE_TOTP", "name": "Configure OTP", "enabled": False, "defaultAction": False,
              "priority": 10, "config": {}},
             {"alias": "terms_and_conditions", "name": "Terms and Conditions", "enabled": True, "defaultAction": True,
              "priority": 20, "config": {}},
             {"alias": "UPDATE_PASSWORD", "name": "Update Password", "enabled": True, "defaultAction": False,
              "priority": 30, "config": {}},
             {"alias": "UPDATE_PROFILE", "name": "Update Profile", "enabled": True, "defaultAction": False,
              "priority": 40, "config": {}},
             {"alias": "VERIFY_EMAIL", "name": "Verify Email", "enabled": True, "defaultAction": False, "priority": 50,
              "config": {}}]
            for record in requiredActions:
                realm_resp = client.put(self.KEYCLOAK_URL + f"admin/realms/{realm_name}/authentication/required-actions/{record['alias']}", headers=headers, json=record)
                print("Action:%s status:%s resp:%s" % (record['alias'], realm_resp.status_code, realm_resp.text))
            r = {'clientId': f'{realm_name}client', 'publicClient': False,
                 'redirectUris': [f'https://{realm_name}.com/api/login']}
            create_client = client.post(f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients', json=r, headers=headers)
            get_client = client.get(f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients?clientId={realm_name}client', headers=headers)
            get_client = get_client.json()
            # print(get_client)
            await asyncio.sleep(2)
            # Create client credentials
            client_secret = client.post(f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{get_client[0]["id"]}/client-secret', headers=headers)

            client_secret = client.get(f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{get_client[0]["id"]}/client-secret', headers=headers)
            # print(client_secret.json())
            get_client[0].update({"serviceAccountsEnabled": True, "name": "CyberCNS", "authorizationServicesEnabled": True})
            edit_client = client.put(f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{get_client[0]["id"]}',
                                     json=get_client[0], headers=headers)
            # Waiting for 10 seconds after realm creation
            await asyncio.sleep(10)
            # Creating Initial Role
            role_mapping = {}
            policy_mapping = {}
            for role, desc in {"admin": "Administrator", "readOnly": "Read Only",
                               "itAdmin": "IT Administrator", "norole": "No Role"}.items():
                admin_role = client.post(f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/roles',
                                         json={"name": role, "description": desc}, headers=headers)
                resp = client.get(f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/roles/{role}', headers=headers)
                if int(resp.status_code / 100) == 2:
                    resp = resp.json()
                    role_mapping[role] = resp["id"]

            # Creating Mappers
            clientid = get_client[0]['id']
            mapurl = f"{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{clientid}/protocol-mappers/models"
            for k,v in self.clientmap.items():
                r = client.post(mapurl, json=v, headers=headers)
                print("Mapping for:%s status:%s response:%s" % (k, r.status_code, r.text))

            # Deleting default Roles
            r = client.get(f"{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{get_client[0]['id']}/authz/resource-server/resource?deep=false&first=0&max=20&name=defa", headers=headers)
            # print(r.json())
            for record in r.json():
                rd = client.delete(
                    f"{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{get_client[0]['id']}/authz/resource-server/resource/{record['_id']}",
                    headers=headers)
                print("Resource delete:%s status:%s resp:%s" % (record['_id'], rd.status_code, rd.text))
            r = client.get(
                f"{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{get_client[0]['id']}/authz/resource-server/policy?deep=false&first=0&max=20&name=defa",
                headers=headers)
            # print(r.json())
            for record in r.json():
                rd = client.delete(
                    f"{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{get_client[0]['id']}/authz/resource-server/policy/{record['id']}",
                    headers=headers)
                print("Policy delete:%s status:%s resp:%s" % (record['id'], rd.status_code, rd.text))
            # todo:- need to remove policies also
            with open(f"{framework.settings.smartrecon_path}globalroles.json") as f:
                roles = json.load(f)
            roles['scopes'] = list({record["name"]: record for record in roles['scopes']}.values())
            roles['policies'] = list({record["name"]: record for record in roles['policies']}.values())
            roles['resources'] = list({record["name"]: record for record in roles['resources']}.values())
            print('KeyCloakURL:',self.KEYCLOAK_URL)
            roles_upload = client.post(
                f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{get_client[0]["id"]}/authz/resource-server/import',
                json=roles, headers=headers)
            if int(roles_upload.status_code / 100) != 2:
                print("Error in importing roles status:%s resp:%s" % (roles_upload.status_code, roles_upload.text))
            await asyncio.sleep(5)
            for role, role_id in role_mapping.items():
                # Creating Policy
                jsonData = {"type": "role", "logic": "POSITIVE", "decisionStrategy": "UNANIMOUS",
                            "name": role + "Policy",
                            "roles": [{"id": role_id}]}
                role_policy = client.post(
                    f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{get_client[0]["id"]}/authz/resource-server/policy/role',
                    json=jsonData, headers=headers)
                if int(role_policy.status_code / 100) != 2:
                    url = f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{get_client[0]["id"]}/authz/resource-server/policy/role'
                    print("Error in generating role policy URL:%s status:%s resp:%s" % (url, role_policy.status_code,
                                                                                        role_policy.text))
                else:
                    policy_mapping[role + "Policy"] = role_policy.json()["id"]
            # Create user
            # email = f'admin@{realm_name}.mycybercns.com'
            r = {"enabled": True, "attributes": {}, "groups": [], "username": email, "emailVerified": "",
                 "email": email, "firstName": firstname, "lastName": lastname}
            create_user = client.post(f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/users', json=r, headers=headers)
            print("Create User email:%s status:%s resp:%s" % (email, create_user.status_code, create_user.text))
            # print(create_user.json())
            get_user = client.get(f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/users?email={email}', headers=headers)
            get_user = get_user.json()
            time.sleep(5)
            # Set user password
            creds = {"type": "password", "value": get_random_string(16), "temporary": True}
            passwd_set = client.put(f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/users/{get_user[0]["id"]}/reset-password', json=creds, headers=headers)
            if int(passwd_set.status_code / 100) != 2:
                print("Error in seting password %s %s" % (passwd_set.status_code, passwd_set.text))
            time.sleep(5)
            passwd_set = client.put(
                f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/users/{get_user[0]["id"]}/reset-password', json=creds,
                headers=headers)
            if int(passwd_set.status_code / 100) != 2:
                print("Error in seting password %s %s" % (passwd_set.status_code, passwd_set.text))
            # Delete All Role Mappings
            attached_roles = client.get(
                f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/users/{get_user[0]["id"]}/role-mappings/realm',
                headers=headers)
            #todo:- has to attach role data as params in delete operation
            if int(attached_roles.status_code / 100) == 2 and len(attached_roles.json()) > 0:
                r = httpx.request('DELETE', f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/users/{get_user[0]["id"]}/role-mappings/realm', headers=headers, json=attached_roles.json(), verify=False)
                if int(r.status_code / 100) != 2:
                    print("Deleteing Role With Status_code %s Resp: %s" % (r.status_code, r.text))

            # Copying First Broker Login as CCNS
            data = {'newName': 'CCNS'}
            flowcopy = client.post(
                f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/authentication/flows/first%20broker%20login/copy',
                json=data, headers=headers)
            print("Flow Copy Status Code:%s Resp:%s" % (flowcopy.status_code, flowcopy.text))

            # Update the Flow
            flowdata = client.get(
                f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/authentication/flows/CCNS/executions',
                headers=headers
            )
            if int(flowdata.status_code / 100) == 2:
                updateurl = f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/authentication/flows/CCNS/executions'
                changed = self.updateflowdata(flowdata.json())
                for record in changed:
                    resp = client.put(updateurl, json=record, headers=headers)

            # Get All Available Roles
            admin_role = {}
            getavailable_roles = client.get(
                f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/users/{get_user[0]["id"]}/role-mappings/realm/available',
                headers=headers)
            if int(getavailable_roles.status_code / 100) != 2:
                print("Error in getting available roles status:%s resp:%s" % (getavailable_roles.status_code,
                                                                                    getavailable_roles.text))
            else:
                for role in getavailable_roles.json():
                    if role["name"] == "admin":
                        admin_role = role
                        break
            update_role = client.post(
                f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/users/{get_user[0]["id"]}/role-mappings/realm',
                json=[admin_role], headers=headers)

            # domain_name = f'{realm_name}.mycybercns.com'
            # createDNSEntry(domain_name, externalIp)
            # await asyncio.sleep(5)
            # os.system(f'cp /data/cybercns_nginx_template.conf /etc/nginx/conf.d/{realm_name}.conf;sed -i "/server_name/c\server_name {domain_name};" /etc/nginx/conf.d/{realm_name}.conf')
            # # {realm_name}_kibana,lingsunku#123
            # authcode = base64.b64encode(f"{realm_name}_kibana:lingsunku#123".encode()).decode()
            # os.system(f'sed -i "s/YWRtaW46YWRtaW4=/{authcode}/g" /etc/nginx/conf.d/{realm_name}.conf')
            # cmd = f"certbot --nginx --non-interactive --agree-tos -m support@netalytics.co -d {domain_name} --redirect"
            # os.system(cmd)
            # await self.createElasticUser(realm_name)
            userdata = {"reset_link": f"https://{realm_name}.com", "email": email, "password": creds["value"], "first_name": firstname, "last_name": lastname}
            self.sendPasswordResetLink(userdata)
            return True, creds["value"]

    async def create_user(self, userdetails):
        realm_name = ""
        email = userdetails["email"]
        password = userdetails["password"]
        firstname = userdetails["firstname"]
        lastname = userdetails["lastname"]
        role = userdetails["role"]
        with httpx.Client(verify=False) as client:
            # Create Realm
            loginUrl = f'{self.KEYCLOAK_URL}realms/master/protocol/openid-connect/token'
            master_login_resp = client.post(loginUrl, data=self.login_data)
            # print('Keycloak Login response:', master_login_resp.text)
            auth_resp = master_login_resp.json()
            # print(auth_resp)
            headers = {
                "Authorization": f'Bearer {auth_resp["access_token"]}'
            }
            # Create user
            # email = f'admin@{realm_name}.mycybercns.com'
            r = {"enabled": True, "attributes": {}, "groups": [], "username": email, "emailVerified": "",
                 "email": email, "firstName": firstname, "lastName": lastname}
            create_user = client.post(f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/users', json=r, headers=headers)
            print("Create User:%s status:%s resp:%s" % (create_user.text))
            # print(create_user.json())
            get_user = client.get(f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/users?email={email}', headers=headers)
            get_user = get_user.json()

            # Set user password
            creds = {"type": "password", "value": password, "temporary": True}
            passwd = client.put(f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/users/{get_user[0]["id"]}/reset-password',
                                json=creds, headers=headers)
            domain_name = f'{realm_name}.com'
            await asyncio.sleep(5)
            userdata = {"reset_link": f"https://{realm_name}.com", "email": email, "password": creds["value"]}
            self.sendPasswordResetLink(userdata)
            return True, creds["value"]

    def sendPasswordResetLink(self, userdata):
        smartreconpath = framework.settings.smartrecon_path
        data = open(f"{smartreconpath}password_reset.html", encoding="utf-8").read()
        template = Template(data)
        final = template.render(userdata)
        print(userdata)
        print("Sending Email " + userdata['email'])
        print(mailApi.sendemail("Welcome to Smart Recon Beta", final, userdata['email'],
                                      fromuser="SmartRecon<support@cybercns.com>", attachFiles=[], isHtml=True))

    async def addExternalScanAgent(self, realm_name):
        clientId = "externalscanagent"
        status, client_details = self.create_client(clientId, realm_name)
        Helpers.execute("mkdir -p /data/CyberCNSAgentV2/netatemp;chown -R cybercns. /data/CyberCNSAgentV2/netatemp")
        print(Helpers.execute(f"cd /data/agents/2.0.8;chmod +x cybercnsagent_linux;./cybercnsagent_linux -b {realm_name}.com -a {clientId} -s {client_details['clientsecret']} -i Probe"))

    async def createElasticUser(self, realm_name):
        data = {"description": "Tenant for " + realm_name}
        with httpx.Client(verify=False) as client:
            response = client.put(f'{self.ELASTIC_URL}_opendistro/_security/api/tenants/{realm_name}', json=data)
            if str(response.status_code).startswith("2"):
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
                        "dls": "",
                        "fls": [],
                        "masked_fields": [],
                        "allowed_actions": [
                            "read",
                            "cluster:admin/opendistro/reports/definition/create",
                            "cluster:admin/opendistro/reports/definition/list",
                            "cluster:admin/opendistro/reports/definition/get",
                            "cluster:admin/opendistro/reports/instance/create",
                            "cluster:admin/opendistro/reports/instance/get"
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
                response = client.put(f'{self.ELASTIC_URL}_opendistro/_security/api/roles/{realm_name}_role', json=data)
                if str(response.status_code).startswith("2"):
                    data = {
                        "password": "lingsunku#123",
                        "opendistro_security_roles": [f"{realm_name}_role"],
                        "backend_roles": [],
                        "attributes": {
                            "realm": f'{realm_name}'
                        }
                    }
                    client.put(f'{self.ELASTIC_URL}_opendistro/_security/api/internalusers/{realm_name}_kibana', json=data)
                    data = {
                        "backend_roles": [],
                        "hosts": [],
                        "users": [f"{realm_name}_kibana"]
                    }
                    client.put(f'{self.ELASTIC_URL}_opendistro/_security/api/rolesmapping/{realm_name}_role',
                               json=data)

        ins = framework.postgresmodel.PostgresModel()
        ins.Config.collection_name = 'test'
        datauuid = str(uuid.uuid4())
        els_data = {"name": realm_name, "u": datetime.datetime.utcnow(), "c": datetime.datetime.utcnow()}
        client = await ins.client()
        resp = await client.create(f'test_{realm_name}', str(datauuid), els_data, refresh=True)
        await client.delete(f'test_{realm_name}', resp['_id'])
        ins = framework.postgresmodel.PostgresModel()
        ins.Config.collection_name = 'test_timeseries'
        client = await ins.client()
        resp = await client.create(f'test_{realm_name}_timeseries', str(datauuid), els_data, refresh=True)
        await client.delete(f'test_{realm_name}_timeseries', resp['_id'])
        ins = framework.postgresmodel.PostgresModel()
        ins.Config.collection_name = 'test_ad_audit'
        client = await ins.client()
        resp = await client.create(f'test_{realm_name}_ad_audit', str(datauuid), els_data, refresh=True)
        await client.delete(f'test_{realm_name}_ad_audit', resp['_id'])
        ins = framework.postgresmodel.PostgresModel()
        ins.Config.collection_name = 'test_alerts'
        client = await ins.client()
        resp = await client.create(f'test_{realm_name}_alerts', str(datauuid), els_data, refresh=True)
        await client.delete(f'test_{realm_name}_alerts', resp['_id'])
        await self.createKibanaDashboards(realm_name)
        await self.updateIndexPattern(realm_name)
        # await self.createDefSchedulers(realm_name)
        # await self.addExternalScanAgent(realm_name)


    async def updateIndexPattern(self, realm_name):
        headers = {"osd-xsrf": "kibana", "securitytenant": realm_name}
        headers["Cookie"] = self.headers["Cookie"]
        indexSettings = f"https://localhost:5601/kibana/api/kibana/settings"
        postdata = {"changes": {"defaultIndex": "2c724830-b235-11eb-ae1b-1561ca4cd695"}}
        response = requests.post(indexSettings, headers=headers, data=json.dumps(postdata), verify=False)

    def _getKibanaLoginData(self):
        username, password = self.ELASTIC_URL.split('@')[0].split("/")[-1].split(':')
        loginData = {'username': username, 'password': password}
        return loginData

    def kibanaLogin(self):
        self.headers = {'osd-xsrf': 'reporting', 'Content-Type': 'application/json'}
        try:
            resp = requests.post("https://localhost:5601/kibana/auth/login", headers=self.headers, data=json.dumps(self._getKibanaLoginData()))
            if int(resp.status_code / 100) != 2:
                return False, resp.text
            self.headers['Cookie'] = resp.headers['set-cookie'].split(";")[0]
            return True, "Success"
        except Exception as e:
            return False, "Exception while login to kibana"

    async def createKibanaDashboards(self, realm_name):
        headers = {"osd-xsrf": "kibana", "securitytenant": realm_name}
        status, resp = self.kibanaLogin()
        if not status:
            print("Kibana login failed resp:%s" % resp)
        headers["Cookie"] = self.headers["Cookie"]
        exportUrl = f"https://localhost:5601/kibana/api/saved_objects/_import?overwrite=true"
        dashfiles = os.listdir("/data/dashboards")
        for file in dashfiles:
            os.system(f"cp {os.path.join('/data/dashboards', file)} /tmp/{realm_name}_{file}")
            os.system(f'sed -i "s/cyberindexpattern/test_{realm_name}*/g" /tmp/{realm_name}_{file}')
            os.system(f'sed -i "s/test_ad_audit/test_{realm_name}_ad_audit/g" /tmp/{realm_name}_{file}')
            os.system(f'sed -i "s/domain_name/https:\/\/{realm_name}.com/g" /tmp/{realm_name}_{file}')
            with open(f"/tmp/{realm_name}_{file}", 'rb') as f:
                response = requests.post(exportUrl, headers=headers, files={'file': f}, verify=False)
                print(f"The response status code is: {response.status_code} ")
                if str(response.status_code).startswith("2"):
                    print(f"Dashboard have been succesfully imported")
                else:
                    print("Error while importing the dashboard resp:%s" % response.text)
            os.unlink(f"/tmp/{realm_name}_{file}")

    async def createDefSchedulers(self, realm_name):
        ins = framework.postgresmodel.PostgresModel()
        ins.Config.collection_name = 'test'
        client = await ins.client()
        scheduleData = {"isGlobal": True, "isActive": True, "name": "DefaultAssetDiscovery Scheduler", "uniqueid": "asset_discovery", "scantype": 2, "settings": {"hours": [6]}, "scheduler": "hourly"}
        resp = await client.create(f'test_{realm_name}', str(uuid.uuid4()), scheduleData)
        print(resp)
        scheduleData_external = {"isGlobal": True, "isActive": True,  "name": "DefaultExternal Scheduler", "uniqueid": "external_scan", "scantype": 4, "settings": {"hours": [6]}, "scheduler": "hourly"}
        resp = await client.create(f'test_{realm_name}', str(uuid.uuid4()), scheduleData_external)
        print(resp)
        scheduleData_ad = {"isGlobal": True, "isActive": True,  "name": "DefaultAD Scheduler", "uniqueid": "active_directory_scan", "scantype": 5,
                                 "settings": {"hours": [24]}, "scheduler": "hourly"}
        resp = await client.create(f'test_{realm_name}', str(uuid.uuid4()), scheduleData_ad)
        print(resp)
        scheduleData_lightweight = {"isGlobal": True, "isActive": True,  "name": "DefaultLightWeight Scheduler", "uniqueid": "lightweight_scan", "scantype": 7,
                                 "settings": {"hours": [2]}, "scheduler": "hourly"}
        resp = await client.create(f'test_{realm_name}', str(uuid.uuid4()), scheduleData_lightweight)
        print(resp)

    def update_globalRoles(self, realm_name):
        with httpx.Client(verify=False, timeout=60) as client:
            loginUrl = f'{self.KEYCLOAK_URL}realms/master/protocol/openid-connect/token'
            master_login_resp = client.post(loginUrl, data=self.login_data, timeout=60)
            # print('Keycloak Login response:', master_login_resp.text)
            auth_resp = master_login_resp.json()
            # print(auth_resp)
            headers = {
                "Authorization": f'Bearer {auth_resp["access_token"]}'
            }
            clients_url = f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients'
            client_data = client.get(clients_url, params={"clientId": f"{realm_name}client"}, headers=headers, timeout=60)
            if not isinstance(client_data.json(), list):
                print("Error in getting clients %s" % client_data.json())
                return

            # Checking for mappers
            clidata = client_data.json()
            for clientd in clidata:
                # get the mappers if includes/excludes is not there, create
                client_id = clientd['id']
                getmapurl = f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{client_id}/protocol-mappers/models'
                r = client.get(getmapurl, headers=headers, timeout=60)
                mapresp = r.json()
                tocreate = ['includes', 'excludes']
                for mr in mapresp:
                    mrname = mr['name'].lower()
                    if mrname in tocreate:
                        tocreate.remove(mrname)

                for mapcreate in tocreate:
                    mapurl = f"{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{client_id}/protocol-mappers/models"
                    r = client.post(mapurl, json=self.clientmap[mapcreate], headers=headers, timeout=60)
                    print("Mapping for:%s status:%s response:%s" % (mapcreate, r.status_code, r.text))

            client_data = client_data.json()[0]
            with open(f"{framework.settings.smartrecon_path}globalroles.json") as f:
                roles = json.load(f)
            roles['scopes'] = list({record["name"]: record for record in roles['scopes']}.values())
            roles['policies'] = list({record["name"]: record for record in roles['policies']}.values())
            roles['resources'] = list({record["name"]: record for record in roles['resources']}.values())
            resourceMapping = {}
            for role, desc in {"admin": "Administrator", "readOnly": "Read Only",
                               "itAdmin": "IT Administrator", "norole": "No Role"}.items():
                try:
                    admin_role = client.post(f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/roles',
                                             json={"name": role, "description": desc}, headers=headers, timeout=30)
                except:
                    pass
            for role_name in ["all", "itAdmin", "readOnly", "norole"]:
                resourceMapping[role_name] = {}
                resources = client.get(f"{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{client_data['id']}/authz/resource-server/resource?deep=true&first=0&max=10000&type={role_name}", headers=headers, timeout=60)
                if int(resources.status_code / 100) == 2:
                    for resource in resources.json():
                        if resource["type"] == role_name:
                            resource['scopes'] = [r['name'] for r in resource.get('scopes', [])]
                            resourceMapping[role_name][resource["name"]] = resource
                else:
                    print("Failed to fetch %s status:%s resp:%s" % (role_name, resources.status_code, resources.text))
            for resource in roles["resources"]:
                scopes = [r['name'] for r in resource['scopes']]
                if resource["type"] in resourceMapping and resource["name"] in resourceMapping[resource["type"]]:
                    if len(ListDiff(scopes, resourceMapping[resource["type"]][resource['name']]["scopes"])) != 0:
                        print(f'Difference in role {resourceMapping[resource["type"]][resource["name"]]}')
                        resp = client.delete(f"{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{client_data['id']}/authz/resource-server/resource/{resourceMapping[resource['type']][resource['name']]['_id']}", headers=headers, timeout=30)
                        if int(resp.status_code / 100) != 2:
                            pass
            for policy in roles['policies']:
                if policy['type'] == 'role':
                    policy_data = client.get(f"{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{client_data['id']}/authz/resource-server/policy?first=0&max=20&permission=false&name={policy['name']}", headers=headers, timeout=30)
                    if int(policy_data.status_code / 100) == 2:
                        policy_data = policy_data.json()
                        for temp_record in policy_data:
                            if temp_record["name"] == policy["name"]:
                                del_resp = client.delete(f"{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{client_data['id']}/authz/resource-server/policy/{temp_record['id']}", headers=headers, timeout=30)
                                break
            roles_upload = client.post(
                f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{client_data["id"]}/authz/resource-server/import',
                json=roles, headers=headers, timeout=60)
            if int(roles_upload.status_code / 100) != 2:
                print("Error in uploading global roles status:%s resp:%s" % (roles_upload.status_code,
                                                                                   roles_upload.text))

            # Copying First Broker Login as CCNS
            data = {'newName': 'CCNS'}
            flowcopy = client.post(
                f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/authentication/flows/first%20broker%20login/copy',
                json=data, headers=headers, timeout=60)
            print("Flow Copy Status Code:%s Resp:%s" % (flowcopy.status_code, flowcopy.text))

            # Update the Flow
            flowdata = client.get(
                f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/authentication/flows/CCNS/executions',
                headers=headers, timeout=60
            )
            if int(flowdata.status_code / 100) == 2:
                updateurl = f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/authentication/flows/CCNS/executions'
                changed = self.updateflowdata(flowdata.json())
                for record in changed:
                    client.put(updateurl, json=record, headers=headers, timeout=30)

            # Configuring Default Authentication Parameters
            requiredActions = [
                {"alias": "CONFIGURE_TOTP", "name": "Configure OTP", "enabled": True, "defaultAction": False,
                 "priority": 10, "config": {}},
                {"alias": "terms_and_conditions", "name": "Terms and Conditions", "enabled": True,
                 "defaultAction": True, "priority": 20, "config": {}},
                {"alias": "UPDATE_PASSWORD", "name": "Update Password", "enabled": True, "defaultAction": False,
                 "priority": 30, "config": {}},
                {"alias": "UPDATE_PROFILE", "name": "Update Profile", "enabled": True, "defaultAction": False,
                 "priority": 40, "config": {}},
                {"alias": "VERIFY_EMAIL", "name": "Verify Email", "enabled": True, "defaultAction": False,
                 "priority": 50,
                 "config": {}}]
            for record in requiredActions:
                realm_resp = client.put(
                    self.KEYCLOAK_URL + f"admin/realms/{realm_name}/authentication/required-actions/{record['alias']}",
                    headers=headers, json=record, timeout=60)
                print("Action:%s status:%s resp:%s" % (record['alias'], realm_resp.status_code, realm_resp.text))

            # Creating Default 'No Role'
            for role, desc in {"norole": "No Role"}.items():
                admin_role = client.post(f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/roles',
                                         json={"name": role, "description": desc}, headers=headers, timeout=60)

    def create_client(self, clientid, realm_name="", force=True, role_assign="", clientName='', isApiClient=False):
        with httpx.Client(verify=False, timeout=180) as client:
            # Login to Keycloak, access_token valid for 1 min only
            loginUrl = f'{self.KEYCLOAK_URL}realms/master/protocol/openid-connect/token'
            #print(self.login_data)
            master_login_resp = client.post(loginUrl, data=self.login_data, timeout=180)
            print('Keycloak Login response:', master_login_resp.text)
            auth_resp = master_login_resp.json()
            headers = {
                "Authorization": f'Bearer {auth_resp["access_token"]}'
            }
            if not realm_name:
                realm_name = framework.ctx["tenant"]
            createClientUrl = f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients'  # TODO: <realmName> has to be set based on the partner domain
            client_data = {
                "clientId": clientid,
                "protocol": "openid-connect",
                "serviceAccountsEnabled": True,
                "standardFlowEnabled": False,
                "directAccessGrantsEnabled": True,
                "attributes": {
                    "backchannel.logout.session.required": False
                },
                "publicClient": False
            }
            # Create the client
            createResp = client.post(createClientUrl, json=client_data, headers=headers, timeout=180)
            clients_url = f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients'
            client_data = client.get(clients_url,params={"clientId":clientid},headers=headers, timeout=180)
            client_data = client_data.json()[0]
            client_data.update({"serviceAccountsEnabled": True,
                "standardFlowEnabled": False,
                "directAccessGrantsEnabled": True,
                "authorizationServicesEnabled": True,
                "attributes": {
                    "backchannel.logout.session.required": True
                },
                "publicClient": False})
            if isApiClient:
                client_data['description'] = 'cyberapiclient'
            if clientName:
                client_data["name"] = clientName
            r = client.put(f"{createClientUrl}/{client_data['id']}", json=client_data, headers=headers, timeout=180)
            if int(r.status_code / 100) != 2:
                print("Error in updating client status:%s resp:%s" % (r.status_code, r.text))
            time.sleep(5)
            clients_secret_url = f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{client_data["id"]}/client-secret'
            client_result = client.get(clients_secret_url, params={}, headers=headers, timeout=30)
            result = client_result.json()
            if force == False:
                return True, {"clientid": clientid, "clientsecret": result["value"]}

            role_mapping = {}
            policy_mapping = {}
            for role, desc in {"agent": "Agent Role"}.items():
                agent_role = client.post(f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/roles',
                                         json={"name": role, "description": desc}, headers=headers, timeout=180)
                resp = client.get(f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/roles/{role}', headers=headers, timeout=180)
                if int(resp.status_code /100 ) == 2:
                    resp = resp.json()
                    role_mapping[role] = resp["id"]
                else:
                    print("Error in creating admin role %s %s" % (resp.status_code, resp.text))
            # Deleting default Roles
            r = client.get(
                f"{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{client_data['id']}/authz/resource-server/resource?deep=false&first=0&max=20&name=defa",
                headers=headers, timeout=180)
            if int(r.status_code / 100) == 2:
                for record in r.json():
                    rd = client.delete(
                        f"{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{client_data['id']}/authz/resource-server/resource/{record['_id']}",
                        headers=headers, timeout=30)
                    print("Role delete:%s status:%s resp:%s" % (record['_id'], rd.status_code, rd.text))
            else:
                print("Get Failed status:%s resp:%s" % (r.status_code, r.text))
            r = client.get(
                f"{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{client_data['id']}/authz/resource-server/policy?deep=false&first=0&max=20&name=defa",
                headers=headers, timeout=180)
            if int(r.status_code / 100) == 2:
                for record in r.json():
                    rd = client.delete(
                        f"{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{client_data['id']}/authz/resource-server/policy/{record['id']}",
                        headers=headers, timeout=180)
                    if int(rd.status_code / 100) != 2:
                        print("Error in deleteing default policies %s %s" % (rd.status_code, rd.text))
            # todo:- need to remove policies also
            # if role_assign:
            #     with open("/data/cybercns/cyberbase/globalroles.json") as f:
            #         roles = json.load(f)
            # else:
            #     with open("/data/cybercns/cyberbase/agentroles.json") as f:
            #         roles = json.load(f)

            # reading only global roles
            with open(f"{framework.settings.smartrecon_path}globalroles.json") as f:
                roles = json.load(f)

            roles['scopes'] = list({record["name"]: record for record in roles['scopes']}.values())
            roles['policies'] = list({record["name"]: record for record in roles['policies']}.values())
            roles['resources'] = list({record["name"]: record for record in roles['resources']}.values())
            resourceMapping = {}
            for role_name in ["agent"]:
                resourceMapping[role_name] = {}
                resources = client.get(
                    f"{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{client_data['id']}/authz/resource-server/resource?deep=true&first=0&max=10000&type={role_name}",
                    headers=headers, timeout=180)
                if int(resources.status_code / 100) == 2:
                    for resource in resources.json():
                        if resource["type"] == role_name:
                            resource['scopes'] = [r['name'] for r in resource['scopes']]
                            resourceMapping[role_name][resource["name"]] = resource
            for resource in roles["resources"]:
                scopes = [r['name'] for r in resource['scopes']]
                if resource["type"] in resourceMapping and resource["name"] in resourceMapping[resource["type"]]:
                    if len(ListDiff(scopes, resourceMapping[resource["type"]][resource['name']]["scopes"])) != 0:
                        print(f'Difference in role {resource["name"]} {resourceMapping[resource["type"]][resource["name"]]}')
                        resp = client.delete(
                            f"{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{client_data['id']}/authz/resource-server/resource/{resourceMapping[resource['type']][resource['name']]['_id']}",
                            headers=headers, timeout=180)
                        if int(resp.status_code / 100) != 2:
                            pass
            missingResources = list(set([r['name'] for r in roles['resources']]) - set(list(resourceMapping['agent'].keys())))
            for resource in missingResources:
                resources = client.get(
                    f"{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{client_data['id']}/authz/resource-server/resource?deep=true&first=0&max=10000&name={resource}",
                    headers=headers, timeout=180)
                if int(resources.status_code / 100) == 2:
                    resources = resources.json()
                    for record in resources:
                        if record['name'] == resource:
                            print(f"Found Resource {resource} with wrong configuration, readding")
                            resp = client.delete(
                                f"{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{client_data['id']}/authz/resource-server/resource/{record['_id']}",
                                headers=headers, timeout=30)
                            if int(resp.status_code / 100) != 2:
                                pass
            roles_upload = client.post(
                f"{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{client_data['id']}/authz/resource-server/import",
                json=roles, headers=headers, timeout=180)
            if int(roles_upload.status_code / 100) != 2:
                print("Error in importing roles status:%s resp:%s" % (roles_upload.status_code, roles_upload.text))
            time.sleep(5)
            service_account_resp = client.get(f"{self.KEYCLOAK_URL}admin/realms/{realm_name}/clients/{client_data['id']}/service-account-user", headers=headers, timeout=30)
            if int(service_account_resp.status_code / 100) != 2:
                print("Error in getting service account user %s %s" % (service_account_resp.status_code, service_account_resp.text))
            else:
                composite_roles = client.get(f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/users/{service_account_resp.json()["id"]}/role-mappings/realm/composite',
                                             headers=headers, timeout=30)
                if int(composite_roles.status_code / 100) != 2:
                    print("Error in getting service account user %s %s" % (composite_roles.status_code, composite_roles.text))
                else:
                    del_resp = httpx.request('DELETE',
                        f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/users/{service_account_resp.json()["id"]}/role-mappings/realm',
                        headers=headers, json=composite_roles.json(), verify=False, timeout=30)
                    if int(del_resp.status_code / 100) != 2:
                        print("Error in deleting composite roles %s %s" % (del_resp.status_code, del_resp.text))
                    available_roles = client.get(
                        f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/users/{service_account_resp.json()["id"]}/role-mappings/realm/available', headers=headers, timeout=30)
                    if int(available_roles.status_code / 100) ==2 :
                        roles = {record['name']: record for record in available_roles.json()}
                        role = roles["agent"] if not role_assign else roles[role_assign]
                        create_resp = client.post(f'{self.KEYCLOAK_URL}admin/realms/{realm_name}/users/{service_account_resp.json()["id"]}/role-mappings/realm',
                                                  headers=headers, json=[role], timeout=30)
                        if int(create_resp.status_code / 100) != 2:
                            print("Error in deleting composite roles %s %s" % (create_resp.status_code, create_resp.text))
                    else:
                        print("Error in deleting available_roles %s %s" % (available_roles.status_code, available_roles.text))
            return True, {"clientid": clientid, "clientsecret": result["value"]}

if __name__ == "__main__":
    asyncio.run(KeyClockSecret().configure_msp("recon", 'Tarun.b@urdhvapay.com', "Tharun", "Boddu"))
    kcs = KeyClockSecret()
    # kcs.update_globalRoles('smartrecondemo')
