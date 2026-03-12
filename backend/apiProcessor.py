import framework.queryparams
import framework.postgresmodel
import framework.redispool
import os
import git
import pytz
import json
import glob
import redis
import httpx
import base64
import urllib
import string
import random
import fastapi
import asyncio
import Helpers
import requests
import datetime
import pandas as pd
import assetProcessor
import keycloakusermgmt
import cyberPrevilagedManager
from docx.shared import Mm
from docxtpl import DocxTemplate, InlineImage

logger = framework.Logger.getInstance('apiprocessor')


class VulnersProcessor():
    async def getVulnerabilityOsView(self, companyId=None):
        acls = keycloakusermgmt.GetAcls()
        filterkey = 'companyRef.id.keyword'
        includes = acls['includes']
        excludes = acls['excludes']
        if companyId and includes:
            if companyId not in includes:
                return False, "Not Allowed"
        if companyId in excludes:
            return False, "Not Allowed"
        ins = framework.postgresmodel.PostgresModel()
        ins.Config.collection_name = 'test'
        must_query = {}
        must_not = {"os.full_name.keyword": ""}
        if companyId:
            must_query.update({"companyRef.id.keyword": companyId})
        query = Helpers.buildElsQuery(must_query, mustExpression=[{"exists": {"field": "lastvul_scannedtime"}}],
                                      must_not=must_not)
        query["aggs"] = {"platform": {"terms": {"field": "os.full_name.keyword", "order": {"_count": "desc"}, "size": 100},
                                      "aggs": {"assetId": {
                                          "terms": {"field": "_id", "order": {"_count": "desc"}, "size": 3000}},
                                          "risk_score": {"avg": {"field": "vul_stats.risk_score"}}}}}
        query["size"] = 0
        if includes:
            inc = {"terms": {filterkey: includes}}
            if "must" in query["query"]["bool"]:
                query["query"]["bool"]["must"] = []
            query["query"]["bool"]["must"].append(inc)
        if excludes:
            exc = {"terms": {filterkey: excludes}}
            if "must_not" not in query["query"]["bool"]:
                query["query"]["bool"]["must_not"] = []
            query["query"]["bool"]["must_not"].append(exc)
        client = await ins.client()
        response = await client.search(index=await ins.collection_name(), body=query)
        aggregationData = []
        for record in response['aggregations'].get('platform', {}).get('buckets', []):
            assets, os_aggregationData = [], {}
            for bucket in record.get('assetId', {}).get('buckets', []):
                assets.append(bucket["key"])
            if len(assets) > 0 and record['key']:
                os_aggregationData["os"] = record['key']
                if record.get('risk_score', {}).get('value', 0):
                    os_aggregationData['risk_score'] = round(record['risk_score']['value'])
                else:
                    os_aggregationData['risk_score'] = 0

            query = Helpers.buildElsQuery(mustExpression=[{"terms": {"assetRef.id.keyword": assets}},
                                                          {"exists": {"field": "assetRef.id"}},
                                                          {"exists": {"field": "score.base_score"}},
                                                          {"range": {"score.base_score": {"gt": 0}}}])
            query["aggs"] = {
                "vulInfo": {"terms": {"field": "severity.keyword", "order": {"_count": "desc"}, "size": 10},
                            "aggs": {"vuls": {
                                "terms": {"field": "vul_id.keyword", "order": {"_count": "desc"}, "size": 5000}}}}}
            query["size"] = 0
            client = await ins.client()
            vul_response = await client.search(index=await ins.collection_name(), body=query)
            for vul in vul_response['aggregations'].get('vulInfo', {}).get('buckets', []):
                if vul['key'] not in ['Critical', 'High', 'Medium', 'Low']:
                    continue
                os_aggregationData[vul['key']] = len(vul.get('vuls', {}).get('buckets', []))
            for key in ['Critical', 'High', 'Medium', 'Low']:
                if key not in os_aggregationData:
                    os_aggregationData[key] = 0
            aggregationData.append(os_aggregationData)
        return True, aggregationData

    async def getVulnerabilityProductView(self, companyId=None, os=None, severity="Critical"):
        acls = keycloakusermgmt.GetAcls()
        filterkey = 'companyRef.id.keyword'
        includes = acls['includes']
        excludes = acls['excludes']
        if companyId and includes:
            if companyId not in includes:
                return False, "Not Allowed"
        if companyId in excludes:
            return False, "Not Allowed"
        ins = framework.postgresmodel.PostgresModel()
        ins.Config.collection_name = 'test'
        must_query = {}
        if companyId:
            must_query.update({"companyRef.id.keyword": companyId})
        if os:
            must_query.update({"os.full_name.keyword": os})
        else:
            return False, "Please provide Os,Severity details."
        query = Helpers.buildElsQuery(must_query, mustExpression=[{"exists": {"field": "lastvul_scannedtime"}}])
        query["aggs"] = {"platform": {"terms": {"field": "os.full_name.keyword", "order": {"_count": "desc"}, "size": 100},
                                      "aggs": {"assetId": {
                                          "terms": {"field": "_id", "order": {"_count": "desc"}, "size": 5000}}}}}
        query["size"] = 0
        if includes:
            inc = {"terms": {filterkey: includes}}
            if "must" in query["query"]["bool"]:
                query["query"]["bool"]["must"] = []
            query["query"]["bool"]["must"].append(inc)
        if excludes:
            exc = {"terms": {filterkey: excludes}}
            if "must_not" not in query["query"]["bool"]:
                query["query"]["bool"]["must_not"] = []
            query["query"]["bool"]["must_not"].append(exc)
        client = await ins.client()
        response = await client.search(index=await ins.collection_name(), body=query)
        aggregationData = []
        for record in response['aggregations'].get('platform', {}).get('buckets', []):
            assets, product_aggregationData = [], {}
            for bucket in record.get('assetId', {}).get('buckets', []):
                assets.append(bucket["key"])
            query = Helpers.buildElsQuery({'severity.keyword': severity},
                                          mustExpression=[{"terms": {"assetRef.id.keyword": assets}},
                                                          {"exists": {"field": "assetRef.id"}},
                                                          {"exists": {"field": "score.base_score"}},
                                                          {"range": {"score.base_score": {"gt": 0}}}])
            query["aggs"] = {
                "productName": {"terms": {"field": "product.keyword", "order": {"_count": "desc"}, "size": 100},
                                "aggs": {"vuls": {
                                    "terms": {"field": "vul_id.keyword", "order": {"_count": "desc"}, "size": 3000}}}}}

            query["size"] = 0
            client = await ins.client()
            vul_response = await client.search(index=await ins.collection_name(), body=query)
            for vul in vul_response['aggregations'].get('productName', {}).get('buckets', []):
                product_aggregationData[vul['key']] = len(vul.get('vuls', {}).get('buckets', []))
            aggregationData.append(product_aggregationData)
        return True, aggregationData

    async def getVulnerabilityView(self, companyId=None, os=None, severity=None, productName=None):
        if not productName or not os or not severity:
            return False, "Missing input arguments"
        acls = keycloakusermgmt.GetAcls()
        filterkey = 'companyRef.id.keyword'
        includes = acls['includes']
        excludes = acls['excludes']
        if companyId and includes:
            if companyId not in includes:
                return False, "Not Allowed"
        if companyId in excludes:
            return False, "Not Allowed"
        ins = framework.postgresmodel.PostgresModel()
        ins.Config.collection_name = 'test'
        must_query = {}
        if companyId:
            must_query.update({"companyRef.id.keyword": companyId})
        if os:
            must_query.update({"os.full_name.keyword": os})
        else:
            return False, "Please provide Os,Severity,productName details."
        query = Helpers.buildElsQuery(must_query, mustExpression=[{"exists": {"field": "lastvul_scannedtime"}}])
        query["aggs"] = {"platform": {
            "terms": {"field": "os.full_name.keyword", "order": {"_count": "desc"}, "size": 100 if not os else 1},
            "aggs": {"assetId": {
                "terms": {"field": "_id", "order": {"_count": "desc"}, "size": 5000}}}}}
        query["size"] = 0
        if includes:
            inc = {"terms": {filterkey: includes}}
            if "must" in query["query"]["bool"]:
                query["query"]["bool"]["must"] = []
            query["query"]["bool"]["must"].append(inc)
        if excludes:
            exc = {"terms": {filterkey: excludes}}
            if "must_not" not in query["query"]["bool"]:
                query["query"]["bool"]["must_not"] = []
            query["query"]["bool"]["must_not"].append(exc)
        cve_list = {}
        client = await ins.client()
        response = await client.search(index=await ins.collection_name(), body=query)
        for record in response['aggregations'].get('platform', {}).get('buckets', []):
            assets = []
            for bucket in record.get('assetId', {}).get('buckets', []):
                assets.append(bucket["key"])
            query = Helpers.buildElsQuery(must={"severity.keyword": severity, "product.keyword": productName},
                                          mustExpression=[{"terms": {"assetRef.id.keyword": assets}},
                                                          {"exists": {"field": "assetRef.id"}},
                                                          {"exists": {"field": "score.base_score"}},
                                                          {"range": {"score.base_score": {"gt": 0}}}])
            query["aggs"] = {
                "vul_id": {"terms": {"field": "vul_id.keyword", "order": {"_count": "desc"}, "size": 3000},
                           "aggs": {
                               "vul_source": {
                                   "top_hits": {"_source": {"include": ["product", "title", "score", "severity"]},
                                                "size": 1}},
                               "companyRef": {
                                   "terms": {"field": "companyRef.id.keyword", "order": {"_count": "desc"},
                                             "size": 100}, "aggs": {
                                       "companyRef": {
                                           "top_hits": {"_source": {"include": ["companyRef"]}, "size": 1}},
                                       "assetRef": {
                                           "terms": {"field": "assetRef.id.keyword", "order": {"_count": "desc"},
                                                     "size": 500},
                                           'aggs': {"assetRef": {"top_hits": {
                                               "_source": {"include": ["assetRef"]},
                                               "size": 1}}}}
                                   }}}}}
            query["size"] = 0
            client = await ins.client()
            vul_response = await client.search(index=await ins.collection_name(), body=query, request_timeout=30)
            for vul in vul_response['aggregations'].get('vul_id', {}).get('buckets', []):
                vul_id = vul["key"]
                if not cve_list.get(vul_id):
                    cve_list[vul_id] = {"vul_id": vul_id, "data": {}}
                    cve_list[vul_id].update(vul['vul_source']["hits"]['hits'][0]['_source'])
                    cve_list[vul_id]["product"] = cve_list[vul_id]["product"][0]
                    if not cve_list[vul_id].get('title'):
                        cve_list[vul_id]['title'] = cve_list[vul_id]["product"]
                for company in vul['companyRef']['buckets']:
                    if company['key'] not in cve_list[vul_id]['data']:
                        cve_list[vul_id]['data'][company['key']] = {
                            **company['companyRef']['hits']['hits'][0]['_source'], **{"assets": []}}
                    for asset in company['assetRef']['buckets']:
                        cve_list[vul_id]['data'][company['key']]['assets'].append(
                            asset['assetRef']['hits']['hits'][0]['_source']['assetRef'])
            for _, details in cve_list.items():
                details['data'] = list(details['data'].values())
        return True, list(cve_list.values())


class RemediationProcessor():
    def getReportCardTemplate(self):
        return {"antiVirus": {
            5: 'Anti-virus is installed and update to date',
            4: 'Anti-virus is installed but not up to date',
            1: 'Anti-virus is not installed',
            -1: 'Not Applicable'
        },
            "antiSpyware": {
                5: 'Anti-spyware is installed and update to date',
                4: 'Anti-spyware is installed but not up to date',
                1: 'Anti-spyware is not installed',
                -1: 'Not Applicable'
            },
            "localFirewall": {
                5: 'Local firewall is enabled for both public and private networks',
                4: 'Local firewall is not enabled for private networks',
                3: 'Local firewall is not enabled',
                1: 'Local firewall is not enabled',
                -1: 'Not Applicable'
            },
            "missingCriticalPatches": {
                5: 'No missing critical patches',
                4: 'Fewer than 3 missing critical patches',
                3: 'Less than 5 missing critical patches',
                1: '5 or more missing critical patches',
                -1: 'Not Applicable'
            },
            "insecureListeningPorts": {
                5: 'There are no insecure listening ports',
                3: 'One insecure listening port detected',
                1: 'More than one insecure listening port detected',
                -1: 'Not Applicable'
            },
            "failedLogin": {
                5: 'No failed interactive logins in the past 7 days',
                4: '7 or fewer failed interactive logins in the past 7 days',
                3: '14 or fewer failed interactive logins in the past 7 days',
                1: '15 or more failed interactive logins in the past 7 days',
                -1: 'Not Applicable'
            },
            "failedLogins": {
                5: 'No failed interactive logins in the past 7 days',
                4: '7 or fewer failed interactive logins in the past 7 days',
                3: '14 or fewer failed interactive logins in the past 7 days',
                1: '15 or more failed interactive logins in the past 7 days',
                -1: 'Not Applicable'
            },
            "networkVulnerabilities": {
                5: 'No network vulnerabilities',
                4: 'Low network vulnerabilities found (CVSS < 4.0)',
                3: 'Medium network vulnerability found (CVSS >= 4.0)',
                1: 'Critical network vulnerability found (CVSS >= 9.0)',
                -1: 'Not Applicable'
            },
            "screenLockWithTimeout": {
                5: 'Screen lock enabled with reasonable timeout (15 minutes)',
                4: 'Screen lock enabled with high timeout (30 minutes)',
                3: 'Screen lock enabled with unreasonable timeout (more than 30 minutes)',
                1: 'Screen lock not enabled',
                -1: 'Not Applicable'
            },
            "screenLockTimeout": {
                5: 'Screen lock enabled with reasonable timeout (15 minutes)',
                4: 'Screen lock enabled with high timeout (30 minutes)',
                3: 'Screen lock enabled with unreasonable timeout (more than 30 minutes)',
                1: 'Screen lock not enabled',
                -1: 'Not Applicable'
            },
            "systemAging": {
                5: 'All computers are less than 2 years old',
                4: 'Some computers between 3 and 4 years old',
                3: 'Some computers between 4 and 7 years old',
                1: 'Some computers over 8 years old',
                -1: 'Not Applicable'
            },
            "supportedOS": {
                5: 'All computers have supported Operating Systems',
                4: 'Some Operating Systems are in extended supported',
                3: 'Some Operating Systems are within 1 year of end of life',
                1: 'Some unsupported Operating Systems',
                -1: 'Not Applicable'
            },
            "llmnr": {
                2: 'LLMNR not Allowed',
                5: 'LLMNR Disabled',
                1: 'LLMNR Enabled',
            },
            "nbtns": {
                2: 'NBT-NS not Allowed',
                5: 'NBT-NS Disabled',
                1: 'NBT-NS Enabled',
            },
            "ntmlv1": {
                2: 'NTMlv1 not Allowed',
                5: 'NTMlv1 Disabled',
                1: 'NTMlv1 Enabled',
            },
            "smbv1Server": {
                2: 'SMBv1 Server not Allowed',
                5: 'SMBv1 Server Disabled',
                1: 'SMBv1 Server Enabled',
            },
            "smbv1Client": {
                2: 'SMBv1 Client not Allowed',
                5: 'SMBv1 Client Enabled',
                1: 'SMBv1 Client Disabled',
            },
            "smbSigning": {
                2: 'SMB Signing not Allowed',
                5: 'SMB Signing Disabled',
                1: 'SMB Signing Enabled',
            }
        }

    async def updateRemediationPlan(self, remsupress_ins, rem_ins, data):
        old_data = None
        suppression_level = 'company'
        if 'assetRef' in data and data['assetRef'] and data['assetRef'].get("id"):
            suppression_level = "asset"
        elif 'agentRef' in data and data['agentRef'] and data['agentRef'].get("id"):
            suppression_level = "agent"
        if data.get('remediation_id'):
            try:
                old_data = await remsupress_ins.get(data['remediation_id'])
            except:
                pass
        if old_data:
            await remsupress_ins(**data).modify()
        else:
            await remsupress_ins(**data).create()
        must = {f"{suppression_level}Ref.id.keyword": data[f"{suppression_level}Ref"]['id'],
                "product.keyword": data["product"], "remediation_status": False}
        params = framework.queryparams.QueryParams()
        params.limit = 10000
        params.skip = 0
        params.q = json.dumps(Helpers.buildElsQuery(must))
        # Todo:- Need to convert this to bulk update
        while True:
            response = await rem_ins().get_all(params)
            if not response.get('count'):
                break
            response = response['data']
            if data.get('version'):
                response = list(filter(lambda x: (
                        Helpers.version_compare(data['version'], x.get("evidence", {}).get('version', '')) in [">",
                                                                                                               "="]),
                                       response))
            if not response:
                break
            date_record = datetime.datetime.utcnow().strftime("%m/%d/%Y")
            for record in response:
                record.update({"remediation_status": True,
                               "remediation_closer_reason": f"Remediation Suppressed On {date_record}"})
            [await rem_ins(**x).update() for x in response]
        return True, f"Remediation Policy Updated Successfully for {data['product']}"

    def getMasterTemplates(self):
        masterData = {}
        with open("/data/agents/masterData/compliance_data.json") as f:
            masterData["compliance"] = json.load(f)
        return masterData

    async def getCompanyRemediationPolicy(self, companyid, remediationstatus="open"):
        acls = keycloakusermgmt.GetAcls()
        includes = acls['includes']
        excludes = acls['excludes']
        if companyid:
            if companyid in excludes:
                return False, "Not Allowed"
            if includes and companyid not in includes:
                return False, "Not Allowed"
        ins = framework.postgresmodel.PostgresModel()
        ins.Config.collection_name = 'test'
        must = {"companyRef.id.keyword": companyid}
        mustExpression = [{"exists": {"field": "remediation_status"}}]
        mustNotExpression = []
        if remediationstatus in ["closed", "suppressed"]:
            must["remediation_status"] = True
            if remediationstatus == "suppressed":
                mustExpression.append(
                    {'match_phrase_prefix': {'remediation_closer_reason': "Remediation Suppressed On*"}})
            else:
                mustNotExpression.append(
                    {'match_phrase_prefix': {'remediation_closer_reason': "Remediation Suppressed On*"}})
        else:
            must["remediation_status"] = False
        all_aggregation_data = []
        for type in ["vuls", "is_denied_application", "is_mandatory_application"]:
            if type == "is_denied_application":
                must["is_denied_application"] = True
                must["is_mandatory_application"] = False
            elif type == "is_mandatory_application":
                must["is_denied_application"] = False
                must["is_mandatory_application"] = True
            else:
                must["is_denied_application"] = False
                must["is_mandatory_application"] = False
            query = Helpers.buildElsQuery(must, mustExpression=mustExpression, mustNotExpression=mustNotExpression)

            fixes = {"sort": [{"u": {"order": "desc"}}],
                     "_source": {"include": ["url", "fix", "remediation_type", "chocoName",
                                             "is_mandatory_application",
                                             "is_denied_application", "remediation_status",
                                             "remediation_closer_reason"]}, "size": 1}
            query["aggs"] = {
                "product": {"terms": {"field": "product.keyword", "order": {"_count": "desc"}, "size": 1000},
                            "aggs": {
                                "assetRef": {"terms": {"field": "assetRef.id.keyword", "order": {"_count": "desc"}, "size": 1000},
                                             "aggs": {"assetIncludes": {"top_hits": {"_source": {"include": ["assetRef", "evidence"]},
                                                          "size": 1}}}},
                                "vulsCount": {"sum": {"field": "vulcount"}},
                                "critical_vuls_count": {"sum": {"field": "critical_vuls_count"}},
                                "high_vuls_count": {"sum": {"field": "high_vuls_count"}},
                                "medium_vuls_count": {"sum": {"field": "medium_vuls_count"}},
                                "low_vuls_count": {"sum": {"field": "low_vuls_count"}},
                                "fixes": {"top_hits": fixes}
                            }}}
            query["size"] = 500
            client = await ins.client()
            await ins.collection_name()
            response = await client.search(index=await ins.collection_name(), body=query)
            aggregationData = []
            for record in response["aggregations"]["product"].get("buckets", []):
                product = {"product": record["key"], "total": record["doc_count"], "assets": [], "url": "", "fix": "",
                           "remediation_type": ""}
                for key in ["critical_vuls_count", "high_vuls_count", "medium_vuls_count", "low_vuls_count",
                            "vulsCount"]:
                    product[key] = record.get(key, {}).get("value", 0)
                for url in record.get("url", {}).get("buckets", []):
                    product["url"] = url["key"]
                    break
                for fix in record.get("fixes", {}).get("hits", {}).get("hits", []):
                    product.update(fix.get("_source", {}))
                    if fix.get("_source", {}).get("remediation_type", ""):
                        product["remediation_type"] = fix['_source']['remediation_type']
                    else:
                        product["remediation_type"] = "application"
                    break
                for rec in record.get("assetRef", {}).get("buckets", []):
                    asset = rec.get('assetIncludes', {}).get("hits", {}).get('hits', [])
                    if not asset:
                        continue
                    else:
                        asset = asset[0]
                    assets = {**asset["_source"]["assetRef"], **{"evidence": asset["_source"].get("evidence", {})}}
                    if not assets in product["assets"]:
                        product["assets"].append(assets)
                product['companyRef'] = {"id": companyid}
                aggregationData.append(product)
            all_aggregation_data.extend(aggregationData)
        return all_aggregation_data

    async def getUniqueApplication(self, appName, companyId=''):
        acls = keycloakusermgmt.GetAcls()
        filterkey = 'companyRef.id.keyword'
        includes = acls['includes']
        excludes = acls['excludes']
        ins = framework.postgresmodel.PostgresModel()
        client = await ins.client()
        ins.Config.collection_name = 'test'
        query = {
            "aggs": {"uniqueName": {"terms": {"field": "name.keyword", "order": {"_count": "desc"}, "size": 50}}},
            "size": 0,
            "query": {"bool": {"filter": [{"bool": {"should": [{"wildcard": {"name": "*" + appName + "*"}}]}}],
                               "must": [{"exists": {"field": "publisher"}}, {"exists": {"field": "version"}}]}}
        }
        if includes:
            inc = {"terms": {filterkey: includes}}
            inc['terms'][filterkey].append("*")
            query["query"]["bool"]["must"].append(inc)
        if excludes:
            exc = {"terms": {filterkey: excludes}}
            if "must_not" not in query["query"]["bool"]:
                query["query"]["bool"]["must_not"] = []
            query["query"]["bool"]["must_not"].append(exc)
        response = await client.search(index=await ins.collection_name(), body=query)
        bucketslist = response['aggregations']['uniqueName']['buckets']
        uniqueName = []
        for items in bucketslist:
            uniqueName.append(items['key'])
        return uniqueName

    async def getGlobalRemediationPolicy(self, remediationstatus="open"):
        acls = keycloakusermgmt.GetAcls()
        filterkey = 'companyRef.id.keyword'
        includes = acls['includes']
        excludes = acls['excludes']
        ins = framework.postgresmodel.PostgresModel()
        ins.Config.collection_name = 'test'
        must = {"remediation_status": False}
        mustExpression = [{"exists": {"field": "remediation_status"}}]
        mustNotExpression = []
        if remediationstatus in ["closed", "suppressed"]:
            must["remediation_status"] = True
            if remediationstatus == "suppressed":
                mustExpression.append(
                    {'match_phrase_prefix': {'remediation_closer_reason': "Remediation Suppressed On*"}})
            else:
                mustNotExpression.append(
                    {'match_phrase_prefix': {'remediation_closer_reason': "Remediation Suppressed On*"}})
        else:
            must["remediation_status"] = False
        all_aggregation_data = []
        for type in ["vuls", "is_denied_application", "is_mandatory_application"]:
            if type == "is_denied_application":
                must["is_denied_application"] = True
                must["is_mandatory_application"] = False
            elif type == "is_mandatory_application":
                must["is_denied_application"] = False
                must["is_mandatory_application"] = True
            else:
                must["is_denied_application"] = False
                must["is_mandatory_application"] = False
            query = Helpers.buildElsQuery(must, mustExpression=mustExpression, mustNotExpression=mustNotExpression)
            # query = Helpers.buildElsQuery({"remediation_status": False},
            #                               mustExpression={"exists": {"field": "remediation_status"}})
            if includes:
                inc = {"terms": {filterkey: includes}}
                inc['terms'][filterkey].append("*")
                query["query"]["bool"]["must"].append(inc)
            if excludes:
                exc = {"terms": {filterkey: excludes}}
                if "must_not" not in query["query"]["bool"]:
                    query["query"]["bool"]["must_not"] = []
                query["query"]["bool"]["must_not"].append(exc)
            fixes = {"sort": [{"u": {"order": "desc"}}], "_source": {"include": ["url", "fix", "remediation_type",
                                                                                 "is_mandatory_application",
                                                                                 "is_denied_application",
                                                                                 "remediation_status",
                                                                                 "remediation_closer_reason"]},
                     "size": 1}
            query["aggs"] = {
                "product": {"terms": {"field": "product.keyword", "order": {"_count": "desc"}, "size": 1000},
                            "aggs": {"company": {
                                "terms": {"field": "companyRef.id.keyword", "order": {"_count": "desc"}, "size": 1000},
                                "aggs": {
                                    "companyRef": {"top_hits": {"_source": {"include": ["companyRef"]}, "size": 1}},
                                    "assetRef": {
                                        "top_hits": {"_source": {"include": ["assetRef", "evidence"]}, "size": 100}},
                                    "vulsCount": {"sum": {"field": "vulcount"}},
                                    "critical_vuls_count": {"sum": {"field": "critical_vuls_count"}},
                                    "high_vuls_count": {"sum": {"field": "high_vuls_count"}},
                                    "medium_vuls_count": {"sum": {"field": "medium_vuls_count"}},
                                    "low_vuls_count": {"sum": {"field": "low_vuls_count"}},
                                    "fixes": {"top_hits": fixes}
                                }}}}}
            query["size"] = 500
            client = await ins.client()
            response = await client.search(index=await ins.collection_name(), body=query)
            aggregationData = []
            for company in response["aggregations"]["product"].get("buckets", []):
                product = {"product": company["key"], "total": company["doc_count"], "companies": [], "url": "",
                           "fix": "", "remediation_type": ""}
                for record in company["company"].get("buckets", []):
                    companyData = {"companyName": "", "companyId": record["key"], "assets": [],
                                   "total": record.get("assetRef", {}).get("hits", {}).get("total", {}).get("value", 0)}
                    for key in ["critical_vuls_count", "high_vuls_count", "medium_vuls_count", "low_vuls_count",
                                "vulsCount"]:
                        companyData[key] = record.get(key, {}).get("value", 0)
                    for url in record.get("url", {}).get("buckets", []):
                        companyData["url"] = url["key"]
                        break
                    for fix in record.get("fixes", {}).get("hits", {}).get("hits", []):
                        for key_source in ["is_mandatory_application", "is_denied_application",
                                           "remediation_status", "remediation_closer_reason"]:
                            if key_source in fix.get("_source", {}):
                                product[key_source] = fix['_source'][key_source]
                        for key_source in ["url", "fix", "remediation_type", "remediation_status"]:
                            if key_source in fix.get("_source", {}):
                                companyData[key_source] = fix['_source'][key_source]
                        if fix.get("_source", {}).get("remediation_type", ""):
                            product["remediation_type"] = fix['_source']['remediation_type']
                        break
                    if record.get("companyRef", {}).get("hits", {}).get("hits", []):
                        companyData["companyName"] = record["companyRef"]["hits"]["hits"][0].get('_source', {}).get(
                            'companyRef', {}).get('name', "")
                    for asset in record.get("assetRef", {}).get("hits", {}).get("hits", []):
                        assets = {**asset["_source"]["assetRef"], **{"evidence": asset["_source"].get("evidence", {})}}
                        if not assets in companyData["assets"]:
                            companyData["assets"].append(assets)
                    product["companies"].append(companyData)
                aggregationData.append(product)
            all_aggregation_data.extend(aggregationData)
        return all_aggregation_data

    async def getCompanyVulnerabilities(self, companyid):
        ins = framework.postgresmodel.PostgresModel()
        ins.Config.collection_name = 'test'
        acls = keycloakusermgmt.GetAcls()
        filterkey = 'companyRef.id.keyword'
        includes = acls['includes']
        excludes = acls['excludes']
        must = {}
        if companyid:
            if companyid in excludes:
                return False, "Not Allowed"
            if includes and companyid not in includes:
                return False, "Not Allowed"
            must.update({"companyRef.id.keyword": companyid})
        query = Helpers.buildElsQuery(must,
                                      mustExpression=[{"exists": {"field": "host.importance"}},
                                                      {"exists": {"field": "vul_stats.risk_score"}},
                                                      {"exists": {"field": 'lastvul_scannedtime'}}])
        if not companyid:
            if includes:
                inc = {"terms": {filterkey: includes}}
                inc['terms'][filterkey].append("*")
                query["query"]["bool"]["must"].append(inc)
            if excludes:
                exc = {"terms": {filterkey: excludes}}
                if "must_not" not in query["query"]["bool"]:
                    query["query"]["bool"]["must_not"] = []
                query["query"]["bool"]["must_not"].append(exc)
        query["aggs"] = {"osname": {"terms": {"field": "os.name.keyword", "order": {"_count": "desc"}, "size": 100},
                                    "aggs": {"company": {
                                        "terms": {"field": "companyRef.id.keyword", "order": {"_count": "desc"},
                                                  "size": 100},
                                        "aggs": {
                                            "companyRef": {
                                                "top_hits": {"_source": {"include": ["companyRef"]}, "size": 1}},
                                            "assetRef": {
                                                "top_hits": {"_source": {"include": ["host.host_name", "host.ip"]},
                                                             "size": 100}},
                                            "count_of_critical_vuls": {
                                                "sum": {"field": "vul_stats.count_of_critical_vuls"}},
                                            "count_of_high_vuls": {"sum": {"field": "vul_stats.count_of_high_vuls"}},
                                            "count_of_medium_vuls": {
                                                "sum": {"field": "vul_stats.count_of_medium_vuls"}},
                                            "count_of_low_vuls": {"sum": {"field": "vul_stats.count_of_low_vuls"}},
                                            "risk_score": {"avg": {"field": "vul_stats.risk_score"}}
                                        }}}}}
        query["size"] = 500
        client = await ins.client()
        response = await client.search(index=await ins.collection_name(), body=query)
        aggregationData = []

        for company in response["aggregations"]["osname"].get("buckets", []):
            osData = {"osname": company["key"], "total": company["doc_count"], "companies": []}
            for record in company["company"].get("buckets", []):
                companyData = {"assets": [],
                               "total": record.get("assetRef", {}).get("hits", {}).get("total", {}).get("value", 0)}
                for key in ["count_of_critical_vuls", "count_of_high_vuls", "count_of_medium_vuls",
                            "count_of_low_vuls"]:
                    companyData[key.split("count_of_")[-1]] = record.get(key, {}).get("value", 0)
                companyData["risk_score"] = round(record.get("risk_score", {}).get("value", 0), 2)
                if not companyid:
                    companyData.update({"companyName": "", "companyId": record["key"]})
                    if record.get("companyRef", {}).get("hits", {}).get("hits", []):
                        companyData["companyName"] = record["companyRef"]["hits"]["hits"][0].get('_source', {}).get(
                            'companyRef', {}).get('name', "")
                for asset in record.get("assetRef", {}).get("hits", {}).get("hits", []):
                    ip = asset["_source"].get("host", {}).get("ip", "")
                    companyData["assets"].append(
                        {"id": asset["_id"], "name": asset["_source"].get("host", {}).get("host_name", ip)})
                osData["companies"].append(companyData)
            if not companyid:
                aggregationData.append(osData)
            else:
                aggregationData.append(
                    {"osname": osData["osname"], "total": osData["osname"], **osData["companies"][0]})

        return aggregationData

    async def searchCVE(self, cve, companyid):
        if companyid:
            acls = keycloakusermgmt.GetAcls()
            includes = acls['includes']
            excludes = acls['excludes']
            if companyid in excludes:
                return False, "Not Allowed"
            if includes and companyid not in includes:
                return False, "Not Allowed"
        cve = cve.strip()
        status, resp = assetProcessor.AssetProcessor()._centralServer(
            "/usermgmt/api/central_services/dummy/get_details", {"cve_list": [cve.upper()], "include_title": True})
        if not status or not resp or resp.get('status') != "ok":
            return False, "Cve not found"
        cve_info = resp["msg"][0]
        cve_info["severity"] = cve_info["severity"].title()
        cve_info["assets"] = []
        if not companyid:
            return True, cve_info
        ins = framework.postgresmodel.PostgresModel()
        ins.Config.collection_name = 'test'
        query = Helpers.buildElsQuery({"companyRef.id.keyword": companyid, "vul_id.keyword": cve.upper()})
        params = framework.queryparams.QueryParams()
        params.limit = 10000
        params.skip = 0
        params.q = json.dumps(query)
        params.fields = ["assetRef"]
        response = await ins.get_all(params)
        if response["data"]:
            cve_info.update({"assets": [record['assetRef'] for record in response['data']]})
        return True, cve_info

    async def getNetworkVulsData(self, companyid):
        acls = keycloakusermgmt.GetAcls()
        includes = acls['includes']
        excludes = acls['excludes']
        if companyid in excludes:
            return False, "Not Allowed"
        if includes and companyid not in includes:
            return False, "Not Allowed"
        ins = framework.postgresmodel.PostgresModel()
        ins.Config.collection_name = 'test'
        query = Helpers.buildElsQuery({"companyRef.id.keyword": companyid},
                                      mustExpression=[{"exists": {"field": "vul_id"}},
                                                      {"exists": {"field": "score.cvss_score"}},
                                                      {"range": {"score.cvss_score": {"gt": 0}}}])
        fixes = {"sort": [{"u": {"order": "desc"}}], "_source": {"include": ["title", "severity", 'score.cvss_score']},
                 "size": 1}

        query["aggs"] = {"vul_id": {"terms": {"field": "vul_id.keyword", "order": {"_count": "desc"}, "size": 1000},
                                    "aggs": {
                                        "assetRef": {"top_hits": {
                                            "_source": {"include": ["assetRef", "ref", 'ticketId', 'port']},
                                            "size": 100}},
                                        "fixes": {"top_hits": fixes}
                                    }}}
        query["size"] = 500
        client = await ins.client()
        response = await client.search(index=await ins.collection_name(), body=query)
        network = []
        for record in response["aggregations"]["vul_id"].get("buckets", []):
            product = {"vul_id": record["key"], "total": record["doc_count"], "assets": []}
            for data in record.get("fixes", {}).get("hits", {}).get("hits", []):
                product.update(**{"title": data["_source"].get("title", '')},
                               **{"severity": data["_source"].get("severity", '')},
                               **{"score": data["_source"]['score'].get("cvss_score", '')})
                for asset in record.get("assetRef", {}).get("hits", {}).get("hits", []):
                    assets = {**asset["_source"]["assetRef"], **{"ref": asset["_source"].get("ref", {})},
                              **{"ticketId": asset["_source"].get("ticketId", '')},
                              **{"port": asset["_source"].get("port", '')}}
                    if not assets in product["assets"]:
                        product["assets"].append(
                            {**asset["_source"]["assetRef"], **{"ticketId": asset["_source"].get("ticketId", '')},
                             **{"ref": asset["_source"].get("ref", '')}, **{"port": asset["_source"].get("port", '')}})
            network.append(product)
        return network

    async def getGlobalNetworkVulsData(self):
        acls = keycloakusermgmt.GetAcls()
        includes = acls['includes']
        excludes = acls['excludes']
        ins = framework.postgresmodel.PostgresModel()
        ins.Config.collection_name = 'test'
        filterkey = "companyRef.id.keyword"
        query = Helpers.buildElsQuery(mustExpression=[{"exists": {"field": "vul_id"}},
                                                      {"exists": {"field": "score.cvss_score"}},
                                                      {"range": {"score.cvss_score": {"gt": 0}}}])
        if includes:
            inc = {"terms": {filterkey: includes}}
            inc['terms'][filterkey].append("*")
            query["query"]["bool"]["must"].append(inc)
        if excludes:
            exc = {"terms": {filterkey: excludes}}
            if "must_not" not in query["query"]["bool"]:
                query["query"]["bool"]["must_not"] = []
            query["query"]["bool"]["must_not"].append(exc)
        fixes = {"sort": [{"u": {"order": "desc"}}], "_source": {"include": ["title", "severity", 'score.cvss_score']},
                 "size": 1}

        query["aggs"] = {"vul_id": {"terms": {"field": "vul_id.keyword", "order": {"_count": "desc"}, "size": 1000},
                                    "aggs": {"company": {
                                        "terms": {"field": "companyRef.id.keyword", "order": {"_count": "desc"},
                                                  "size": 1000},
                                        "aggs": {
                                            "companyRef": {
                                                "top_hits": {"_source": {"include": ["companyRef"]}, "size": 1}},
                                            "assetRef": {"top_hits": {
                                                "_source": {"include": ["assetRef", "ref", 'ticketId', 'port']},
                                                "size": 100}},
                                            "fixes": {"top_hits": fixes}
                                        }}}}}
        query["size"] = 500
        client = await ins.client()
        response = await client.search(index=await ins.collection_name(), body=query)
        aggregationData = []
        for company in response["aggregations"]["vul_id"].get("buckets", []):
            product = {"vul_id": company["key"], "total": company["doc_count"], "companies": [], "title": "",
                       "severity": "", "score": ""}
            for record in company["company"].get("buckets", []):
                companyData = {"companyName": "", "companyId": record["key"], "assets": [],
                               "total": record.get("assetRef", {}).get("hits", {}).get("total", {}).get("value", 0)}

                for fix in record.get("fixes", {}).get("hits", {}).get("hits", []):
                    companyData.update(fix.get("_source", {}))
                    if fix.get("_source", {}):
                        product["title"] = fix["_source"]['title']
                        product['severity'] = fix["_source"]['severity']
                        product['score'] = fix["_source"]['score'].get("cvss_score", '')

                if record.get("companyRef", {}).get("hits", {}).get("hits", []):
                    companyData["companyName"] = record["companyRef"]["hits"]["hits"][0].get('_source', {}).get(
                        'companyRef', {}).get('name', "")
                    for asset in record.get("assetRef", {}).get("hits", {}).get("hits", []):
                        assets = {**asset["_source"]["assetRef"], **{"ref": asset["_source"].get("ref", {})},
                                  **{"ticketId": asset["_source"].get("ticketId", '')},
                                  **{"port": asset["_source"].get("port", '')}}
                        if not assets in companyData["assets"]:
                            companyData["assets"].append(assets)
                    product["companies"].append(companyData)
            aggregationData.append(product)
        return aggregationData


class XlsxreportGenerator():
    async def generateXlsxReport(self, clsins, clsname, query, filename, fieldMap):
        fieldMap = {d.field: d.renameas for d in fieldMap}
        if not filename.endswith(".xlsx"):
            filename += ".xlsx"
        basepath = "/data/agents/runtimereports"
        if not os.path.exists(basepath):
            os.makedirs(basepath)
        params = framework.queryparams.QueryParams()
        params.q = query
        params.limit = 10000
        params.skip = 0
        params.fields = list(fieldMap.keys())
        if clsname == "Compliance":
            if "complaince_id" not in params.fields:
                params.fields.append("complaince_id")
        responseData = await clsins().get_all(params)
        data = responseData['data']
        if clsname == "Compliance":
            for record in data:
                for key, value in record.get('benchmarks', {}).items():
                    record[f"benchmarks.{key}"] = value
                if "benchmarks" in record:
                    del record["benchmarks"]
        df = pd.DataFrame(data)
        if clsname == "Compliance":
            with open("/data/agents/masterData/compliance_data.json") as f:
                complianceData = json.load(f)
                for id, comp_data in complianceData.items():
                    comp_data["complaince_id"] = id
                df_ = pd.DataFrame(list(complianceData.values()))
                df_.rename(columns={"title": "Title", "description": "Description", "remediation": "Remediation",
                                    "rationale": "Rationale"}, inplace=True)
                if fieldMap:
                    for key in ["Title", "Description", "Remediation"]:
                        if key not in fieldMap:
                            fieldMap[key] = key
                df = pd.merge(df, df_, how='left', on="complaince_id")
        # df.drop(['_id'], axis = 1)
        columns = list(df.columns)
        if not fieldMap:
            fieldMap = {k: k.title() for k in columns}
        missingkeys = list(set(list(fieldMap.keys())) - set(columns))
        for key in missingkeys:
            del fieldMap[key]
        df.rename(fieldMap, axis='columns', inplace=True)
        if '_id' in df.columns:
            df.pop('_id')
        df.to_excel(os.path.join(basepath, filename))
        return "agents/runtimereports/" + filename


class ComplianceProcessor(object):
    def getUniqueComplianceRules(self):
        return True, [
            {"name": 'CIS', "value": 'cis', "data": []},
            {"name": 'CIS CSC', "value": 'cis_csc', "data": []},
            {"name": 'GDPR IV', "value": 'gdpr_IV', "data": []},
            {"name": 'GPG 13', "value": 'gpg13', "data": []},
            {"name": 'HIPAA', "value": 'hipaa', "data": []},
            {"name": 'NIST 800 53', "value": 'nist_800_53', "data": []},
            {"name": 'PCI DSS', "value": 'pci_dss', "data": []}
        ]

    async def getComplianceData(self, companyid, compliance_type):
        ins = framework.postgresmodel.PostgresModel()
        ins.Config.collection_name = 'test'
        query = Helpers.buildElsQuery({"companyRef.id.keyword": companyid, "iscompliant": True},
                                      mustExpression=[{"exists": {"field": "complaince_id"}},
                                                      {"exists": {"field": f"benchmarks.{compliance_type}.keyword"}}])
        query["aggs"] = {
            "compliance_type": {"terms": {"field": f"complaince_id.keyword", "order": {"_count": "desc"}, "size": 1500},
                                "aggs": {"assetRef": {
                                    "terms": {"field": "assetRef.id.keyword", "order": {"_count": "desc"},
                                              "size": 3000},
                                    "aggs": {
                                        "assetRef": {"top_hits": {
                                            "_source": {"include": ["iscompliant", "assetRef",
                                                                    f"benchmarks.{compliance_type}"]},
                                            "size": 1}}
                                    }}}}}
        query["size"] = 0
        client = await ins.client()
        response = await client.search(index=await ins.collection_name(), body=query, request_timeout=45)
        complianceData = {}
        for record in response['aggregations'].get('compliance_type', {}).get('buckets', []):
            assets = []
            for bucket in record.get('assetRef', {}).get('buckets', []):
                assets.extend([{**rec['_source'].get('assetRef', {}),
                                'iscompliant': True, 'compliance_id': record['key'],
                                compliance_type: rec['_source'].get('benchmarks', {}).get(compliance_type, [''])[0]}
                               for rec in bucket.get('assetRef', {}).get('hits', {}).get('hits', [])])
            if len(assets) > 0:
                if record['key'] not in complianceData:
                    complianceData[record['key']] = {"assets": [], 'total': 0, 'compliant': 0,
                                                     'noncompliant': 0,
                                                     'compliance_id': record['key']}
                complianceData[record['key']]['assets'].extend(assets)
                complianceData[record['key']]['total'] = len(complianceData[record['key']]['assets'])
                complianceData[record['key']]['compliant'] = len(assets)
                complianceData[record['key']]['noncompliant'] = 0
                # complianceData[record['key']]['noncompliant'] = len(assets) - complianceData[record['key']]['compliant']
        query = Helpers.buildElsQuery({"companyRef.id.keyword": companyid, "iscompliant": False},
                                      mustExpression=[{"exists": {"field": "complaince_id"}},
                                                      {"exists": {"field": f"benchmarks.{compliance_type}.keyword"}}])
        query["aggs"] = {
            "compliance_type": {"terms": {"field": f"complaince_id.keyword", "order": {"_count": "desc"}, "size": 1500},
                                "aggs": {"assetRef": {
                                    "terms": {"field": "assetRef.id.keyword", "order": {"_count": "desc"},
                                              "size": 3000},
                                    "aggs": {
                                        "assetRef": {"top_hits": {
                                            "_source": {"include": ["iscompliant", "assetRef",
                                                                    f"benchmarks.{compliance_type}"]},
                                            "size": 1}}
                                    }}}}}
        query["size"] = 0
        client = await ins.client()
        response = await client.search(index=await ins.collection_name(), body=query, request_timeout=45)
        for record in response['aggregations'].get('compliance_type', {}).get('buckets', []):
            assets = []
            for bucket in record.get('assetRef', {}).get('buckets', []):
                assets.extend([{**rec['_source'].get('assetRef', {}),
                                'iscompliant': False, 'compliance_id': record['key'],
                                compliance_type: rec['_source'].get('benchmarks', {}).get(compliance_type, [''])[0]}
                               for rec in bucket.get('assetRef', {}).get('hits', {}).get('hits', [])])
            if len(assets) > 0:
                if record['key'] not in complianceData:
                    complianceData[record['key']] = {"assets": [], 'total': 0, 'compliant': 0,
                                                     'noncompliant': 0,
                                                     'compliance_id': record['key']}
                complianceData[record['key']]['assets'].extend(assets)
                complianceData[record['key']]['total'] = len(complianceData[record['key']]['assets'])
                complianceData[record['key']]['noncompliant'] = len(assets)
        return True, complianceData


class CyberUtilities():
    def _getRedisInstance(self):
        return redis.Redis(db=5)

    def getSupportedTimeZones(self):
        return pytz.all_timezones

    def getSchedulerTimeZone(self):
        redisIns = self._getRedisInstance()
        resp = redisIns.get("shedulerTimezone")
        if resp:
            resp = resp.decode()
        else:
            resp = "US/Central"
        redisIns.close()
        return resp

    def updateSchedulerTimeZone(self, timezone):
        redisIns = self._getRedisInstance()
        oldTimeZone = self.getSchedulerTimeZone()
        if timezone not in pytz.all_timezones:
            return False, "Timezone %s not supported" % timezone
        redisIns.set('shedulerTimezone', timezone)
        redisIns.close()
        if oldTimeZone != timezone:
            job_data = {"model": "service", "serviceName": "cyberscheduler", "arguments": [],
                        'serviceaction': 'restart'}
            cyberPrevilagedManager.RedisQueue('previlegedservices').put(json.dumps(job_data))
        #     Helpers.execute("systemctl restart scheduler")
        return True, "Success"

    def getReleaseNotes(self):
        # Get release notes
        relase_note_list = []
        try:
            resp = requests.get(
                "https://cybercnsagent.s3.amazonaws.com/release_notes.txt")
            if resp.status_code == 200:
                relase_note_list = str(resp.text).strip().split("\n")
        except:
            pass
        # if not relase_note_list and os.path.exists("/data/cybercns/cyberbase/release_notes_v2.txt"):
        #     with open("/data/cybercns/cyberbase/release_notes_v2.txt") as fopen:
        #         data = fopen.read()
        #         relase_note_list = str(data).split("\n")

        if relase_note_list and len(relase_note_list) > 2:
            date = relase_note_list[0].replace("Date:", "")
            release_notes = relase_note_list[2:]
            while '' in release_notes:
                release_notes.remove('')
            return {"date": date, "release_notes": release_notes}
        return {}

    def getSessionTimeoutSettings(self):
        redisIns = self._getRedisInstance()
        resp = redisIns.get("sessionTimeoutSettings")
        if resp:
            resp = json.loads(resp.decode())
        else:
            resp = {"idle": 1800, "timeout": 1800, "ping": 1800}
        redisIns.close()
        return resp

    def updateSessionTimeoutSettings(self, data):
        redisIns = self._getRedisInstance()
        redisIns.set("sessionTimeoutSettings", json.dumps(data.dict()))
        redisIns.close()
        return True, "Success"

    def getBuildInfo(self):
        data = {}
        redisIns = self._getRedisInstance()
        temp_data = redisIns.hgetall('builddata')
        if len(temp_data) > 0:
            for key, value in temp_data.items():
                data[key.decode()] = value.decode()
            if 'ui' in data:
                try:
                    data['ui'] = json.loads(data['ui'])
                except Exception as e:
                    logger.info(e)
            if 'backend' in data:
                try:
                    data['backend'] = json.loads(data['backend'])
                except Exception as e:
                    logger.info(e)
                    data['backend'] = data['backend']
        if not data.get('ui'):
            data['ui'] = {}
        if not data.get('backend'):
            data['backend'] = {}
        return True, data

    def getFeedInfo(self):
        software_repo_email = "support@netalytics.co"
        software_repo_api_key = ""
        feedInfo = []
        errMsg = ""
        resp = requests.post("https://swmanager.mycybercns.com/usermgmt/api/feed_info/dummy/getFeedInfo",
                             headers={'X-Api-AccessKey': software_repo_api_key,
                                      "content-type": "application/json"})
        if resp.status_code != 200:
            logger.info("Error getting details to %s" % resp.text)
            errMsg = "Error fetching details from central server"
        else:
            data = resp.json()
            if data['status'] == "ok":
                feedInfo.extend(data.get('msg', []))
        session = requests.session()
        resp = session.post("https://3.91.65.42/api/login",
                            data=json.dumps({"email": software_repo_email, "apiKey": software_repo_api_key}),
                            headers={"Content-Type": "application/json"}, verify=False)
        if resp.status_code != 200:
            logger.info("Error login to 3.91.65.42")
            errMsg = "Error connecting to central server"
        else:
            resp = session.post("https://3.91.65.42/api/feed_info/dummy/getFeedInfo",
                                headers={"Content-Type": "application/json"}, verify=False)
            if resp.status_code != 200:
                logger.info("Error getting details to %s %s" % ("3.91.65.42", resp.text))
                errMsg = "Error fetching details from central server"
            else:
                data = resp.json()
                if data['status'] == "ok":
                    feedInfo.extend(data.get('msg', []))
        if not feedInfo:
            return False, errMsg if errMsg else "Error connecting to central server"
        return True, feedInfo

    def checkCyberUpdates(self, updatetype=''):
        # return True, {"backend": False, "ui": False}
        deferrmsg = "Error in getting updates check from central server"
        url = 'https://signup.mycybercns.com/api/cyberv2_updatecheck/dummy/getavailableUpdates'
        resp = requests.get(url, data={"updatetype": updatetype})
        if (resp.status_code / 100) != 2:
            return False, deferrmsg
        respData = resp.json()
        if respData.get("status", "") != "ok":
            return False, respData.get("msg", deferrmsg)
        status, buildInfo = self.getBuildInfo()
        update_status = {}
        for update_type, sha in respData['msg'].items():
            if sha != buildInfo.get(update_type, {}).get("commitSha", ""):
                update_status[update_type] = True
            else:
                update_status[update_type] = False
        return True, update_status

    def installCyberUpdates(self, updatetype=''):
        r = redis.Redis()
        patch_update_status = r.get("patch_update_status")
        r.close()
        if patch_update_status:
            if isinstance(patch_update_status, bytes):
                patch_update_status = json.loads(patch_update_status.decode())
            else:
                patch_update_status = json.loads(patch_update_status)
            initiated_time = patch_update_status["initiatedTime"]

            if patch_update_status.get('status') == 3 and \
                    (datetime.datetime.utcnow() - datetime.datetime.fromisoformat(initiated_time)).seconds < 30 * 60:
                return False, "Patching in progress, Please try after some time"
        status, resp = self.checkCyberUpdates(updatetype)
        if not status or not resp:
            return status, resp
        if True not in list(set(list(resp.values()))):
            return False, "No Pending updates available"
        arguments = ""
        if "backend" in resp:
            arguments += "b"
        if "ui" in resp:
            arguments += "u"
        if not arguments:
            arguments = "bu"
        job_data = {"model": "service", "serviceName": "codeupdater", "arguments": [arguments]}
        cyberPrevilagedManager.RedisQueue('previlegedservices').put(json.dumps(job_data))
        return True, "Patch update initiated"

    def getPatchingStatus(self):
        r = redis.Redis()
        patch_update_status = r.get("patch_update_status")
        r.close()
        if patch_update_status:
            if isinstance(patch_update_status, bytes):
                patch_update_status = json.loads(patch_update_status.decode())
            else:
                patch_update_status = json.loads(patch_update_status)
        else:
            patch_update_status = {}
        return patch_update_status

    async def partnerInsightsData(self, getReport="", companyId=""):
        queryList = {
            "osBreakdown": {"size": 0, "aggs": {
                "aggs": {"terms": {"field": "companyRef.id.keyword", "order": {"_key": "desc"}, "size": 1000}, "aggs": {
                    "aggs": {"terms": {"field": "os.name.keyword", "order": {"_key": "desc"}, "size": 1000}, "aggs": {
                        "aggs": {"top_hits": {"docvalue_fields": [{"field": "host.manufacturer.keyword"}],
                                              "_source": "host.manufacturer.keyword", "size": 1,
                                              "sort": [{"u": {"order": "desc"}}]}}}}}}},
                            "query": {"bool": {"must": [], "filter": [{"exists": {"field": "host.importance"}}]}}},
            "firewallAssets": {"size": 0, "aggs": {
                "aggs": {"terms": {"field": "companyRef.id.keyword", "order": {"_count": "desc"}, "size": 10000}}},
                               "query": {"bool": {"must": [], "filter": [{"exists": {"field": "host.importance"}}, {
                                   "match": {"os.product_type.keyword": "firewall"}}]}}},
            "allAssets": {"size": 0, "query": {"bool": {"must": [{"exists": {"field": "host.importance"}}]}}},
            "companylevelAssets": {"size": 0, "aggs": {
                "aggs": {"terms": {"field": "companyRef.id.keyword", "order": {"_count": "desc"}, "size": 10000},
                         "aggs": {"aggs": {"terms": {"field": "companyRef.name.keyword", "order": {"_count": "desc"},
                                                     "size": 10000}}}}}, "query": {
                "bool": {"must": [], "filter": [{"exists": {"field": "host.importance"}}]}}},
            "externalAssets": {"size": 0, "aggs": {"aggs": {"terms": {"field": "companyRef.id.keyword"}}}, "query": {
                "bool": {"must": [], "filter": [{"match_phrase": {"discoveredProtocols.keyword": "EXTERNALSCAN"}}]}}},
            "companyList": {"size": 10000, "query": {
                "bool": {"must": [], "filter": [{"exists": {"field": "description.keyword"}}],
                         "must_not": [{"exists": {"field": "companyRef.id.keyword"}}]}}}}
        ins = framework.postgresmodel.PostgresModel()
        ins.Config.collection_name = "test"
        index = await ins.collection_name()
        for key, assetquery in queryList.items():
            if companyId and key not in ["companyList"]:
                assetquery["query"]["bool"]["must"].append({"match": {"companyRef.id.keyword": companyId}})
            client = await ins.client()
            queryList[key] = await client.search(index=index, body=assetquery)
        firewallassets = {x.get("key"): x.get("doc_count")
                          for x in
                          queryList.get("firewallAssets", {}).get("aggregations", {}).get("aggs", {}).get("buckets",
                                                                                                          [])}
        externalassets = {x.get("key"): x.get("doc_count")
                          for x in
                          queryList.get("externalAssets", {}).get("aggregations", {}).get("aggs", {}).get("buckets",
                                                                                                          [])}
        companynames = {x.get("_id", ""): x.get("_source", {}).get("name", {})
                        for x in queryList.get("companyList", {}).get("hits", {}).get("hits", [])}
        finaldata = {
            "totalCompanies": queryList.get("companyList", {}).get("hits", {}).get("total", {}).get("value", 0),
            "totalAssets": queryList.get("allAssets", {}).get("hits", {}).get("total", {}).get("value", {}),
            "companyOverview": []}
        companylist = []
        for x in queryList.get("osBreakdown", {}).get("aggregations", {}).get("aggs", {}).get("buckets", []):
            companylist.append(x.get("key", ""))
            finaldata["companyOverview"].append({
                "companyName": companynames.get(x.get("key", ""), ""),
                "companyId": x.get("key", ""),
                "totalAssets": x.get("doc_count", 0),
                "external": externalassets.get(x.get("key", ""), 0),
                "firewalls": firewallassets.get(x.get("key", ""), 0),
                "assets": x.get("doc_count", 0) - externalassets.get(x.get("key", ""), 0) - firewallassets.get(
                    x.get("key", ""), 0),
                "details": sorted([{"os": y.get("key", "") if y.get("key", "") else "Unknown",
                                    "count": y.get("doc_count", 0)} for y in x.get("aggs", {}).get("buckets", [])],
                                  key=lambda details: (details['os'].lower()))})
        if companyId:
            if companyId not in companylist:
                return False ,f"No assets present in {companynames.get(companyId,'')}"
        else:
            finaldata["companyOverview"].extend(
            {"companyName": v, "companyId": k, "totalAssets": 0, "external": 0, "firewalls": 0, "assets": 0,
             "details": []} for k, v in companynames.items() if k not in companylist)
        reportPath = f"/data/agents/runtimereports/partner Insights"
        if companynames.get(companyId, ''):
            reportPath = reportPath+f" - {companynames.get(companyId, '')}"
        if getReport=="docx":
            tpl = DocxTemplate("/data/ReportTpl/DocxTpl/partnerInsightsData.docx")
            finaldata["partnerlogo"] = {
                "image": InlineImage(tpl, "/usr/share/nginx/cybercns/ui/assets/images/cybercns_logo.png", width=Mm(70))}
            finaldata["companyId"] = True if companyId else False
            tpl.render(finaldata)
            reportPath=reportPath+".docx"
            tpl.save(reportPath)
        elif getReport == "xlsx":
            if companyId:
                dflist=[{"os": "","count": 0}]
                for companies in finaldata.get("companyOverview",[]):
                    if companyId==companies.get("companyId",""):
                        dflist=companies.get("details",[])
                        break
                df = pd.DataFrame(dflist, columns=["os", "count"])
            else:
                df = pd.DataFrame(finaldata["companyOverview"],
                                  columns=["companyName", "totalAssets", "assets", "external", "firewalls"])
            df.fillna("-", inplace=True)
            reportPath = reportPath + ".xlsx"
            await self.generateXlsx(reportPath,df)
        else:
            return True, finaldata
        return True, reportPath.replace("/opt", "")

    async def generateXlsx(self,reportPath,df):
        writer = pd.ExcelWriter(reportPath, engine="xlsxwriter")
        workbook = writer.book
        df.to_excel(writer, sheet_name="Partner Insights", index=False, startcol=0)
        worksheet = writer.sheets["Partner Insights"]
        color = workbook.add_format({"bg_color": "#FFFFFF", "font_color": "#000081", "border": 1})
        color.set_align("left")
        color.set_align("vcenter")
        header_color = workbook.add_format(
            {"bg_color": "#DAF7A6", "font_color": "#000081", "border": 1, "font_size": 14, "bold": True})
        header_color.set_align("left")
        header_color.set_align("vcenter")
        for i, col in enumerate(df.columns.values):
            worksheet.set_row(0, None, color)
            worksheet.write(0, i, col, header_color)
            worksheet.set_column(i - 1, i, len(col) + 10, color)
        writer.save()


    async def sendSlackMsg(self, message):
        return True, ""
        jdata = {"blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": ""}}]}
        jdata["blocks"][0]["text"]["text"] = "CyberCNS V2:- " + message
        if "Internal Error" in message:
            redisIns = await framework.redispool.get_redis_connection()
            id = message.split("Internal Error:-")[-1].strip().split('"}')[0].strip()
            if id:
                resp = await redisIns.get("internalerror_" + id)
                if resp:
                    if isinstance(resp, bytes):
                        resp = resp.decode()
                    d = {"type": "section", "text": {"type": "mrkdwn", "text": "*" * 30 + "Stack Trace" + "*" * 30}}
                    jdata["blocks"].append(d)
                    d = {"type": "section", "text": {"type": "mrkdwn", "text": resp[0:3000]}}
                    jdata["blocks"].append(d)
                    if len(resp) > 30000:
                        d = {"type": "section", "text": {"type": "mrkdwn", "text": resp[3000:]}}
                        jdata["blocks"].append(d)
                    d = {"type": "section", "text": {"type": "mrkdwn", "text": "*" * 70}}
                    jdata["blocks"].append(d)
                    await redisIns.delete("internalerror_" + id)
                    return True, requests.post(url, json.dumps(jdata))
        return True, ""

async def getCompanyAgents(agent_ins, companyid):
    agents = []
    ins = framework.postgresmodel.PostgresModel()
    ins.Config.collection_name = 'test'
    query = Helpers.buildElsQuery({"companyRef.id.keyword": companyid, "agent_type": 1},
                                  mustExpression=[{"exists": {"field": "agent_type"}}])

    params = framework.queryparams.QueryParams()
    params.q = json.dumps(query)
    params.limit = 1000
    resp = await agent_ins.get_all(params)
    for agent in resp['data']:
        agents.append({"_id": agent['_id'], "name": agent["name"], "agent_type": agent["agent_type"]})

    query = Helpers.buildElsQuery({"agent_type": 4},
                                  mustExpression=[{"exists": {"field": "agent_type"}}])
    params = framework.queryparams.QueryParams()
    params.q = json.dumps(query)
    params.limit = 1
    resp = await agent_ins.get_all(params)
    for agent in resp['data']:
        agents.append({"_id": agent['_id'], "name": agent["name"], "agent_type": agent["agent_type"]})
    return True, agents


def _getDashboardDetails():
    headers = {'osd-xsrf': 'reporting', 'Content-Type': 'application/json'}
    try:
        dburl = [str(url) for url in framework.settings.db_urls["elastic"]]
        username, password = dburl[0].split('@')[0].split("/")[-1].split(':')
        logindata = {'username': username, 'password': password}
        loginresp = requests.post("http://localhost:5601/kibana/auth/login", headers=headers,
                                  data=json.dumps(logindata))
        if int(loginresp.status_code / 100) != 2:
            return False, loginresp.text
        headers['Cookie'] = loginresp.headers['set-cookie'].split(";")[0]
        exportUrl = f"http://localhost:5601/kibana/api/saved_objects/_find?default_search_operator=AND&page=1&per_page=1000&search_fields=title%5E3&search_fields=description&type=dashboard"
        headers["osd-xsrf"] = "kibana"
        headers["securitytenant"] = framework.ctx['tenant']
        dashboardresp = requests.get(exportUrl, headers=headers, verify=False)
        if int(dashboardresp.status_code / 100) != 2:
            return False, dashboardresp.text
        ids = {}
        dashboardJson = dashboardresp.json()
        for dashboard in dashboardJson['saved_objects']:
            ids[dashboard['attributes']['title']] = dashboard['id']
            # ids[dashboard['id']] = dashboard['attributes']['title']
        return True, ids
    except Exception as e:
        return False, "Exception while login to kibana"


def CompanycompanyDashboards(reconId, assetid):
    # todo:- need to check company existance
    acls = keycloakusermgmt.GetAcls()
    includes = acls['includes']
    excludes = acls['excludes']
    if reconId in excludes:
        return False, "Not Allowed"
    if includes and reconId not in includes:
        return False, "Not Allowed"
    dashboardList = []
    dashboards = {
        "Recon Summary": {
            "Recon Summary": "441ccfd0-5728-11ec-9d9b-3b765ce9919a"
        }
    }

    st, ids = _getDashboardDetails()

    # print(f"the dashboard dictionary which is available is {ids}")
    # baseUrl = "/kibana/app/dashboards?security_tenant={tenantId}#/view/{dashBoardId}?_g=(filters:!(),refreshInterval:(pause:!t,value:0),time:(from:now-30d,to:now))&_a=(description:'\'',filters:!(),fullScreenMode:!f,options:(hidePanelTitles:!f,useMargins:!t),query:(language:kuery,query:'companyRef.id.keyword:\"{companyId}\"\''),timeRestore:!f,title:Overview,viewMode:view)&show-top-menu=true&show-time-filter=true&hide-filter-bar=true"
    baseUrl = "/kibana/app/dashboards?security_tenant={tenantId}#/view/{dashBoardId}?_g=(filters:!(),refreshInterval:(pause:!t,value:0),time:(from:now-30d,to:now))&_a=(description:'Updated%20on%2016-06-22',filters:!(''),fullScreenMode:!f,options:(hidePanelTitles:!f,useMargins:!t),query:(language:kuery,query:''),timeRestore:!t,title:'Recon%20Summary',viewMode:view)"
    if st and ids:
        for name, dashboardId in ids.items():
            dashboardList.append({"name": name,
                                #   "section": "Global",
                                  "section": framework.ctx["tenant"],
                                  "url": baseUrl.format(dashBoardId=dashboardId,
                                                        tenantId=framework.ctx["tenant"],
                                                        # tenantId="global",
                                                        reconId=reconId,
                                                        description=urllib.parse.quote(name))})
    else:
        for section, dashboard in dashboards.items():
            for name, dashboardId in dashboard.items():
                dashboardList.append({"name": name,
                                      "section": section,
                                      "url": baseUrl.format(dashBoardId=dashboardId,
                                                            tenantId=framework.ctx["tenant"],
                                                            # tenantId="global",
                                                            reconId=reconId,
                                                            description=urllib.parse.quote(name))})
    return True, dashboardList


async def modifyCompanyName(companyid, companyName):
    ins = framework.postgresmodel.PostgresModel()
    client = await ins.client()
    query = Helpers.buildElsQuery({"companyRef.id.keyword": companyid}, mustExpression=[{"exists": {"field": "companyRef.id"}}])
    query['script'] = {
        "inline": f"ctx._source.companyRef.name='{companyName}'",
        "lang": "painless"
    }
    for index in ['test', 'test_timeseries', 'test_ad_audit']:
        ins.Config.collection_name = index
        indexName = await ins.collection_name()
        try:
            await client.update_by_query(index=indexName, body=query)
        except Exception as e:
            print("Exception while running update by query %s" % e)

def getApiRoles():
    roles = {}
    for file in glob.glob("*_roles.json"):
        with open(file) as f:
            roles.update(json.load(f))
    return roles


def _generateRandomPassword(length=16):
    lower = string.ascii_lowercase
    upper = string.ascii_uppercase
    num = string.digits
    symbols = string.punctuation
    symbols = "#$!_-=;[]|(){}^*~"
    #string.ascii_letters
    #combine the data
    all = lower + upper + num + symbols
    #use random
    temp = random.sample(all,length)
    #create the password
    password = "".join(temp)
    return password


async def getDashboardLoginData(domainname):
    connectionData = {}
    rpt = framework.context.context.get('rpt', {})
    connectionData["headers"] = {framework.settings.dashboard_header: 'reporting', 'Content-Type': 'application/json'}
    redisIns = await framework.redispool.get_redis_connection()
    password_key = f"{domainname}_{rpt.get('email', '-')}_kibanapassword"
    rawpassword = await redisIns.get(password_key)
    update_password = False
    if rawpassword:
        rawpassword = rawpassword.decode() if isinstance(rawpassword, bytes) else rawpassword
    else:
        rawpassword = _generateRandomPassword()
        update_password = True
    password = base64.b64encode(rawpassword.encode()).decode()
    connectionData["url"] = f"https://{domainname}/kibana/auth/login"
    connectionData["authenticationData"] = {'username': framework.ctx["tenant"] + "_kibana", 'password': password}
    if update_password:
        databaseuserdata = {"email": rpt.get('email', '-'), "attributes": {"includes": rpt.get('includes', ''),
                                                                           "excludes": rpt.get('excludes', '')}}
        keycloakusermgmt._createDatabaseUser(databaseuserdata, framework.ctx["tenant"], rawpassword)
    connectionData["authenticationData"] = {'username': rpt.get("email") + '_kibana', 'password': rawpassword}
    session = requests.Session()
    resp = session.post(connectionData['url'], data=json.dumps(connectionData['authenticationData']),
                        headers=connectionData['headers'], verify=False)
    if resp.status_code // 100 != 2:
        await asyncio.sleep(2)
        rawpassword = _generateRandomPassword()
        update_password = True
        databaseuserdata = {"email": rpt.get('email', '-'), "attributes": {"includes": rpt.get('includes', ''),
                                                                           "excludes": rpt.get('excludes', '')}}
        keycloakusermgmt._createDatabaseUser(databaseuserdata, framework.ctx["tenant"], rawpassword)
        connectionData["authenticationData"] = {'username': rpt.get("email") + '_kibana', 'password': rawpassword}
        session = requests.Session()
        resp = session.post(connectionData['url'], data=json.dumps(connectionData['authenticationData']),
                            headers=connectionData['headers'], verify=False)
    if resp.status_code // 100 == 2:
        if update_password:
            await redisIns.setex(password_key, 24 * 60 * 60, rawpassword)
        connectionData = session.cookies.get_dict()
        cookie_name = list(connectionData.keys())[0]
        cookie_id = list(connectionData.values())[0]
        response = fastapi.responses.JSONResponse({"status": "Configured"}, 200)
        response.set_cookie(cookie_name, cookie_id, expires=900, httponly=True, path="/kibana")
        return response
    return fastapi.responses.JSONResponse({"status": "Failed to login"}, 200)

