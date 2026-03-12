import sys
import json
import httpx
import asyncio
import Helpers
import traceback
import pandas as pd
import cybercns_model
import keyCloakManager
import framework.postgresmodel
import framework.queryparams
logger = framework.Logger.getInstance('appbaselineprocessor')
sys.path.append('/data/cybercns/cyberbase')


class AppBaseLineProcessor:
    def __init__(self):
        self.asset_ins = cybercns_model.Asset()
        self.programs_ins = cybercns_model.InstalledProgram()
        self.remediation_ins = cybercns_model.ApplicationBaseline()

    async def getListOfOS(self):
        os_list = []
        ins = framework.postgresmodel.BasePostgresModel()
        client = await ins.client()
        ins.Config.collection_name = 'test'
        query = '{"size":0,"aggs":{"aggs":{"terms":{"field":"os.name.keyword"}}},"query":{"bool":{"must":[{"exists":{"field":"os.name"}}]}}}'
        params = framework.queryparams.QueryParams()
        params.limit = 10000
        params.skip = 0
        resp_data = await client.search(index=await ins.collection_name(), body=query)
        for os_name in resp_data['aggregations']['aggs']["buckets"]:
            if os_name.get("key"):
                os_list.append(os_name.get("key"))
        return os_list

    async def _buildMultiMatchQuery(self, apps):
        multi_match_query = ""
        for value in apps:
            if multi_match_query != "":
                multi_match_query += "and "
            multi_match_query += "full_name: %s*" % value
        return multi_match_query

    async def ruleprocessor(self, ruledata, cyberTenant):
        mandatoryApplications = ruledata['mandatoryApplications']
        deniedApplications = ruledata['deniedApplications']

        ins = framework.postgresmodel.PostgresModel()
        ins.Config.collection_name = 'test'

        params = framework.queryparams.QueryParams()
        params.limit = 10000
        params.skip = 0

        ruleid = ruledata['_id']
        rulename = ruledata['name']
        ruleref = {'id': ruleid, 'name': rulename}
        companyref = ruledata['companyRef']
        companyid = companyref["id"]
        isLightWeightMandatory = ruledata.get('isLightWeightMandatory', False)

        # Get the assets matching os
        query_builder = {"companyRef.id.keyword": companyid}
        if ruledata.get("os_type") and ruledata.get("osname"):
            query_builder["os.platform.keyword"] = ruledata.get("os_type")
        query = Helpers.buildElsQuery(query_builder,
                                      mustExpression=[{"exists": {"field": "os.platform"}},
                                                      {"exists": {"field": "host.ip"}}])
        query['query']['bool']['must'].append(
            {'match_phrase_prefix': {'os.full_name': ruledata.get('osname') + "*"}})
        params.q = json.dumps(query)
        params.fields = ['_id', 'host', 'agentRef']
        asset_resp = await self.asset_ins.get_all(params, cyberTenant)
        if asset_resp["data"]:
            matchedassets = {}
            assetlist = []
            for x in asset_resp['data']:
                matchedassets[x['_id']] = {'assetRef': {"id": x["_id"], "name": x["host"].get("host_name", '')},
                                           'agentRef': x['agentRef']}
                assetlist.append(x["host"].get("host_name", ''))

            # Get existing open remediation's
            remediationdf = pd.DataFrame(columns=['product'])
            query = Helpers.buildElsQuery({"companyRef.id.keyword": companyid,
                                           "ruleRef.id.keyword": ruleid,
                                           "remediation_status": False,
                                           'is_mandatory_application': True},
                                          mustExpression=[{"exists": {"field": "remediation_status"}}])
            params.fields = ['product', 'agentRef', 'assetRef', 'companyRef']
            params.q = json.dumps(query)
            remediation_resp = await self.programs_ins.get_all(params, cyberTenant)
            if remediation_resp["data"]:
                remediationdf = pd.DataFrame(remediation_resp['data'])

            # if lightweight agent is mandatory collecting the installed light weight agents
            cnsapp = "CyberCNS Lightweight Agent"
            lightweighthosts = []
            if isLightWeightMandatory:
                query = Helpers.buildElsQuery({'agent_type': 3,
                                               "companyRef.id.keyword": companyid},
                                              mustExpression=[{"exists": {"field": "agent_type"}}])
                params.fields = ['ip', 'host_name', 'name']
                params.q = json.dumps(query)
                lightweight_resp = await self.programs_ins.get_all(params, cyberTenant)
                if lightweight_resp["data"]:
                    lightweighthosts = pd.DataFrame(lightweight_resp["data"])['host_name'].unique().tolist()
            lightweighthosts = [a.split('.')[0] for a in lightweighthosts]

            remediationprograms = {}
            rmdict = remediationdf.to_dict(orient='records')
            for rm in rmdict:
                product = rm['product']
                asset_id = rm['assetRef']['id']
                if asset_id not in remediationprograms:
                    remediationprograms[asset_id] = {}
                remediationprograms[asset_id][product] = rm['_id']

            # checking mandatory
            for assetid, assetinfo in matchedassets.items():
                assethostname = assetinfo['assetRef']['name']
                plainassethostname = assetinfo['assetRef']['name'].split('.')[0]
                assetprograms = remediationprograms.get(assetid, {})
                multi_match_query = await self._buildMultiMatchQuery(mandatoryApplications)
                query = Helpers.buildElsQuery({"companyRef.id.keyword": companyid,
                                               "assetRef.id.keyword": assetid},
                                              mustExpression=[{"exists": {"field": "version"}},
                                                              {"multi_match": {
                                                                  "query": multi_match_query,
                                                                  "fields": ["full_name"]}}])
                params.fields = []
                params.q = json.dumps(query)
                prog_resp = await self.programs_ins.get_all(params, cyberTenant)
                if prog_resp["data"]:
                    for app in mandatoryApplications:
                        appfound = False
                        for program in prog_resp["data"]:
                            if app in program["full_name"]:
                                appfound = True
                                break
                        if (not appfound) and (app not in assetprograms):
                            logger.info("Mandatory program not installed:%s asset:%s" % (app,
                                                                                         assetinfo['assetRef']['name']))
                            await cybercns_model.Remediation(**{"product": app,
                                                                "is_mandatory_application": True,
                                                                "url": "", "fix": "",
                                                                "remediation_status": False,
                                                                'ruleRef': ruleref,
                                                                "companyRef": companyref,
                                                                "assetRef": assetinfo["assetRef"],
                                                                "agentRef": assetinfo["agentRef"]}).create(cyberTenant)
                        if appfound and (app in assetprograms):
                            logger.info("Mandatory program installed closing:%s asset:%s" % (app,
                                                                                             assetinfo['assetRef']['name']))
                            await cybercns_model.Remediation(**{"_id": assetprograms[app]['_id'],
                                                                "remediation_status": True}).update(cyberTenant)
                else:
                    # None of mandatory applications are installed
                    for app in mandatoryApplications:
                        if app not in assetprograms:
                            logger.info("(ALL)Mandatory program not installed:%s asset:%s" % (app,
                                                                                         assetinfo['assetRef']['name']))
                            await cybercns_model.Remediation(**{"product": app,
                                                                "is_mandatory_application": True,
                                                                "url": "", "fix": "",
                                                                "remediation_status": False,
                                                                'ruleRef': ruleref,
                                                                "companyRef": companyref,
                                                                "assetRef": assetinfo["assetRef"],
                                                                "agentRef": assetinfo["agentRef"]}).create(cyberTenant)

                # if any previously created remediation is removed from mandatory close it
                for apk, apid in assetprograms.items():
                    if apk not in mandatoryApplications and apk != cnsapp:
                        logger.info("Mandatory not required anymore:%s asset:%s" % (apk,
                                                                                    assetinfo['assetRef']['name']))
                        await cybercns_model.Remediation(**{"_id": apid,
                                                            "remediation_closer_reason": 'Not Required',
                                                            "remediation_status": True}).update(cyberTenant)

                # checking if the light weight agent is mandatory and is installed
                if isLightWeightMandatory:
                    if (cnsapp not in assetprograms) and (plainassethostname not in lightweighthosts):
                        await cybercns_model.Remediation(**{"product": cnsapp,
                                                            "is_mandatory_application": True,
                                                            "url": "", "fix": "",
                                                            "remediation_status": False,
                                                            'ruleRef': ruleref,
                                                            "companyRef": companyref,
                                                            "assetRef": assetinfo["assetRef"],
                                                            "agentRef": assetinfo["agentRef"]}).create(cyberTenant)
                    elif (cnsapp in assetprograms) and (plainassethostname in lightweighthosts):
                        await cybercns_model.Remediation(**{"_id": assetprograms[cnsapp],
                                                            "remediation_closer_reason": 'Installed',
                                                            "remediation_status": True}).update(cyberTenant)
                else:
                    if cnsapp in assetprograms:
                        await cybercns_model.Remediation(**{"_id": assetprograms[cnsapp],
                                                            "remediation_closer_reason": 'Not Required',
                                                            "remediation_status": True}).update(cyberTenant)

            # checking denied
            denieddf = pd.DataFrame(columns=['full_name'])
            query = Helpers.buildElsQuery(must={"companyRef.id.keyword": companyid},
                                          mustExpression=[{"exists": {"field": "version"}}])
            query['query']['bool']['must'].append({'terms': {'assetRef.id.keyword': list(matchedassets.keys())}})
            query['query']['bool']['must'].append({'terms': {'name.keyword': deniedApplications}})
            params.fields = ['agentRef', 'assetRef', 'companyRef', 'full_name', 'version', 'path']
            params.q = json.dumps(query)
            prog_resp = await self.programs_ins.get_all(params, cyberTenant)
            if prog_resp["data"]:
                denieddf = pd.DataFrame(prog_resp["data"])
                del denieddf['_id']

            # get existing denied remediation's
            remediationdf = pd.DataFrame(columns=['product'])
            query = Helpers.buildElsQuery({"companyRef.id.keyword": companyid,
                                           "ruleRef.id.keyword": ruleid,
                                           "remediation_status": False,
                                           'is_denied_application': True},
                                          mustExpression=[{"exists": {"field": "remediation_status"}}])
            params.fields = ['product']
            params.q = json.dumps(query)
            remediation_resp = await self.programs_ins.get_all(params, cyberTenant)
            if remediation_resp["data"]:
                remediationdf = pd.DataFrame(remediation_resp['data'])

            # merging
            mergedf = remediationdf.merge(denieddf, left_on='product', right_on='full_name', how='outer', indicator=True)

            # denied create
            deniedcreate = mergedf[mergedf['_merge'] == 'right_only']
            dclist = deniedcreate.to_dict(orient='records')
            for dc in dclist:
                assetname = dc.get('assetRef', {}).get('name', '')
                logger.info("Denied program installed:%s asset:%s" % (dc.get("full_name", ''), assetname))
                await cybercns_model.Remediation(
                    **{"product": dc.get("full_name", ''), "is_denied_application": True, "url": "", "fix": "",
                       "remediation_status": False, "companyRef": companyref,
                       "evidence": {'productRef': dc.get('_id', ''), 'version': dc.get('version', ''),
                                    'path': dc.get('path', '')},
                       'ruleRef': ruleref,
                       "assetRef": dc["assetRef"], "agentRef": dc["agentRef"]}).create(cyberTenant)

            # denied close
            deniedclose = mergedf[mergedf['_merge'] == 'left_only']
            dclist = deniedclose.to_dict(orient='records')
            for dc in dclist:
                await cybercns_model.Remediation(**{"_id": dc['_id'], "remediation_status": True}).update(cyberTenant)
        else:
            logger.info("No matching assets found")

    async def processor(self, domain):
        cyberTenant = domain
        ins = framework.postgresmodel.PostgresModel()
        ins.Config.collection_name = 'test'
        baseline_ins = cybercns_model.ApplicationBaseline()

        params = framework.queryparams.QueryParams()
        params.limit = 10000
        params.skip = 0
        query = Helpers.buildElsQuery(shouldExpression=[{"exists": {"field": "mandatoryApplications"}},
                                                        {"exists": {"field": "deniedApplications"}}])
        params.q = json.dumps(query)
        try:
            base_line_resp = await baseline_ins.get_all(params, cyberTenant)
            if base_line_resp['data']:
                for baselinerule in base_line_resp['data']:
                    if baselinerule.get('companyRef'):
                        companyname = baselinerule['companyRef'].get('name', '')
                        logger.info("Processing for %s rule:%s" % (companyname, baselinerule['name']))
                        await self.ruleprocessor(baselinerule, domain)
                    else:
                        # TODO Global Level
                        pass
        except Exception as e:
            logger.info("Rule processing exception:%s" % e)
            print(traceback.print_exc())

    async def get_processor(self, realm=''):
        if realm:
            await self.processor(realm)
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
                await self.processor(realm_name)

    async def rule_evaluator(self, ruleid, domain):
        ruledata = await self.remediation_ins.get(ruleid, domain)
        ruledata = ruledata.dict()
        try:
            ruledata['_id'] = ruledata['id']
            logger.info("Processing single rule:%s" % ruledata['name'])
            await self.ruleprocessor(ruledata, domain)
            return "Processed"
        except Exception as e:
            logger.info("Exception in processing single rule:%s" % e)
            return "Failed to Process"

    async def company_rule_processor(self, companyid, domain):
        # get rules associated for this company
        baseline_ins = cybercns_model.ApplicationBaseline()
        params = framework.queryparams.QueryParams()
        params.limit = 10000
        params.skip = 0
        query = Helpers.buildElsQuery(shouldExpression=[{"exists": {"field": "mandatoryApplications"}},
                                                        {"exists": {"field": "deniedApplications"}}],
                                      must={'companyRef.id.keyword': companyid})
        params.q = json.dumps(query)
        try:
            base_line_resp = await baseline_ins.get_all(params, domain)
            for ruledata in base_line_resp['data']:
                await self.ruleprocessor(ruledata, domain)
        except Exception as e:
            logger.info("Exception in processing base rule for comapny:%s %s" % (companyid, e))

    async def update_remediations(self, ruleid, domain):
        ruledata = await self.remediation_ins.get(ruleid)
        ruledata = ruledata.dict()
        try:
            logger.info("Processing rule deletion:%s" % ruledata['name'])
            ins = framework.postgresmodel.PostgresModel()
            ins.Config.collection_name = 'test'
            params = framework.queryparams.QueryParams()
            params.limit = 10000
            params.skip = 0
            query = Helpers.buildElsQuery(mustExpression=[{"match": {"ruleRef.id.keyword": ruleid}},
                                                          {"exists": {"field": "remediation_status"}}])
            query['script'] = {
                "inline": "ctx._source.remediation_status=true;ctx._source.remediation_closer_reason='Remediated as the rule is deleted'",
                "lang": "painless"
            }
            params.q = json.dumps(query)
            client = await ins.client()
            indexName = f"test_{domain}"
            remediation_resp = await client.update_by_query(index=indexName, body=query)
            logger.info(remediation_resp)
            return "Deleted"
        except Exception as e:
            logger.info("Exception in deleting the remediation single rule:%s" % e)
            return "Failed to Process"


if __name__ == "__main__":
    ap = AppBaseLineProcessor()
    asyncio.run(ap.get_processor())

