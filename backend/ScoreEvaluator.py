import sys
import json
import httpx
import socket
import Helpers
import asyncio
import requests
import requests.auth
import cybercns_model
import keyCloakManager
import framework.queryparams
import framework.postgresmodel
from jinja2 import Template
logger = framework.Logger.getInstance('scoreevaluator')


class ScoreEvaluator:
    def __init__(self, type, id, domain=None):
        self.rules = {}
        self.cyberTenant = domain
        self.id=id
        self.target = ""
        if type == "asset":
            self.target = "meta/assettemplate.json"
        elif type == "company":
            self.target = "meta/companytemplate.json"
        with open(self.target, "r") as f:
            self.rules = json.load(f)
        self.ins = framework.postgresmodel.PostgresModel()
        self.ins.Config.collection_name = 'test'

    async def getConditions(self):
        return self.rules

    async def updateRule(self, id, value):
        categoryindex = 0
        for category in self.rules:
            ruleindex = 0
            for r in category["controls"]:
                if r["id"] == id:
                    # print("found", r)
                    r["params"]["normal"] = value
                    self.rules[categoryindex]["controls"][ruleindex] = r
                ruleindex += 1
        with open(self.target, "w") as f:
            json.dump(self.rules, f)

    async def securityReprotCard(self,data,params):
        finalgrade=0
        for report in data.get("data",[]):
            for grade in report.get("report_card",[]):
                if grade.get("name","")==params and 0<grade.get("grade","")<5:
                    finalgrade+=1
        return {"id":finalgrade}

    async def _getmarks(self, condition):
        query = json.loads(condition["query"].replace("{{id}}",self.id))

        if condition.get("externalCall",{}):
            query["size"] = 500
            params = framework.queryparams.QueryParams()
            params.limit = 10000
            params.q = json.dumps(query)
            data=await self.ins.get_all(params, self.cyberTenant)
            data= await eval("self.%s"%condition.get("externalCall",{}).get("func",""))(data,condition.get("externalCall",{}).get("params",""))
        else:
            client = await self.ins.client()
            data = await client.search(index=await self.ins.collection_name(domain=self.cyberTenant), body=query)
        # print(condition,data)
        t = Template(condition["condition"])
        expression = t.render(condition=condition, data=data)
        retval = eval(expression)
        if not retval:
            return condition["params"]["risk"]
        else:
            return 0

    async def getScore(self):
        totalmarks = 0
        for category in self.rules:
            for rule in category["controls"]:
                totalmarks += await self._getmarks(rule)
        return totalmarks


class CompanyScoreStats:
    async def getScoreTemplates(self):
        templates = {"asset":"meta/assettemplate.json","company":"meta/companytemplate.json"}
        rules = {}
        for key,val in templates.items():
            with open(val, "r") as f:
                rules[key] = json.load(f)
                #remove query param
                for category in rules[key]:
                    for r in category["controls"]:
                        del r["query"]
        return rules
    
    async def updateScoreTemplates(self, type ,rules=[]):
        #rules =[{"id": "AR-001","normal":5,"risk":5}]
        template = "meta/assettemplate.json"
        if type == "asset":
            template = "meta/assettemplate.json"
        elif type == "company":
            template = "meta/companytemplate.json"
        current_rules = {}
        with open(template, "r") as f:
            current_rules = json.load(f)
        for rule in rules:
            categoryindex = 0
            for category in current_rules:
                ruleindex = 0
                for r in category["controls"]:
                    if r["id"] == rule.id:
                        # print("found", r)
                        r["params"]["normal"] = rule.normal
                        r["params"]["risk"] = rule.risk
                        current_rules[categoryindex]["controls"][ruleindex] = r
                        break
                    ruleindex += 1
                categoryindex += 1    
        with open(template, "w") as f:
            json.dump(current_rules, f)
        await self.get_processor()
        return current_rules

    async def get_processor(self, realm=''):
        if realm:
            await self.getCompanyStats(realm)
            return
        ins = keyCloakManager.KeyClockSecret()
        with httpx.Client(verify=False) as client:
            loginUrl = f'{ins.KEYCLOAK_URL}realms/master/protocol/openid-connect/token'
            master_login_resp = client.post(loginUrl, data=ins.login_data)
            auth_resp = master_login_resp.json()
            headers = {"Authorization": f'Bearer {auth_resp["access_token"]}'}
            realm_url = f'{ins.KEYCLOAK_URL}admin/realms'
            realm_resp = client.get(realm_url, headers=headers)
            if int(realm_resp.status_code / 100) != 2:
                logger.info("Error in getting realm details %s " % realm_resp.text)
                sys.exit(0)
            realms = realm_resp.json()
        for realm in realms:
            realm_name = realm["realm"]
            if realm_name in ["master"]:
                continue
            else:
                logger.info("Processing Domain:%s" % realm_name)
                await self.getCompanyStats(realm_name)

    async def getCompanyStats(self, domain):
        cyberTenant = domain
        company_timeseries_stats_ins = cybercns_model.CompanyStatsTimeseries()
        company_stats_ins = cybercns_model.CompanyStats()
        ins = framework.postgresmodel.BasePostgresModel()
        client = await ins.client()
        ins.Config.collection_name = 'test'
        query = Helpers.buildElsQuery(mustExpression=[{"exists": {"field": "description"}}],
                                      mustNotExpression=[{"exists": {"field": "companyRef"}}])
        params = framework.queryparams.QueryParams()
        params.limit = 10000
        params.skip = 0
        params.q = json.dumps(query)
        resp = await ins.get_all(params, cyberTenant)
        if resp['data']:
            for company in resp['data']:
                company_stats = {}
                # find secure score and insert into db
                logger.info("company:%s" % company["name"])
                company_stats['companyRef'] = {"id": company["_id"], "name": company["name"]}
                company_stats['company_score'] = await ScoreEvaluator("company", company["_id"],domain).getScore()
                # For Asset Count
                query_list = {
                    'asset_count': '{"size":0,"aggs":{"aggs":{"filters":{"filters":{"aggs":{"bool":{"must":[{"exists":{"field":"assetRef.id"}}]}}}}}},"query":{"bool":{"must":[{"match":{"companyRef.id.keyword":"{{id}}"}}]}}}',
                    'critical_unique_vuls_count': '{"size":0,"aggs":{"aggs":{"filters":{"filters":{"aggs":{"bool":{"must":[{"exists":{"field":"vul_id"}},{"match":{"severity.keyword":"Critical"}},{"match":{"companyRef.id.keyword":"{{id}}"}}]}}}}}},"query":{"bool":{"must":[{"exists":{"field":"score"}}]}}}',
                    'high_unique_vuls_count': '{"size":0,"aggs":{"aggs":{"filters":{"filters":{"aggs":{"bool":{"must":[{"exists":{"field":"vul_id"}},{"match":{"severity.keyword":"High"}},{"match":{"companyRef.id.keyword":"{{id}}"}}]}}}}}},"query":{"bool":{"must":[{"exists":{"field":"score"}}]}}}'
                    }
                for key, query in query_list.items():
                    query = query.replace("{{id}}", company["_id"])
                    resp_data = await client.search(index=await ins.collection_name(domain=cyberTenant), body=query)
                    company_stats[key] = resp_data['aggregations']['aggs']['buckets']['aggs']['doc_count']
                    company_stats['companyRef'] = {"id": company["_id"], "name": company["name"]}

                # check for score_card entry
                query = Helpers.buildElsQuery({"companyRef.id.keyword": company["_id"]},
                                              mustExpression={"exists": {"field": "company_score"}})
                params.q = json.dumps(query)
                response = await company_stats_ins.get_all(params, cyberTenant)
                await cybercns_model.CompanyStatsTimeseries(**company_stats).create(cyberTenant)
                if response.get('count'):
                    company_stats['_id'] = response['data'][0]['_id']
                    logger.info("Update:: %s" % company_stats)
                    await cybercns_model.CompanyStats(**company_stats).update(cyberTenant)
                else:
                    logger.info("Create:: %s" % company_stats)
                    await cybercns_model.CompanyStats(**company_stats).create(cyberTenant)


def getCookie(realm_name, clientid, role):
    keycloak_ins = keyCloakManager.KeyClockSecret()
    status, resp = keycloak_ins.create_client(clientid, realm_name, True, role)
    authKey = requests.auth._basic_auth_str(resp['clientid'], resp['clientsecret'])
    with httpx.Client(verify=False) as client:
        resp = client.get(f"https://{realm_name}.mycybercns.com/api/login", headers={"Authorization": authKey},
                          allow_redirects=False)
        if int(resp.status_code/100) not in [2, 3]:
            return False, resp.text
        cookie = resp.cookies.get('framework')
        return True, cookie


if __name__ == "__main__":
    ap = CompanyScoreStats()
    asyncio.run(ap.get_processor())

    '''ins = keyCloakManager.KeyClockSecret()
    with httpx.Client(verify=False) as client:
        loginUrl = f'{ins.KEYCLOAK_URL}realms/master/protocol/openid-connect/token'
        master_login_resp = client.post(loginUrl, data=ins.login_data)
        # print('Keycloak Login response:', master_login_resp.text)
        auth_resp = master_login_resp.json()
        # print(auth_resp)
        headers = {
            "Authorization": f'Bearer {auth_resp["access_token"]}'
        }
        realm_url = f'{ins.KEYCLOAK_URL}admin/realms'
        realm_resp = client.get(realm_url, headers=headers)
        if int(realm_resp.status_code / 100) != 2:
            logger.info("Error in getting realm details %s " % realm_resp.text)
            sys.exit(0)
        realms = realm_resp.json()
    for realm in realms:
        realm_name = realm["id"]
        if realm_name in ["master"]:
            continue
        try:
            externalIp = requests.get('https://checkip.amazonaws.com').text.strip()
            if socket.gethostbyname(f'{realm_name}.mycybercns.com') not in ["127.0.0.1", "localhost", externalIp]:
                continue
        except Exception as e:
            logger.info("Exception %s" % e)
            continue
        status, cookie = getCookie(realm_name, "scheduleclient", "")
        if status and cookie:
            resp = requests.post(f'https://{realm_name}.mycybercns.com/api/company/dummy/updateCompanyScore',
                                 cookies={'framework': cookie}, json={})
            if int(resp.status_code / 100) != 2:
                logger.info("Error in company syncing statusCode %s %s" % (resp.status_code, resp.text))
            requests.get(f'https://{realm_name}.mycybercns.com/api/logout', cookies={'framework': cookie})'''

