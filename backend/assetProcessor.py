import framework
import re
import os
import sys
import time
import uuid
import json
import copy
import math
import manuf
import redis
import base64
import socket
import asyncio
import netaddr
import requests
import datetime
import Helpers
import traceback
import json_flatten
import pandas as pd
import cybercns_enum
import cybercns_model
import ScoreEvaluator
import reportProcessor
import dateutil.parser
from io import StringIO
import agentCommunicator
#import AppBaseLineProcessor
import framework.queryparams
import framework.postgresmodel
from es_pandas import es_pandas
from elasticsearch import helpers
from difflib import SequenceMatcher
logger = framework.Logger.getInstance('assetprocessor')

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# this class is responsible for converting raw data from asset to elastic schema format

insecurePorts = [20, 21, 22, 23, 25, 53, 80, 139, 445, 1433, 1434, 1583, 3306, 3389, 3351, 5600, 5432, 6379, 9200, 27017]
ignore_ports = {445, 80, 443, 3389, 135}  # Ports to be ignored.


integration = {'active': True, 'name': 'new board', 'sbId': 19, 'sbTypeId': 89, 'sbSubTypeId': 130, 'new': 91, 'closed': 155, 'critical': 2, 'high': 1, 'medium': 4, 'low': 3, 'sbName': 'Alerts', 'credId': '5c41b09c-c979-4508-be53-e3307dbb3127', 'product': 'connectwise', 'family': 'integrations', 'species': 'ticketing', 'updated': 1618222478, 'created': 1618222478, '_id': '3gmTxXgBIY1ot-eIdf6z', 'Severity': 'High'}
settings = {'company': 'platform_c', 'domain': 'staging.connectwisedev.com', 'publicKey': 'QUwXmz3yZBC6dttd', 'privateKey': 'GhoM161Ms5bZI53R'}
suppress_rules = {}
if os.path.exists("meta/networkSupressRules.json"):
    with open("meta/networkSupressRules.json") as f:
        suppress_rules = json.load(f)


def getVendorIcon(vendor):
    vendor_icon = "generic.svg"
    if not vendor or vendor.lower() == "unknown":
        return vendor_icon
    df = pd.read_csv(f"vendors.csv")
    vendor = vendor.lower().strip().split(" ")[0]
    df = df[df["Vendor"].str.startswith(vendor[0])]
    matches = list(df["Vendor"])
    best = 0
    finalmatch = None
    for match in matches:
        m = SequenceMatcher(None, vendor, match)
        if m.ratio() > best:
            best = m.ratio()
            finalmatch = match
    vendor_icon_match = df[df["Vendor"] == finalmatch].to_dict(orient="records")
    if vendor_icon_match:
        vendor_icon = f"{vendor_icon_match[0]['Vendor']}.{vendor_icon_match[0]['Extension']}"
    return vendor_icon


def getESpandasConnection():
    dburl = [str(url) for url in framework.settings.db_urls["elastic"]]
    return es_pandas(dburl, timeout=600, use_ssl=True, verify_certs=False)


class AssetProcessor():
    # Interface to connect with central server and fetch required information
    # Get Api's are not allowed with central server
    def myconverter(self, o):
        if isinstance(o, datetime.datetime):
            return o.__str__()

    def _centralServer(self, url, doc):
        headers = {'X-Api-AccessKey': "", "Content-Type": "application/json"}
        try:
            resp = requests.post(
                "https://softwarerepo.my-netalytics.com" + url,
                headers=headers,
                data=json.dumps(doc, default=self.myconverter)
            )
        except Exception as e:
            logger.info("Exception in central server request %s" % e)
            return False, e
        if int(resp.status_code / 100) != 2:
            logger.info("Error in getting central server Status_code:- %s Resp:- %s" % (resp.status_code, resp.text))
            return False, "Error in getting central server Status_code:- %s Resp:- %s" % (resp.status_code, resp.text)
        data = resp.json()
        return True, data

    def _validate_ipAddress(self, IPAddress):
        try:
            netaddr.IPAddress(IPAddress)
            return True
        except:
            return False

    # Getting os information from nmapdata
    def _getOsinfo_Nmap(self, valuetosave):
        os_data = {}
        if valuetosave.ostype:
            os_data["platform"] = valuetosave.ostype
        if valuetosave.os:
            os_data["name"] = valuetosave.os
        if valuetosave.osversion:
            os_data["version"] = valuetosave.osversion
        return os_data

    # Getting host information from nmap data
    def _getHostInfo(self, valuetosave):
        # print(valuetosave.dict())
        host_data = {}
        if valuetosave.ip:
            if self._validate_ipAddress(valuetosave.ip):
                host_data['ip'] = valuetosave.ip
        icon = ""
        if valuetosave.mac and valuetosave.mac != "00:00:00:00:00:00" and \
                not valuetosave.mac.lower().startswith("no_mac"):
            valuetosave.mac = valuetosave.mac.upper()
            host_data['mac'] = valuetosave.mac

            if valuetosave.ostype and "windows" in valuetosave.ostype.lower():
                icon = "windows.svg"
            else:
                icon = manuf.MacParser().get_manuf(valuetosave.mac)
                icon = getVendorIcon(icon)
            vendor = manuf.MacParser().get_manuf_long(valuetosave.mac)
            if vendor:
                host_data["manufacturer"] = vendor
            if icon:
                host_data["icon"] = icon
        if not icon or icon == "generic.svg":
            if valuetosave.ostype and "windows" in valuetosave.ostype.lower():
                icon = "windows.svg"
            elif valuetosave.ostype and ('linux_kernel' in valuetosave.ostype.lower() or 'linux based os' in valuetosave.ostype.lower()):
                icon = "linux.svg"
            elif valuetosave.ostype:
                icon = getVendorIcon(valuetosave.ostype)
            if icon:
                host_data["icon"] = icon
        if valuetosave.assetName:
            host_data['host_name'] = valuetosave.assetName
        return host_data

    # Getting exact operating system details from central server and also converting fields to required format
    def _getOsInfo(self, valuetosave):
        if valuetosave["os"].get("build"):
            valuetosave["os"]["build"] = str(valuetosave["os"]["build"])
        if "install_date" in valuetosave["os"]:
            try:
                int(valuetosave["os"]["install_date"])
            except:
                del valuetosave["os"]["install_date"]
        if "version" in valuetosave["os"]:
            valuetosave["os"]["version"] = str(valuetosave["os"]["version"])
        full_name = valuetosave['os']['name']
        valuetosave['os']['full_name'] = full_name
        valuetosave['os']["patches"] = []
        if valuetosave.get('hotfixes'):
            valuetosave['os']['patches'] = valuetosave["hotfixes"]
        elif "patches" in valuetosave:
            valuetosave['os']['patches'] = [str(record['hotfix_id']) for record in valuetosave['patches']]
        status, resp = self._centralServer("/usermgmt/api/central_services/dummy/extract_os_info",
                                                           {"doc": {"os": valuetosave["os"]}})
        if status and resp:
            if resp.get("status") == "ok" and resp.get("msg"):
                resp = json_flatten.unflatten(resp["msg"])
                valuetosave['os'].update(resp.get("os", {}))

    # Convert osquery raw csv data to json structure
    def _convertCollectedData(self, event_data):
        finalResp = {}
        event_data = json.loads(event_data.encode('utf-8', 'ignore').decode('latin1', errors='ignore'))
        for key_, details in event_data.items():
            if not details['status'] or not details['data']:
                # todo:- need to log error output
                continue
            if key_ == "compliance":
                if isinstance(details, dict):
                    finalResp["compliance"] = details
                else:
                    try:
                        finalResp["compliance"] = json.loads(details)
                    except:
                        pass
                continue
            if key_ == "hotfixes":
                # print("Hot Fixes: %s" % details["data"])
                finalResp["hotfixes"] = details["data"]
                continue
            if key_ == "oscap":
                finalResp["oscap"] = details
                continue
            if len(details["data"]):
                ext = StringIO(details["data"])
                for f in pd.read_csv(ext, sep="|").fillna('').to_dict(orient='records'):
                    temp = json_flatten.unflatten(f)
                    for key, value in temp.items():
                        if key not in finalResp:
                            finalResp[key] = []
                        if isinstance(value, dict):
                            finalResp[key].append(value)
                        else:
                            # print(key, value)
                            finalResp[key].extend(value)
        if not finalResp:
            return {}
        if finalResp.get("host", []):
            finalResp["host"] = finalResp["host"][0]
        if finalResp.get("os", []):
            finalResp["os"] = finalResp["os"][0]
        return finalResp

    # Getting valid Packages from packages + applications
    def _filterPackages(self, package, application):
        skip_ = re.compile(r"^Update for|rollup|^Security Update|^HotFix", re.IGNORECASE)
        packages = []
        temp = {}
        #All packages
        for elem in package:
            temp[elem['name']]= elem
        
        #Application info with CPE details
        for elem in application:
            extra_pack_info = {}
            if temp.get(elem['full_name']):
                extra_pack_info = {
                            "publisher":temp[elem['full_name']]["publisher"],
                             "install_source":temp[elem['full_name']].get("install_source", ""),
                             "uninstall_string":temp[elem['full_name']].get("uninstall_string", ""),
                             "install_date":temp[elem['full_name']].get("install_date", ""),
                             "identifying_number":temp[elem['full_name']].get("identifying_number", "")
                            }
                #if application have empty version let fill it from packages            
                if not elem['version']:
                    extra_pack_info["version"] = temp[elem['full_name']].get("version", "")
            temp[elem['full_name']]= {**elem, **extra_pack_info}
        
        for x, y in temp.items():
            # skip microsoft update related products.
            if skip_.search(x):
                continue
            if not y.get('path'):
                y["path"] = y.get("install_source", "")
            packages.append(y)
        return packages

    # Getting valid interfaces from all interfaces
    def _filterValidInterfaces(self, ipdetails):
        interfaces = []
        for record in ipdetails:
            if not record.get('name') and record.get('interface'):
                record['name'] = record['interface']
            if not record.get('name') or record["name"].startswith("lo"):
                continue
            if record.get("address") in ["127.0.0.1", "::1"]:
                continue
            if record.get("address", "").startswith("169."):
                continue
            if record.get("mac") == "00:00:00:00:00:00":
                continue
            record["mac"] = record["mac"].upper()
            interfaces.append(record)
        return interfaces

    # getting ip and mac from valid interface
    def _fetchIpDetails(self, interfaces):
        mac = ip = ""
        for record in interfaces:
            if record.get("address") and ":" not in record["address"]:
                ip = record["address"]
            if record.get("mac") and record["mac"] != ["00:00:00:00:00:00"]:
                mac = record["mac"]
            if ip and mac:
                break
        return ip, mac

    # Checking whether the asset available in db or not
    # Todo:- need to add companyid in reference fields
    async def mergeAssets(self, asset_ins, matched_assets, domain):
        if len(matched_assets) == 0:
            return {}
        if len(matched_assets) == 1:
            return list(matched_assets.values())[0]
        assetPriority = {}
        lastvul_scannedtime = "0"
        lastdiscoveredtime = "0"
        protocols_count = 0
        idtokeep = ''
        for _id, asset in matched_assets.items():
            if 'LIGHTWEIGHTAGENT' in asset.get('discoveredProtocols', []):
                assetPriority[1] = _id
                continue
            if asset.get('lastvul_scannedtime'):
                if asset['lastvul_scannedtime'] > lastvul_scannedtime:
                    assetPriority[2] = _id
                    lastvul_scannedtime = asset['lastvul_scannedtime']
                    continue
                if "AD" in asset.get('discoveredProtocols', []):
                    assetPriority[3] = _id
                    continue
            if asset.get('lastdiscoveredtime') and asset['lastdiscoveredtime'] > lastdiscoveredtime:
                assetPriority[4] = _id
                lastdiscoveredtime = asset['lastdiscoveredtime']
                continue
            if len(asset.get('discoveredProtocols', [])) > protocols_count:
                protocols_count = len(asset.get('discoveredProtocols', []))
                assetPriority[5] = _id
                continue
        if len(assetPriority) > 0:
            priority_index = list(assetPriority.keys())
            priority_index.sort()
            idtokeep = assetPriority[priority_index[0]]
        else:
            idtokeep = list(matched_assets.keys())[0]
        if idtokeep:
            for _id, asset in matched_assets.items():
                if _id != idtokeep:
                    await asset_ins.delete(_id, cyberTenant=domain)
        return matched_assets.get(idtokeep, {})


    async def verifyHostname(self, asset_ins, assetName, company_id, domain=None):
        must_expression = [{"exists": {"field": "host.ip"}}]
        must = {"host.host_name.keyword": assetName, "companyRef.id.keyword": company_id}
        query = Helpers.buildElsQuery(must, mustExpression=must_expression)
        query['fields'] = ["host"]
        client = await asset_ins.client()
        response = await client.search(index=await asset_ins.collection_name(domain=domain), body=query)
        assets = [{**record['_source'], **{"_id": record["_id"]}} for record in
                  response.get('hits', {}).get("hits", [])]
        matched_assets = []
        for asset in assets:
            matched_assets.append(asset)
        # if len(assets) > 0:
        #     return assets
        # must = {"host.host_name": assetName.split(".")[0].lower(), "companyRef.id.keyword": company_id}
        must = {"companyRef.id.keyword": company_id}
        must_expression.append({"query_string":{"query": f"*{assetName.split('.')[0].lower()}*", "fields": ["host.host_name"]}})
        query = Helpers.buildElsQuery(must, mustExpression=must_expression)
        # query['fields'] = ["host"]
        response = await client.search(index=await asset_ins.collection_name(domain=domain), body=query)
        assets = [{**record['_source'], **{"_id": record["_id"]}} for record in
                  response.get('hits', {}).get("hits", [])]
        matched_assets = []
        for asset in assets:
            if asset['host']['host_name'].split(".")[0].lower() == assetName.split(".")[0].lower():
                matched_assets.append(asset)
        return matched_assets

    async def checkAssetExists(self, asset_ins, host_data, interfaces, company_id, assetData, domain=None):
        must_expression = {"exists": {"field": "host.ip"}}
        params = framework.queryparams.QueryParams()
        params.limit = 10
        params.skip = 0
        matched_assets = {}
        if host_data["host"].get("mac"):
            query = Helpers.buildElsQuery({"host.mac.keyword": host_data["host"]["mac"], "companyRef.id.keyword": company_id}, mustExpression=must_expression)
            params.q = json.dumps(query)
            response = await asset_ins.get_all(params, cyberTenant=domain)
            if response.get('count'):
                for asset in response['data']:
                    if asset['_id'] not in matched_assets:
                        matched_assets[asset['_id']] = asset
        if host_data["host"].get("host_name"):
            resp = await self.verifyHostname(asset_ins, host_data["host"].get("host_name"), company_id, domain)
            for asset in resp:
                if asset['_id'] not in matched_assets:
                    matched_assets[asset['_id']] = asset
        for interface in interfaces:
            if interface.get("mac"):
                query = Helpers.buildElsQuery({"host.mac.keyword": interface["mac"], "companyRef.id.keyword": company_id},
                                              mustExpression=must_expression)
                params.q = json.dumps(query)
                response = await asset_ins.get_all(params, cyberTenant=domain)
                for asset in response['data']:
                    if asset['_id'] not in matched_assets:
                        matched_assets[asset['_id']] = asset
        # Checking ip based asset query if none of the above are matching
        if len(matched_assets) == 0:
            if host_data["host"]["ip"]:
                query = Helpers.buildElsQuery({"host.ip.keyword": host_data["host"]["ip"], "companyRef.id.keyword": company_id},
                                              mustExpression=must_expression)
                params.q = json.dumps(query)
                response = await asset_ins.get_all(params, cyberTenant=domain)
                for asset in response['data']:
                    if asset['_id'] not in matched_assets:
                        matched_assets[asset['_id']] = asset
            for interface in interfaces:
                if interface.get("address"):
                    query = Helpers.buildElsQuery({"host.ip.keyword": interface["address"], "companyRef.id.keyword": company_id},
                                                  mustExpression=must_expression)
                    params.q = json.dumps(query)
                    response = await asset_ins.get_all(params, cyberTenant=domain)
                    for asset in response['data']:
                        if asset['_id'] not in matched_assets:
                            matched_assets[asset['_id']] = asset
        return await self.mergeAssets(asset_ins, matched_assets, domain)

    async def getVulnerabilities(self, ep, vul_ins, prog_ins, remediation_ins, remsupress_ins, reference, assetData, installed_programs, oscap_data, domain=None):
        start_time = datetime.datetime.utcnow()
        if assetData['host'].get('discovered'):
            del assetData['host']['discovered']
        vul_stats = assetData.get("vul_stats", {})
        vul_stats['count_of_installed_softwares'] = len(installed_programs)
        vul_stats_timeseries = {}
        vulnerability = {}
        remediationPlan = {}
        params = framework.queryparams.QueryParams()
        params.limit = 10000
        params.skip = 0
        query = Helpers.buildElsQuery({"assetRef.id.keyword": reference['assetRef']['id']}, mustExpression=[{"exists": {"field": "version"}}, {"exists": {"field": "publisher"}}], shouldExpression=[{"exists": {"field": "name"}}, {"exists": {"field": "full_name"}}])
        params.q = json.dumps(query)
        basedata = {"assetRef": reference['assetRef'], "agentRef": reference["agentRef"], "companyRef": reference["companyRef"]}
        installed_programs_old = await prog_ins.get_all(params, cyberTenant=domain)
        # print(installed_programs_old)
        # return [[], []]
        installed_programs_old = {program.get('full_name', program['name']): program['_id'] for program in installed_programs_old['data']}
        new_programs = []
        modified_programs = []
        for program in installed_programs:
            if not program.get('name') and not program.get('full_name'):
                continue
            program.update(copy.deepcopy(basedata))
            if not program.get('name'):
                program['name'] = program['full_name']
            if not program.get('full_name'):
                program['full_name'] = program['name']
            if program['full_name'] in installed_programs_old:
                program['_id'] = installed_programs_old[program['full_name']]
                modified_programs.append(program)
            else:
                new_programs.append(program)
        deleted_programs = list(set(list(installed_programs_old.keys())) - set([program['full_name'] for program in installed_programs if program.get('full_name')]))
        deleted_programs = [installed_programs_old[key] for key in deleted_programs]

        query = Helpers.buildElsQuery({"assetRef.id.keyword": reference['assetRef']['id']},
                                      mustExpression=[{"exists": {"field": "assetRef.id"}}, {"exists": {"field": "score.base_score"}}, {"range": {"score.base_score": {"gt": 0}}}])

        params.q = json.dumps(query)
        responseData = await vul_ins().get_all(params, cyberTenant=domain)
        # discovered_vulnerabilities = {record['vul_id']: record['_id'] for record in responseData['data']}
        duplicateVuls = {}
        for record in responseData['data']:
            if record['vul_id'] not in duplicateVuls:
                duplicateVuls[record['vul_id']] = [record['_id']]
            else:
                duplicateVuls[record['vul_id']].append(record['_id'])
        removedIds = []
        for _, ids in duplicateVuls.items():
            if len(ids) == 1:
                continue
            else:
                for id in ids[1:]:
                    removedIds.append(id)
        discovered_vulnerabilities = {record['vul_id']: record['_id'] for record in responseData['data'] if
                                      record['_id'] not in removedIds}
        query = Helpers.buildElsQuery({"assetRef.id.keyword": reference['assetRef']['id'], "remediation_status": False},
                                      must_not={"is_mandatory_application": True, "is_denied_application": True},
                                      mustExpression=[{"exists": {"field": "assetRef.id"}}, {"exists": {"field": "remediation_status"}}])
        params.q = json.dumps(query)
        responseData = await vul_ins().get_all(params, cyberTenant=domain)
        discovered_remediations = {record['product']+"_"+record["fix"]: record for record in responseData['data']}
        doc = {"os": assetData["os"], "packages": [program for program in installed_programs if program.get('name')], "host": assetData["host"], "oscap": oscap_data}
        apistart = datetime.datetime.utcnow()
        errmsg = ""
        status = False
        resp = {}
        if doc['os'].get('platform') in ['linux', 'ubuntu', 'rhel', 'debian']:
            if not oscap_data or 'ovalOutput' not in oscap_data:
                installCommand = "apt-get install libopenscap8 -y" if doc['os'].get('platform') in ["ubuntu", "debian"] else "yum install openscap scap-security-guide openscap-scanner -y"
                errmsg = f"Openscap not available, Please install openscap by running {installCommand} and initiate scan."
                resp = {"status": "error"}
        if len(errmsg) == 0:
            status, resp = self._centralServer("/usermgmt/api/central_services/dummy/find_vulnerabilities", {"doc": doc})
        apiend = datetime.datetime.utcnow()
        c = u = datetime.datetime.utcnow()
        if not status or resp["status"] != "ok":
            classname = prog_ins().getclassname()
            indexName = await prog_ins().collection_name(domain=domain)
            bulk_data_create = [{**prog_ins(**x).to_elastic(exclude_unset=False, exclude_none=True),
                              **{"c": c, "u": u, '_type_': classname}} for x in new_programs]
            bulk_data_update = [{**prog_ins(**x).to_elastic(exclude_unset=False, exclude_none=True),
                              **{"u": u, '_type_': classname}} for x in modified_programs]
            if bulk_data_create:
                ep.to_es(pd.DataFrame(bulk_data_create), indexName, doc_type='_doc')
            if bulk_data_update:
                df = pd.DataFrame(bulk_data_update)
                df['index'] = df['_id']
                df.set_index('index', drop=True, inplace=True)
                df.drop(['_id'], axis=1, inplace=True)
                ep.to_es(df, indexName, doc_type='_doc', _op_type='update')
            if len(errmsg) == 0:
                return True, vul_stats, "Sucess"
            else:
                return False, vul_stats, errmsg
        else:
            for sev in ['critical', 'high', 'medium', 'low', 'security feature bypass', 'important', 'moderate']:
                vul_stats.update(
                    {f"count_of_{sev}_vuls": 0, f"count_of_{sev}_vuls_new": 0, f"count_of_{sev}_installed_softwares": 0})
            basedata = {"assetRef": reference['assetRef'],
                        "agentRef": reference["agentRef"],
                        "companyRef": reference["companyRef"]}
            logger.info("Vuls Count %s Remediation Count %s" % (len(resp['msg']['cve_info']), len(resp['msg']['remediation'])))
            # print(resp["msg"])
            # print(json.dumps(resp['msg']['cve_info']))
            products_vul = {}
            softwares_vuls = {"critical": [], 'high': [], 'medium': [], "low": [],"important": [],"moderate":[]}
            already_discovered_val = []
            for vul in resp['msg']['cve_info']:
                vul = json_flatten.unflatten(vul)
                vul = vul['vulnerability']
                vul.update(copy.deepcopy(basedata))
                if vul['vul_id'] in already_discovered_val or vul.get('score', {}).get('base_score', 0) == 0:
                    continue
                already_discovered_val.append(vul['vul_id'])
                if vul['vul_id'] in discovered_vulnerabilities:
                    vul['_id'] = discovered_vulnerabilities[vul['vul_id']]
                vulnerability[vul['vul_id']] = vul
                if f"count_of_{vul['severity'].lower()}_vuls" not in vul_stats:
                    vul_stats[f"count_of_{vul['severity'].lower()}_vuls"] = 0
                vul_stats[f"count_of_{vul['severity'].lower()}_vuls"] += 1
                if vul.get('product'):
                    if vul['severity'].lower() not in softwares_vuls:
                        continue
                    softwares_vuls[vul['severity'].lower()].extend(vul["product"])
                for product in vul["product"]:
                    if product not in products_vul:
                        products_vul[product] = {"critical":0,"high":0,"medium":0,"low":0, "defense in depth":0,"important":0,"moderate":0}
                    if vul["severity"].lower() not in products_vul[product]:
                        products_vul[product][vul["severity"].lower()] = 0
                    products_vul[product][vul["severity"].lower()] += 1

            if resp['msg'].get('cve_info'):
                max_base_score = max(resp['msg']['cve_info'], key=lambda x: x['vulnerability.score.base_score'])['vulnerability.score.base_score']
            else:
                max_base_score = 0

            if resp['msg'].get('cve_info'):
                max_exp_score = max(resp['msg']['cve_info'], key=lambda x: x['vulnerability.score.exploit_score'])['vulnerability.score.exploit_score']
            else:
                max_exp_score = 0

            if math.isnan(max_base_score):
                max_base_score = 0
            vul_risk = 0
            if max_base_score and max_exp_score:
                vul_risk = (max_base_score * 5) + (max_exp_score * 2) + (assetData["host"]["importance"] / 10) * 3
            vul_stats['risk_score'] = vul_risk
            vul_stats['base_score'] = max_base_score
            for sev, products in softwares_vuls.items():
                vul_stats[f"count_of_{sev}_installed_softwares"] = len(list(set(products)))
            basedata = {"assetRef": reference['assetRef'],
                        "agentRef": reference["agentRef"],
                        "companyRef": reference["companyRef"]}
            for remediation in resp['msg']['remediation']:
                remediationId = remediation['product']+"_"+remediation["fix"]
                if remediationId in discovered_remediations:
                    remediation['_id'] = discovered_remediations[remediationId]['_id']
                query = Helpers.buildElsQuery({"product.keyword": remediation["product"]},
                                              mustExpression=[{"exists": {"field": "remediationdays"}}],
                                              should={f"{key}.id.keyword": [value['id']] for key, value in basedata.items()})
                # print(query)
                params = framework.queryparams.QueryParams()
                params.limit = 10000
                params.skip = 0
                params.q = json.dumps(query)
                remediation_data = await remsupress_ins.get_all(params, cyberTenant=domain)
                is_allowed = True
                for record in remediation_data['data']:
                    # print(record)
                    if (datetime.datetime.utcnow() - dateutil.parser.parse(record['c'])).days > record['remediationdays']:
                        continue
                    if record.get('version'):
                        if Helpers.version_compare(record['version'], remediation.get("evidence", {}).get('version', '')) in [">", "="]:
                            is_allowed = False
                            break
                        else:
                            continue
                    else:
                        is_allowed = False
                        break
                if not is_allowed:
                    continue
                remediation["vulcount"] = sum(list(products_vul.get(remediation["product"], {}).values()))
                for key in ['critical', 'high', "medium", "low"]:
                    remediation[key+'_vuls_count'] = products_vul.get(remediation["product"], {}).get(key, 0)
                remediation["remediation_status"] = False
                remediation.update(copy.deepcopy(basedata))
                remediationPlan[remediationId] = remediation
            # print(remediationPlan)
            # {'fix': 'Install Latest Apple Security Updates', 'product': 'MacOS Catalina', 'url': 'https://support.apple.com/en-us/HT201222'}
        new_rems = [record for _, record in remediationPlan.items() if '_id' not in record]
        modified_rems = [record for _, record in remediationPlan.items() if '_id' in record]
        deleted_rems = list(set(list(discovered_remediations.keys())) - set(list(remediationPlan.keys())))
        for rem in deleted_rems:
            record = discovered_remediations[rem]
            record['remediation_status'] = True
            record['remediation_closer_reason'] = "Software updated to the latest version"
            modified_rems.append(record)
        new_vuls = [record for _, record in vulnerability.items() if '_id' not in record]
        for record in new_vuls:
            vul_stats[f"count_of_{record['severity'].lower()}_vuls_new"] += 1
        modified_vuls = [record for _, record in vulnerability.items() if '_id' in record]
        deleted_vuls = list(set(list(discovered_vulnerabilities.keys())) - set(list(vulnerability.keys())))
        deleted_vuls = [discovered_vulnerabilities[key] for key in deleted_vuls]
        response = [[new_programs, modified_programs, deleted_programs], [new_vuls, modified_vuls, deleted_vuls], [new_rems, modified_rems, deleted_rems]]
        if response:
            if response[0]:
                for program in response[0][0]:
                    if program.get('cpe_vendor') and program['cpe_vendor'] in products_vul:
                        for key in ['critical', 'high', "medium", "low"]:
                            program[key + '_vuls_count'] = products_vul.get(program['cpe_vendor'], {}).get(key, 0)
                        program["vulcount"] = sum([program.get(key + '_vuls_count', 0) for key in ['critical', 'high', "medium", "low"]])
                    elif program.get('name') and program['name'] in products_vul:
                        for key in ['critical', 'high', "medium", "low"]:
                            program[key + '_vuls_count'] = products_vul.get(program['name'], {}).get(key, 0)
                        program["vulcount"] = sum([program.get(key + '_vuls_count', 0) for key in ['critical', 'high', "medium", "low"]])
                    else:
                        for key in ['critical', 'high', "medium", "low"]:
                            program[key + '_vuls_count'] = 0
                        program["vulcount"] = sum([program.get(key + '_vuls_count', 0) for key in ['critical', 'high', "medium", "low"]])
                for program in response[0][1]:
                    if program.get('cpe_vendor') and program['cpe_vendor'] in products_vul:
                        for key in ['critical', 'high', "medium", "low"]:
                            program[key + '_vuls_count'] = products_vul.get(program['cpe_vendor'], {}).get(key, 0)
                        program["vulcount"] = sum([program.get(key + '_vuls_count', 0) for key in ['critical', 'high', "medium", "low"]])
                    elif program.get('name') and program['name'] in products_vul:
                        for key in ['critical', 'high', "medium", "low"]:
                            program[key + '_vuls_count'] = products_vul.get(program['name'], {}).get(key, 0)
                        program["vulcount"] = sum([program.get(key + '_vuls_count', 0) for key in ['critical', 'high', "medium", "low"]])
                    else:
                        for key in ['critical', 'high', "medium", "low"]:
                            program[key + '_vuls_count'] = 0
                        program["vulcount"] = sum([program.get(key + '_vuls_count', 0) for key in ['critical', 'high', "medium", "low"]])
                classname = prog_ins().getclassname()
                bulk_data_create = []
                bulk_data_update = []
                indexName = await prog_ins().collection_name(domain=domain)
                bulk_data_create = [{**prog_ins(**x).to_elastic(exclude_unset=False, exclude_none=True),
                                          **{"c": c, "u": u, '_type_': classname}} for x in response[0][0]]
                bulk_data_update = [{**prog_ins(**x).to_elastic(exclude_unset=False, exclude_none=True),
                                          **{"u": u, '_type_': classname, '_id': x['_id']}} for x in response[0][1]]
                deleted_records = [{"_id": x} for x in response[0][2]]
                if bulk_data_create:
                    ep.to_es(pd.DataFrame(bulk_data_create), indexName, doc_type='_doc', show_progress=False)
                if bulk_data_update:
                    df = pd.DataFrame(bulk_data_update)
                    df['index'] = df['_id']
                    df.set_index('index', drop=True, inplace=True)
                    df.drop(['_id'], axis=1, inplace=True)
                    ep.to_es(df, indexName, doc_type='_doc', _op_type='update', show_progress=False)
                if deleted_records:
                    try:
                        df = pd.DataFrame(deleted_records)
                        df.set_index('_id', drop=True, inplace=True)
                        ep.to_es(df, indexName, doc_type='_doc', _op_type='delete', show_progress=False)
                    except Exception as e:
                        print(f"Exception in deleting installed programs {e}")
            if response[1]:
                classname = vul_ins().getclassname()
                indexName = await vul_ins().collection_name(domain=domain)
                bulk_data_create = [{**vul_ins(**x).to_elastic(exclude_unset=False, exclude_none=True),
                                          **{"c": c, "u": u, '_type_': classname}} for x in response[1][0]]
                bulk_data_update = [{**vul_ins(**x).to_elastic(exclude_unset=False, exclude_none=True),
                                          **{"u": u, '_type_': classname, '_id': x['_id']}} for x in response[1][1]]
                deleted_records = [{"_id": x} for x in list(set((response[1][2] + removedIds)))]
                if bulk_data_create:
                    ep.to_es(pd.DataFrame(bulk_data_create), indexName, doc_type='_doc', show_progress=False)
                if bulk_data_update:
                    df = pd.DataFrame(bulk_data_update)
                    df['index'] = df['_id']
                    df.set_index('index', drop=True, inplace=True)
                    df.drop(['_id'], axis=1, inplace=True)
                    ep.to_es(df, indexName, doc_type='_doc', _op_type='update', show_progress=False)
                if deleted_records:
                    try:
                        df = pd.DataFrame(deleted_records)
                        df.set_index('_id', drop=True, inplace=True)
                        ep.to_es(df, indexName, doc_type='_doc', _op_type='delete',
                                 show_progress=False)
                    except Exception as e:
                        print(f"Exception in deleting vulnerabilities {e}")
            if response[2]:
                params = framework.queryparams.QueryParams()
                params.limit = 10000
                params.skip = 0
                query = Helpers.buildElsQuery({"assetRef.id.keyword": reference['assetRef']['id'],
                                               "companyRef.id.keyword": reference["companyRef"]['id']
                                              },
                                              mustExpression=[{"exists": {"field": "version"}},
                                                              {"exists": {"field": "publisher"}}],
                                              shouldExpression=[{"exists": {"field": "name"}},
                                                                {"exists": {"field": "full_name"}}])
                params.q = json.dumps(query)
                basedata = {"assetRef": reference['assetRef'], "agentRef": reference["agentRef"],
                            "companyRef": reference["companyRef"]}
                installed_programs = await prog_ins.get_all(params, cyberTenant=domain)
                installed_programs = {program["name"]: program["_id"] for program in installed_programs["data"]}
                await self.verifyRemediationPlan(remediation_ins, response[2][0], reference, installed_programs, domain=domain)
                # tmpData = [await remediation_ins(**x).create() for x in response[2][0]]
                for remediation in response[2][1]:
                    if remediation["product"] in installed_programs:
                        remediation["evidence"].update({"productRef": installed_programs[remediation["product"]]})
                classname = remediation_ins().getclassname()
                indexName = await remediation_ins().collection_name(domain=domain)
                bulk_data_update = [{**remediation_ins(**x).to_elastic(exclude_unset=False, exclude_none=True),
                                          **{"u": u, '_type_': classname, '_id': x['_id']}} for x in response[2][1]]
                if bulk_data_update:
                    df = pd.DataFrame(bulk_data_update)
                    df['index'] = df['_id']
                    df.set_index('index', drop=True, inplace=True)
                    df.drop(['_id'], axis=1, inplace=True)
                    ep.to_es(df, indexName, doc_type='_doc', _op_type='update', show_progress=False)
        # Processing Application Baseline
        # try:
        #     ap = AppBaseLineProcessor.AppBaseLineProcessor()
        #     await ap.company_rule_processor(reference['companyRef']['id'], domain)
        # except Exception as e:
        #     logger.info("Error in processing application baseline:%s" % e)
        end_time = datetime.datetime.utcnow()
        # print(f"Took {(end_time - start_time).seconds} Seconds For vuls function {(apiend - apistart).seconds} Seconds For vuls api")
        return True, vul_stats, "Sucess"

    # Verifying remediation plan if already closed for same version re-opening it else creating new one
    async def verifyRemediationPlan(self, remediation_ins, remediation_plans, reference, programs, domain=None):
        for remediation in remediation_plans:
            if remediation["product"] in programs:
                if not remediation["evidence"]:
                    remediation["evidence"] = {}
                remediation["evidence"].update({"productRef": programs[remediation["product"]]})
            if remediation.get("fix"):
                query = Helpers.buildElsQuery({"assetRef.id.keyword": reference['assetRef']['id'], "remediation_status": True,
                                               "product.keyword": remediation["product"], "fix.keyword": remediation["fix"]},
                                          mustExpression=[{"exists": {"field": "assetRef.id"}}, {"exists": {"field": "remediation_status"}}])
                params = framework.queryparams.QueryParams()
                params.limit = 1
                params.skip = 0
                params.q = json.dumps(query)
                params.sort = json.dumps([{"u": {"order": "desc"}}])
                resp = await remediation_ins.get_all(params, cyberTenant=domain)
                if resp["data"]:
                    remediation['_id'] = resp['data'][0]['_id']
                    await remediation_ins(**remediation).update(cyberTenant=domain)
                    continue
            await remediation_ins(**remediation).create(cyberTenant=domain)


    async def saveNoauthVulnerabilities(self, ep, vul_ins, prog_ins, reference, noAuthVuls_, networkPortVersions, agenttype, domain=None):
        # print(noAuthVuls)
        vulstats = {"count_of_critical_network_vuls": 0, "count_of_high_network_vuls": 0,
                    "count_of_medium_network_vuls": 0, "count_of_low_network_vuls": 0,
                    "count_of_info_network_vuls": 0}
        logger.info("No Auth Vuls %s" % len(noAuthVuls_))
        noAuthVuls = []
        if suppress_rules:
            for vul in noAuthVuls_:
                # print(vul.shortName)
                issuppressed = False
                if vul.shortName in suppress_rules:
                    vul_data = vul.dict()
                    # print(vul_data)
                    for key, value in suppress_rules.get("matches", {}).items():
                        if key not in vul_data or vul_data[key] != value:
                            issuppressed = True
                            break
                if issuppressed == False:
                    noAuthVuls.append(vul)
        else:
            noAuthVuls = noAuthVuls_

        params = framework.queryparams.QueryParams()
        params.limit = 10000
        params.skip = 0
        query = Helpers.buildElsQuery({"assetRef.id.keyword": reference['assetRef']['id']},
                                      mustExpression=[{"exists": {"field": "assetRef.id"}},
                                                      {"exists": {"field": "score.cvss_score"}},
                                                      {"exists": {"field": "port"}},
                                                      {"range": {"port": {"gt": 0}}}])
        params.q = json.dumps(query)
        responseData = await vul_ins().get_all(params, cyberTenant=domain)
        duplicateVuls = {}
        for record in responseData['data']:
            if record['vul_id'] not in duplicateVuls:
                duplicateVuls[record['vul_id']] = [record['_id']]
            else:
                duplicateVuls[record['vul_id']].append(record['_id'])
        removedIds = []
        for _, ids in duplicateVuls.items():
            if len(ids) == 1:
                continue
            else:
                for id in ids[1:]:
                    # await vul_ins().delete(id, cyberTenant=domain)
                    removedIds.append(id)
        discovered_vulnerabilities = {record['vul_id']: record['_id'] for record in responseData['data'] if record['_id'] not in removedIds}
        # print(json.dumps([vul['vul_id'] for vul in resp['msg']['cve_info']]))
        basedata = {"assetRef": reference['assetRef'],
                    "agentRef": reference["agentRef"],
                    "companyRef": reference["companyRef"]}
        vulnerability = {}
        for record in noAuthVuls:
            vulstats[f'count_of_{record.severity.lower()}_network_vuls'] += 1
            vul = {"vul_id": record.shortName, "category": record.category, "severity": record.severity.title(), "title": record.title}
            if record.result:
                vul['ref'] = record.result
            if record.port:
                vul["port"] = record.port
            if record.cvss:
                vul["score"] = {"cvss_score": record.cvss}
            else:
                vul["score"] = {"cvss_score": 0}
            if record.product:
                vul["product"] = [record.product]

            if vul['vul_id'] in discovered_vulnerabilities:
                vul["_id"] = discovered_vulnerabilities[vul['vul_id']]
            vul.update(copy.deepcopy(basedata))
            vulnerability[record.shortName] = vul
        bulk_data = []
        delete_ids = []
        u = c = datetime.datetime.utcnow()
        if networkPortVersions:
            vuls_doc = [{"name": rec["name"], "version": rec["version"]} for rec in list(networkPortVersions.values())]
            portmap = {rec["name"]: {"port": port, "ref": rec["ref"]} for port, rec in networkPortVersions.items()}
            port_vuls = {}
            for _, vul in vulnerability.items():
                if not vul.get('port') or not vul.get("severity") or vul["severity"].lower() == 'info':
                    continue
                if vul["port"] not in port_vuls:
                    port_vuls[vul["port"]] = {"vulcount": 0}
                    for key in ['critical', 'high', "medium", "low"]:
                        port_vuls[vul["port"]][key + '_vuls_count'] = 0
                port_vuls[vul["port"]]['vulcount'] += 1
                port_vuls[vul["port"]][vul['severity'].lower() + '_vuls_count'] += 1
            status, resp = self._centralServer("/usermgmt/api/central_services/dummy/application_vulnerabilities", {"doc": vuls_doc})
            if status and resp['msg'].get('cve_info'):
                for record in resp['msg']['cve_info']:
                    record = json_flatten.unflatten(record)['vulnerability']
                    if record['vul_id'] in vulnerability:
                        continue
                    vulstats[f'count_of_{record["severity"].lower()}_network_vuls'] += 1
                    vul = {"vul_id": record['vul_id'], "category": "Discovered Remote Service Version", "severity": record['severity'].title(),
                           "title": record['vul_id'], "port": int(portmap[record["product"][0]]["port"]),
                           "score": {"cvss_score": record["score"]["base_score"]},
                           "product": record["product"], "ref": portmap[record["product"][0]]["ref"]}
                    vul.update(copy.deepcopy(basedata))
                    if vul['vul_id'] in discovered_vulnerabilities:
                        vul["_id"] = discovered_vulnerabilities[vul['vul_id']]
                    vulnerability[vul['vul_id']] = vul
                    if vul["port"] not in port_vuls:
                        port_vuls[vul["port"]] = {"vulcount": 0}
                        for key in ['critical', 'high', "medium", "low"]:
                            port_vuls[vul["port"]][key + '_vuls_count'] = 0
                    port_vuls[vul["port"]]['vulcount'] += 1
                    port_vuls[vul["port"]][record['severity'].lower() + '_vuls_count'] += 1
            if agenttype == 4:
                params = framework.queryparams.QueryParams()
                params.limit = 10000
                params.skip = 0
                query = Helpers.buildElsQuery({"assetRef.id.keyword": reference['assetRef']['id']},
                                              mustExpression=[{"exists": {"field": "version"}},
                                                              {"exists": {"field": "publisher"}}],
                                              shouldExpression=[{"exists": {"field": "name"}},
                                                                {"exists": {"field": "full_name"}}])
                params.q = json.dumps(query)
                basedata = {"assetRef": reference['assetRef'], "agentRef": reference["agentRef"],
                            "companyRef": reference["companyRef"]}
                installed_programs_old = await prog_ins.get_all(params, cyberTenant=domain)
                installed_programs_old = {program['full_name']: program['_id'] for program in
                                          installed_programs_old['data']}
                new_programs = []
                modified_programs = []
                for program in list(networkPortVersions.values()):
                    if not program.get('name') and not program.get('full_name'):
                        continue
                    program.update(port_vuls.get(program["port"], {}))
                    program.update(copy.deepcopy(basedata))
                    if not program.get('name'):
                        program['name'] = program['full_name']
                    if not program.get('full_name'):
                        program['full_name'] = program['name']
                    if program['full_name'] in installed_programs_old:
                        program['_id'] = installed_programs_old[program['full_name']]
                        modified_programs.append(program)
                    else:
                        new_programs.append(program)
                deleted_programs = list(set(list(installed_programs_old.keys())) - set(
                    [program['full_name'] for _, program in networkPortVersions.items() if program.get('full_name')]))
                classname = prog_ins().getclassname()
                indexName = await prog_ins().collection_name(domain=domain)
                bulk_data_create = [{**prog_ins(**x).to_elastic(exclude_unset=False, exclude_none=True),
                                     **{"c": c, "u": u, '_type_': classname}} for x in new_programs]
                bulk_data_update = [{**prog_ins(**x).to_elastic(exclude_unset=False, exclude_none=True),
                                     **{"u": u, '_type_': classname, '_id': x['_id']}} for x in modified_programs]
                if bulk_data_create:
                    ep.to_es(pd.DataFrame(bulk_data_create), indexName, doc_type='_doc', show_progress=False)
                if bulk_data_update:
                    df = pd.DataFrame(bulk_data_update)
                    df['index'] = df['_id']
                    df.set_index('index', drop=True, inplace=True)
                    df.drop(['_id'], axis=1, inplace=True)
                    ep.to_es(df, indexName, doc_type='_doc', _op_type='update', show_progress=False)
                if deleted_programs:
                    df = pd.DataFrame([{'_id': installed_programs_old[key]} for key in deleted_programs])
                    df.set_index('_id', drop=True, inplace=True)
                    try:
                        ep.to_es(df, indexName, doc_type='_doc', _op_type='delete', show_progress=False)
                    except Exception as e:
                        pass
        new_vuls = [record for _, record in vulnerability.items() if '_id' not in record]
        modified_vuls = [record for _, record in vulnerability.items() if '_id' in record]
        deleted_vuls = list(set(list(discovered_vulnerabilities.keys())) - set(list(vulnerability.keys())))
        deleted_vuls = [discovered_vulnerabilities[key] for key in deleted_vuls]
        classname = vul_ins().getclassname()
        indexName = await vul_ins().collection_name(domain)
        bulk_data_create = [{**vul_ins(**x).to_elastic(exclude_unset=False, exclude_none=True),
                             **{"c": c, "u": u, '_type_': classname}} for x in new_vuls]
        bulk_data_update = [{**vul_ins(**x).to_elastic(exclude_unset=False, exclude_none=True),
                             **{"u": u, '_type_': classname, '_id': x['_id']}} for x in modified_vuls]
        if bulk_data_create:
            ep.to_es(pd.DataFrame(bulk_data_create), indexName, doc_type='_doc', show_progress=False)
        if bulk_data_update:
            df = pd.DataFrame(bulk_data_update)
            df['index'] = df['_id']
            df.set_index('index', drop=True, inplace=True)
            df.drop(['_id'], axis=1, inplace=True)
            ep.to_es(df, indexName, doc_type='_doc', _op_type='update', show_progress=False)
        if deleted_vuls:
            df = pd.DataFrame([{'_id': key} for key in deleted_vuls + removedIds])
            df.set_index('_id', drop=True, inplace=True)
            try:
                ep.to_es(df, indexName, doc_type='_doc', _op_type='delete', show_progress=False)
            except Exception as e:
                pass
        return vulstats, list(vulnerability.values())


    async def saveRecords(self, ep, queryPoints, records_ins, reference, records, domain=None, isUpdate=False):
        records = [record.dict() if not isinstance(record, dict) else record for record in records if record]
        params = framework.queryparams.QueryParams()
        params.limit = 10000
        params.skip = 0
        query_raw = {"must": {"assetRef.id.keyword": reference['assetRef']['id']}}
        if queryPoints.get("exists"):
            if queryPoints["exists"].get("must"):
                query_raw["mustExpression"] = [{"exists": {"field": field}} for field in queryPoints["exists"]["must"]]
            if queryPoints["exists"].get("should"):
                query_raw["shouldExpression"] = [{"exists": {"field": field}} for field in queryPoints["exists"]["should"]]
        query = Helpers.buildElsQuery(**query_raw)
        params.q = json.dumps(query)
        basedata = {f"assetRef": reference['assetRef'],
                    f"agentRef": reference["agentRef"],
                    f"companyRef": reference["companyRef"]}
        for interface in records:
            interface.update(copy.deepcopy(basedata), cyberTenant=domain)
        records_old = await records_ins().get_all(params, cyberTenant=domain)
        
        found_records = []
        bulk_data_create = []
        bulk_data_update = []
        indexName = await records_ins().collection_name(domain)
        classname = records_ins().getclassname()
        c = u = datetime.datetime.utcnow()
        if isUpdate:
            for interface in records:
                #checking only first field for compare need to add more fileds
                field = queryPoints["exists"]["must"][0]
                isfound = False
                for interface_old in records_old['data']:
                    #if match found update record
                    if interface.get(field) == interface_old.get(field):
                        # interface["_id"] = interface_old["_id"]
                        bulk_data_update.append({**records_ins(**interface).to_elastic(exclude_unset=False, exclude_none=True),
                             **{"c": c, "u": u, '_type_': classname, '_id': interface_old['_id']}})
                        # await records_ins(**interface).update(cyberTenant=domain)
                        found_records.append(interface_old["_id"])
                        isfound = True
                        break
                #If not found create the records
                if not isfound:
                    bulk_data_create.append({**records_ins(**interface).to_elastic(exclude_unset=False, exclude_none=True), **{"c": c, "u": u, '_type_': classname}})
            deleted_records = [{"_id": interface['_id']} for interface in records_old['data'] if interface["_id"] not in found_records]
        else:
            # Delete all records
            deleted_records = [{"_id": x['_id']} for x in records_old['data']]
            #create all records
            bulk_data_create.extend([{**records_ins(**x).to_elastic(exclude_unset=False, exclude_none=True),
                              **{"c": c, "u": u, '_type_': classname}} for x in records])
        if deleted_records:
            try:
                df = pd.DataFrame(deleted_records)
                df.set_index('_id', drop=True, inplace=True)
                ep.to_es(df, indexName, doc_type='_doc', _op_type='delete', show_progress=False)
            except Exception as e:
                pass
        if bulk_data_create:
            ep.to_es(pd.DataFrame(bulk_data_create), indexName, doc_type='_doc', show_progress=False)
        if bulk_data_update:
            df = pd.DataFrame(bulk_data_update)
            df['index'] = df['_id']
            df.set_index('index', drop=True, inplace=True)
            df.drop(['_id'], axis=1, inplace=True)
            ep.to_es(df, indexName, doc_type='_doc', _op_type='update', show_progress=False)
        return records

    async def getInsecurePorts(self, companyid, domain=None):
        import cybercns_model
        ins = cybercns_model.CustomPortSettings()
        query = Helpers.buildElsQuery({"companyRef.id.keyword": companyid}, mustExpression={"exists":{"field":"insecurePorts"}})
        params = framework.queryparams.QueryParams()
        params.q = json.dumps(query)
        params.limit = 1
        resp = await ins.get_all(params, cyberTenant=domain)
        if resp["data"]:
            return [int(port) for port in resp["data"][0].get("insecurePorts", [])]
        query = Helpers.buildElsQuery(mustExpression={"exists": {"field": "insecurePorts"}}, mustNotExpression={"exists": {"field": "companyRef.id.keyword"}})
        params = framework.queryparams.QueryParams()
        params.q = json.dumps(query)
        params.limit = 1
        resp = await ins.get_all(params, cyberTenant=domain)
        if resp["data"]:
            return [int(port) for port in resp["data"][0].get("insecurePorts", [])]
        return insecurePorts

    async def updateAssetPorts(self, ruledata):
        if not isinstance(ruledata, dict):
            ruledata = ruledata.dict()

        ins = framework.postgresmodel.PostgresModel()
        ins.Config.collection_name = 'test'
        client = await ins.client()
        indexName = await ins.collection_name()
        params = framework.queryparams.QueryParams()
        params.limit = 10000
        params.skip = 0
        try:
            must = {}
            mustNotExpression = []
            companies = []
            if ruledata.get('companyRef'):
                companies = [ruledata['companyRef']['id']]
            else:
                companyQuery = {"query": {"bool": {"must": [{"exists": {"field": "description"}}], "must_not": [{"exists": {"field": "companyRef"}}]}}}
                params.q = json.dumps(companyQuery)
                companyResp = await ins.get_all(params)
                companySettingData = []
                if companyResp["data"]:
                    companyId = [company.get('id') for company in companyResp['data']]
                    settingsQuery = Helpers.buildElsQuery(shouldExpression=[{"exists": {"field": "insecurePorts"}},
                                    {"exists": {"field": "excludedPorts"}},
                                   {"exists": {"field": "assetDeprecationDays"}}])
                    settingsQuery['query']['bool']['must'].append({"exists": {"field": "companyRef"}})
                    params.q = json.dumps(settingsQuery)
                    companySettings = await ins.get_all(params)
                    if companySettings["data"]:
                        companySettingData = [setCompany.get('companyRef',{}).get('id','') for setCompany in companySettings['data']]
                    companies = list(set(companyId) - set(companySettingData))
            for company in companies:
                inSecurePortsAssets = []
                securePortsAssets = []
                must = {"companyRef.id.keyword": company}
                insecurePorts = [int(port) for port in ruledata['insecurePorts']]
                if insecurePorts:
                    logger.info("The update operation is being triggered in asset level since insecure ports is available")
                    query = Helpers.buildElsQuery(must=must,
                                                  mustExpression=[{"exists": {"field": "port"}},
                                                                  {"exists": {"field": "service"}}])
                    query['query']['bool']['must'].append({'terms': {'port':insecurePorts}})
                    query['script'] = {
                        "inline": "ctx._source.isSecure=false",
                        "lang": "painless"
                    }

                    asset_secure_ports_update = await client.update_by_query(index=indexName, body=query,refresh=True)
                    logger.info("The response of updating all the asset ports to insecure true  is :%s" % asset_secure_ports_update)
                    if asset_secure_ports_update.get('updated') > 0:
                        aggrquery = Helpers.buildElsQuery(must=must,
                                                          mustExpression=[{"exists": {"field": "port"}},
                                                                          {"exists": {"field": "service"}}])
                        aggrquery['query']['bool']['must'].append({'terms': {'port': insecurePorts}})
                        aggrquery['aggs'] = {"assets": {"terms": {"field": "assetRef.id.keyword", "order": {"_count": "desc"}, "size": 10000}}}
                        aggrquery['size'] = 0
                        response = await client.search(index=indexName, body=aggrquery)
                        for record in response.get("aggregations").get("assets").get("buckets", []):
                            inSecurePortsAssets.append(record.get('key'))
                        if inSecurePortsAssets:
                            updateSecurityScorequery = {"query": {"bool": {"must": {"exists": {"field": "security_reportcard"}}}}}
                            updateSecurityScorequery['query']['bool']['filter'] = [{"ids": {"values": inSecurePortsAssets}}]
                            updateSecurityScorequery['script'] = {"source": "ctx._source.security_reportcard.insecureListeningPorts=1", "lang": "painless"}
                            insecure_ports_update = await client.update_by_query(index=indexName, body=updateSecurityScorequery,refresh=True)
                            logger.info("The response of updating all the asset ports to insecure false  is :%s" % insecure_ports_update)
                asset_insecure_ports_query = Helpers.buildElsQuery(must,
                                            mustExpression=[{"exists": {"field": "port"}},{"exists": {"field": "service"}}])
                if insecurePorts:
                    asset_insecure_ports_query['query']['bool']['must_not'] = {'terms': {'port': insecurePorts}}
                asset_insecure_ports_query['script'] = {"inline": "ctx._source.isSecure=true", "lang": "painless"}
                asset_insecure_ports_update = await client.update_by_query(index=indexName, body=asset_insecure_ports_query,refresh=True)
                aggrquery = Helpers.buildElsQuery(must=must,
                                                  mustExpression=[{"exists": {"field": "port"}},
                                                                  {"exists": {"field": "service"}}])
                aggrquery['query']['bool']['must_not'] = [{'terms': {'port': insecurePorts}}]
                aggrquery['aggs'] = {"assets": {"terms": {"field": "assetRef.id.keyword", "order": {"_count": "desc"}, "size": 10000}}}
                aggrquery['size'] = 0

                response = await client.search(index=indexName, body=aggrquery)
                for record in response.get("aggregations").get("assets").get("buckets", []):
                    securePortsAssets.append(record.get('key'))
                if securePortsAssets:
                    assets = list(set(securePortsAssets) - set(inSecurePortsAssets))
                    updateSecurityScorequery = Helpers.buildElsQuery(must=must,
                                              mustExpression=[{"exists": {"field": "host.importance"}}, {"exists": {"field": "security_reportcard"}}])
                    updateSecurityScorequery['query']['bool']['filter'] = [{"ids": {"values": assets}}]
                    updateSecurityScorequery['script'] = {"source": "ctx._source.security_reportcard.insecureListeningPorts=5", "lang": "painless"}
                    security_report_update = await client.update_by_query(index=indexName,body=updateSecurityScorequery)
                    logger.info("The response of updating all the asset ports to insecure false  is :%s" % security_report_update)
            return "Processed"
        except Exception as e:
            logger.info("Exception in updating the asset port single rule:%s" % e)
            return "Failed to Process"

    # This function will change data to ELS/Fast API schema format
    async def convert_to_schema(self, asset_ins, assetData, domain=None):
        vul_stats = {}
        asset_id = ""
        importance = 25
        client = await asset_ins.client()
        try:
            agent_data = await client.get(index=await asset_ins.collection_name(domain), id=assetData.agent_id)
            if not isinstance(agent_data,dict):
                agent_data = agent_data.dict()
            _id = agent_data["_id"]
            agent_data = agent_data["_source"]
            agent_data["_id"] = _id
        except Exception as e:
            agent_data = {}
            logger.info("Exception in agent_data : %s" % e)
        host_data = {"host": {}, "os": {}, "agentRef": {"id": assetData.agent_id, "name": ""}}
        if assetData.agent_data.agent_type.lower() == "lightweight":
            host_data['agentRef']['agent_type'] = 2
        elif assetData.agent_data.agent_type.lower() == "lightweightinstalled":
            host_data['agentRef']['agent_type'] = 3
        else:
            host_data['agentRef']['agent_type'] = 1
        asset_parameters = {}
        osquery_data = {}
        if assetData.data.vulnerability_status:
            osquery_data = self._convertCollectedData(assetData.data.vulnerability_resp)
        if osquery_data:
            self._getOsInfo(osquery_data)
            osquery_data["package"] = self._filterPackages(osquery_data.get("package", []),osquery_data.get("application", []))
            interfaces = self._filterValidInterfaces(osquery_data.get("interface", []))
            if assetData.data.ip and len(assetData.data.ip) and assetData.data.ip not in ["localhost", "127.0.0.1"]:
                osquery_data['host']["ip"] = assetData.data.ip
            else:
                ip, mac = self._fetchIpDetails(interfaces)
                if ip:
                    osquery_data['host']["ip"] = ip
                if mac:
                    osquery_data['host']["mac"] = mac
            host_data['host'] = osquery_data['host']
            host_data['os'] = osquery_data['os']
            asset_parameters['interfaces'] = interfaces
            asset_parameters['firewall'] = osquery_data.get('firewall',[])
            #print(osquery_data.get('firewall'))
            # update bit-locker status to disk details
            if 'bitlocker' in osquery_data and 'disk' in osquery_data:
                bitlocker_status = {
                    i['drive_letter']: 1 if i['protection_status'] else 0
                    for i in osquery_data.get('bitlocker', [])
                }
                osquery_data['disk'] = [
                    {**i, **{'encrypted': bitlocker_status.get(i["device"], 2)}} for i in osquery_data.get('disk', [])
                ]

            # update windows product-type (WorkStation, Server or Domain Controller)
            if osquery_data.get('product_type'):
                product_type = {
                    "WinNT": "Workstation", "ServerNT": "Server standalone", "LanmanNT": "Server Domain Controller"
                }
                host_data['os'].update(
                    {"product_type": product_type.get(osquery_data['product_type'][0]['data'], 'Unknown')}
                )

            # check for registry misconfigurations
            if osquery_data.get('best_practices'):
                with open('meta/registry_misconfiguration.json', "r") as f:
                    reg_misconfig = json.load(f)
                osquery_data['reg_misconfiguration'] = copy.deepcopy(osquery_data['best_practices'])
                for record in osquery_data['reg_misconfiguration']:
                    record["found"] = str(record["status"])
                    del record["status"]
                tmp = [i.update(reg_misconfig.get(i['name'], {})) for i in osquery_data['reg_misconfiguration']]
            if "disk" in osquery_data:
                # print(osquery_data.get('disk'))
                for disk in osquery_data["disk"]:
                    if not disk.get("encrypted") or not isinstance(disk["encrypted"], int):
                        disk["encrypted"] = 2
            # All supporting packages
            for key in ['package', 'user', 'failedlogon', 'firewall_policy', 'disk', 'best_practices',
                        'reg_misconfiguration', 'running_process']:
                asset_parameters[key] = osquery_data.get(key, [])
            if osquery_data.get("compliance"):
                assetData.data.compliance_status = osquery_data["compliance"]["status"]
                assetData.data.compliance_resp = osquery_data["compliance"]["data"]
        else:
            host_data["os"] = self._getOsinfo_Nmap(assetData.data)
            host_data["host"] = self._getHostInfo(assetData.data)
        if assetData.data.ports:
            asset_parameters['noAuthVuls'] = assetData.data.noAuthVuls
            if not asset_parameters['noAuthVuls']:
                asset_parameters['noAuthVuls'] = []
            port_vuls = {}
            for vul in asset_parameters['noAuthVuls']:
                if vul.port and vul.severity.lower() != 'info':
                    if vul.port not in port_vuls:
                        port_vuls[vul.port] = 0
                    port_vuls[vul.port] += 1
            for port_info in assetData.data.ports:
                if port_info.port in port_vuls:
                    port_info.vulCount = port_vuls[port_info.port]
            asset_parameters['ports'] = assetData.data.ports
            vul_stats["count_of_open_ports"] = len(assetData.data.ports)
        if assetData.data.sslGrade:
            vul_stats["ssl_grade"] = assetData.data.sslGrade
        if assetData.data.sslCert:
            asset_parameters["ssl_data"] = self._processSslData(assetData)
        host_data['host']['jid'] = assetData.data.jid
        if assetData.data.status:
            host_data['host']["discovered"] = datetime.datetime.utcnow()
        host_data['host']['status'] = assetData.data.status
        if host_data.get("host", {}).get("mac") and host_data["host"]["mac"] != "00:00:00:00:00:00":
            if "windows" in host_data.get('os', {}).get('platform', '').lower():
                icon = "windows.svg"
            else:
                icon = manuf.MacParser().get_manuf(host_data["host"]["mac"])
                icon = getVendorIcon(icon)
            osquery_data["icon"] = icon
            vendor = manuf.MacParser().get_manuf_long(host_data["host"]["mac"])
            if vendor:
                host_data["host"]["manufacturer"] = vendor
            if icon:
                host_data["host"]["icon"] = icon
        else:
            os_platform = host_data.get("os", {}).get('platform', '')
            if os_platform:
                icon = ""
                if "windows" in os_platform.lower():
                    icon = "windows.svg"
                else:
                    if os_platform == "rhel":
                        os_platform = "redhat"
                    icon = getVendorIcon(os_platform)
                if icon:
                    host_data["host"]["icon"] = icon
        if host_data["host"].get("version"):
            host_data["host"]["version"] = str(host_data["host"]["version"])
        if assetData.data.compliance_status:
            compliance = json.loads(assetData.data.compliance_resp)
            if isinstance(compliance, dict):
                asset_parameters['compliance'] = compliance["complianceData"]
                asset_parameters['complianceCheckFiles'] = compliance["filesVerified"]
            else:
                asset_parameters['compliance'] = compliance
        # todo:- if asset is discovered with lightweightagent(installed one) and then with probe, need to keep only lightweightagent details
        response = await self.checkAssetExists(asset_ins, host_data, asset_parameters.get('interfaces', []), assetData.companyid, assetData.data, domain=domain)
        if response:
            asset_id = response['_id']
            host_data['companyRef'] = response.get('companyRef', {})
            if agent_data and agent_data['agent_type'] == 3:
                host_data['agentRef'] = {"id": agent_data["_id"], "name": agent_data['name'], "agent_type": agent_data['agent_type']}
            else:
                host_data['agentRef'] = response.get('agentRef', {})
            if response.get('importance'):
                importance = response['importance']
        if not host_data.get('agentRef'):
            host_data['agentRef'] = {"id": assetData.agent_id}
        if not host_data.get('companyRef'):
            host_data['companyRef'] = {}
            host_data['companyRef']['id'] = assetData.companyid
        # FIXME, update here accordingly..
        if asset_parameters.get('package'):
            host_data["security_reportcard"] = self._gen_sec_report_card(host_data, asset_parameters)
            logger.info("Report Card %s" % host_data["security_reportcard"])
        #Handling Compliance Security Card
        print("compliance_report_card data %s" %osquery_data.get('compliance_report_card'))
        if osquery_data.get('compliance_report_card'):
            host_data["compliance_reportcard"] = self._gen_comp_report_card(osquery_data.get('compliance_report_card'))
            print("Compliance Report Card %s" % host_data["compliance_reportcard"])
        host_data["host"]['importance'] = importance
        # print(asset_parameters.get('running_process'))
        if asset_parameters.get('ports'):
            insecure_ports = await self.getInsecurePorts(assetData.companyid, domain=domain)
            for port in asset_parameters["ports"]:
                if port.port in insecure_ports:
                    port.isSecure = False
                else:
                    port.isSecure = True
        if asset_parameters.get('ports') and asset_parameters.get('running_process'):
            portmap = {
                i['port']: i
                for i in asset_parameters.get('running_process', [])
            }
            for port in asset_parameters['ports']:
                if port.port in portmap:
                    for key in ["name", "path"]:
                        if key in portmap[port.port]:
                            if key == 'name':
                                port.name = portmap[port.port][key]
                            elif key == 'path':
                                port.path = portmap[port.port][key]
                            # port[key] = portmap[port['port']][key]
        # print(osquery_data.get('oscap', {}).keys())
        if osquery_data.get('oscap'):
            osquery_data['oscap'] = {'ovalOutput': osquery_data['oscap'].get('data', {}).get('ovalOutput', '')}
            if osquery_data['oscap'].get('ovalOutput'):
                ovalOutput = []
                for line in osquery_data['oscap']['ovalOutput'].strip().splitlines():
                    if line.strip().startswith("Definition"):
                        definition, status = line.replace("Definition", "").strip().split(": ")
                        if status.strip() == "false":
                            continue
                        else:
                            ovalOutput.append(line.strip())
                osquery_data['oscap']['ovalOutput'] = "\n".join(ovalOutput)
        return {"host_data": host_data, "asset_parameters": asset_parameters, "asset_id": asset_id, "vul_stats": vul_stats, 'oscap': osquery_data.get('oscap')}


    @staticmethod
    def _processSslData(assetData):
        ssl_data = {"protocols": [], "ciphers": []}
        enumCiphers = assetData.data.enumCiphers
        protocolsSupported = []
        if enumCiphers:
            for record in enumCiphers:
                record_ = record.dict()
                info = {"name": record_["tlsversion"], "isSecure": True}
                if record_.get("port"):
                    info["port"] = record_["port"]
                if record_["tlsversion"].lower().startswith('tls'):
                    info["name"] = record_["tlsversion"].replace('tlsv', 'TLS v')
                    version = record_["tlsversion"].lower().split("tlsv")[-1]
                    if version.strip() < "1.2":
                        info['isSecure'] = False
                    for rec in record.ciphers:
                        rec.protocol = info["name"]
                    #     if "CBC" in rec["name"]:
                    #         info['isSecure'] = False
                    ssl_data["ciphers"].extend(record_['ciphers'])
                ssl_data["protocols"].append(info)
        ssl_data["additional_certs"] = assetData.data.additional_certs
        ssl_data["sslCert"] = assetData.data.sslCert
        ssl_data["grade"] = assetData.data.sslGrade
        return ssl_data

    @staticmethod
    def _is_edr_installed(installed_programs, host_, firewall=[]):
        if host_.get('os', {}).get('platform') in ['linux', 'ubuntu', 'rhel']:
            return -1,"Os Info: "+host_.get('os', {}).get('platform')

        count, edr_list = 3, None
        for _ in range(3):
            # Query EDR Vendor's, if installed mark anti-virus as installed.
            edr_vendor_resp = requests.get(
                "https://softwarerepo.my-netalytics.com/usermgmt/api/central_services/dummy/list_edr_vendors",
                headers={'X-Api-AccessKey': "", "content-type": "application/json"}
            )
            if edr_vendor_resp.status_code == 200 or count < 0:
                edr_list = re.compile("|".join(edr_vendor_resp.json()['msg']), re.IGNORECASE)
                break
            else:
                logger.info(f"EDR API Response {edr_vendor_resp.status_code}")
                time.sleep(30)
        else:
            logger.info("Failed to update EDR Details.")

        if not edr_list:
            return 1, "Failed to get EDR Details."

        evidence = []
        for ip in installed_programs:
            if ip.get("name") and edr_list.search(ip['name']):
                evidence.append(ip.get("name"))
        #check from firewall_policy if any edr installed
        for fw in firewall:
            if fw.get("name"):
                evidence.append(fw.get("name"))
        if len(evidence):
            return 5, f"Applications: {','.join(evidence)}"
        return 1, "No matching EDR Found."

    @staticmethod
    def _supported_os(os_):
        data_ = [{
            "product": os_['name'],
            "version": os_.get('build', os_.get('version', '')) if os_['name'].strip().lower() == 'windows 10' else "",
            "edition": os_.get('edition', "") if os_['name'].strip().lower() == 'windows 10' else "",
        }]

        resp = requests.post("https://softwarerepo.my-netalytics.com/usermgmt/api/central_services/dummy/get_eol_info",
                             headers={'X-Api-AccessKey': "", "Content-Type": "application/json"},
                             data=json.dumps({"products": data_}), timeout=300, verify=False)

        if resp.status_code != 200:
            return -1, "EOL not found."

        if resp.status_code == 200:
            resp = resp.json()['msg'][0]

            if not resp.get('active_support') or not resp.get('security_support'):
                return -1, "Active Support and Security Support date not found."

            active_support = datetime.datetime.strptime(resp['active_support'], "%d/%m/%Y").date()
            security_support = datetime.datetime.strptime(resp['security_support'], "%d/%m/%Y").date()

            now_ = datetime.datetime.now().date()

            # unsupported Operating Systems
            if active_support < now_ and security_support < now_:
                return 1, "Active Support:"+str(active_support)+",Security Support:"+str(security_support)

            # Operating Systems are within 1 year of end of life
            elif security_support - datetime.timedelta(days=365) <= now_ < security_support:
                return 3, "Active Support:"+str(active_support)+",Security Support:"+str(security_support)

            #  Operating Systems are in extended supported
            elif active_support < now_ < security_support:
                return 4, "Active Support:"+str(active_support)+",Security Support:"+str(security_support)

            #  computers have supported Operating Systems
            else:
                return 5, "Active Support:"+str(active_support)+",Security Support:"+str(security_support)
        else:
            return -1, "EOL not found."
    def _gen_comp_report_card(self, compliance_data):
        llmnr_grade, ntmlv1_grade, nbtns_grade = 2, 1, 2
        smbv1Server_grade, smbv1Client_grade, smbSigning_grade = 5, 5, 1
        ReqSecuritySig, EnableSecuritySig = 0, 0
        llmnr_evidence, ntmlv1_evidence, nbtns_evidence  = "" ,"", ""
        smbv1Server_evidence, smbv1Client_evidence, smbSigning_evidence = "", "" , ""
        for key in compliance_data:
            if key["name"] == "LLMNR":
                llmnr_evidence = r"Path : HKEY_LOCAL_MACHINE\Software\Policies\Microsoft\Windows NT\DNSClient\EnableMulticast, Data : "+str(key["data"])
                if int(key["data"]) == 0:
                    llmnr_grade = 5
                else:
                    llmnr_grade = 1
            elif key["name"] == "NTMLv1":
                ntmlv1_evidence = r"Path : HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Lsa\LmCompatibilityLevel, Data : "+str(key["data"])
                if int(key["data"]) == 5:
                    ntmlv1_grade = 5
            elif key["name"] == "NBTNS" and nbtns_grade != 1:
                nbtns_evidence = r"Path : HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\NetBT\Parameters\Interfaces\\NetbiosOptions, Data : "+str(key["data"])
                nbtns_grade = 5
                if int(key["data"]) == -1:
                    nbtns_grade = 2
                elif int(key["data"]) == 1:
                    nbtns_grade = 1
                elif int(key["data"]) == 0:
                    nbtns_grade = 2
            elif key["name"] == "SMBv1Server":
                smbv1Server_evidence = r"Path : HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters\SMB1, Data : "+str(key["data"])
                if int(key["data"]) != 0:
                    smbv1Server_grade = 1
            elif key["name"] == "SMBv1Client":
                smbv1Client_evidence = r"Path : HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\mrxsmb10\Start, Data : "+str(key["data"])
                if int(key["data"]) in [2,3]:
                    smbv1Client_grade = 1
            elif key["name"] == "ReqSecuritySig":
                smbSigning_evidence = r"Path : HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters\RequireSecuritySignature, Data : "+str(key["data"])
                ReqSecuritySig = int(key["data"])
            elif key["name"] == "EnableSecuritySig":
                EnableSecuritySig = int(key["data"])
        if ReqSecuritySig == 1 and EnableSecuritySig == 1 :
            smbSigning_grade = 5
        report_card = [
            {"name": "llmnr", "grade": llmnr_grade},
            {"name": "ntmlv1", "grade": ntmlv1_grade},
            {"name": "nbtns", "grade": nbtns_grade},
            {"name": "smbv1Server", "grade": smbv1Server_grade},
            {"name": "smbv1Client", "grade": smbv1Client_grade},
            {"name": "smbSigning", "grade": smbSigning_grade}
        ]
        evidence = {"llmnr": llmnr_evidence,
                    "ntmlv1": ntmlv1_evidence,
                    "nbtns": nbtns_evidence,
                    "smbv1Server": smbv1Server_evidence,
                    "smbv1Client": smbv1Client_evidence,
                    "smbSigning": smbSigning_evidence}
        resp = {r["name"]: r["grade"] for r in report_card}
        resp["evidence"] = evidence
        return resp

    def _gen_sec_report_card(self, host_data, asset_data):
        if host_data.get('os', {}).get('platform') != "windows":
            return {}
        # ref: https://www.rapidfiretools.com/reports/Security_Assessment_Consolidated_Security_Report_Card.pdf

        # Local Firewall
        logger.info("firewall_policy %s" % asset_data.get('firewall_policy', []))
        fw_policy = {i['policytype']: i.get('policystatus', "") for i in asset_data.get('firewall_policy', [])}
        # TODO, domain policy check required.
        if fw_policy.get("PublicProfile", "") == 1 and fw_policy.get("StandardProfile", "") == 1:
            fw_status = 5
        elif fw_policy.get("StandardProfile", "") == 1:
            fw_status = 4
        else:
            fw_status = 1
        fw_status_evidence = "Public Profile: "+str(fw_policy.get("PublicProfile", ""))+",Standard Profile: "+str(fw_policy.get("StandardProfile", ""))

        # Insecure Listening Ports
        ignore_ports = {445, 80, 443, 3389, 135}  # Ports to be ignored.
        port_count = sum(p.port not in ignore_ports for p in asset_data.get("ports", []))
        insecurePorts_evidence = "Listening Ports:"+str([p.port for p in asset_data.get("ports", [])])
        failed_login = -1
        # Failed Logins
        if asset_data.get('failed_login'):
            if asset_data['failed_login'][0]['count'] == 0:
                failed_login = 5
            elif asset_data['failed_login'][0]['count'] <= 7:
                failed_login = 4
            elif asset_data['failed_login'][0]['count'] <= 14:
                failed_login = 3
            else:
                failed_login = 1

            failed_login_evidence = "Failed Login count :"+str(asset_data['failed_login'][0]['count'])
        else:
            failed_login_evidence = "Failed login count not found."

        # Network Vulnerabilities
        noauth_score_ = dict({"minor": 0, "major": 0, "critical": 0})
        for record in asset_data.get('noAuthVuls', []):
            if not record.cvss:
                continue

            if 0 < record.cvss < 4:
                noauth_score_['minor'] = noauth_score_['minor'] + 1
            elif 4 <= record.cvss < 7:
                noauth_score_['major'] = noauth_score_['major'] + 1
            else:
                noauth_score_['critical'] = noauth_score_['critical'] + 1
        if noauth_score_.get('critical'):
            no_auth_grade = 1
        elif noauth_score_.get('major'):
            no_auth_grade = 3
        elif noauth_score_.get('minor'):
            no_auth_grade = 4
        else:
            no_auth_grade = 5

        no_auth_grade_evidence = "Critical Score: "+str(noauth_score_.get('critical'))+",Major Score: "+str(noauth_score_.get('major'))+",Minor Score: "+str(noauth_score_.get('minor'))

        # System Aging
        install_date = host_data['os'].get('install_date')
        sys_age = 0
        if install_date:
            sys_age = (datetime.datetime.now() - datetime.datetime.fromtimestamp(install_date)).days
            if sys_age <= 365 * 2:
                sys_age_grade = 5
            elif 365 * 2 < sys_age <= 365 * 4:
                sys_age_grade = 4
            elif 365 * 4 < sys_age <= 365 * 7:
                sys_age_grade = 3
            else:
                sys_age_grade = 1
        else:
            sys_age_grade = -1
        sys_age_grade_evidence = "System Age: "+str(sys_age)+", Install Date: "+str(datetime.datetime.fromtimestamp(install_date))
        edr_grade, edr_value = self._is_edr_installed(asset_data.get('package', []), host_data, asset_data.get('firewall', []))
        supportedOS_grade, supportedOS_evidence = self._supported_os(host_data['os'])
        report_card = [
            {"name": "antiVirus", "grade": edr_grade},
            {"name": "localFirewall", "grade": fw_status},
            {"name": "insecureListeningPorts", "grade": {0: 5, 1: 3}.get(port_count, 1)},
            {"name": "failedLogin", "grade": failed_login},
            {"name": "networkVulnerabilities", "grade": no_auth_grade},
            {"name": "systemAging", "grade": sys_age_grade},
            {"name": "supportedOS", "grade": supportedOS_grade},  # Supported OS
        ]
        evidence = {"antiVirus": edr_value,
                    "localFirewall": fw_status_evidence,
                    "insecureListeningPorts": insecurePorts_evidence,
                    "failedLogin": failed_login_evidence,
                    "networkVulnerabilities": no_auth_grade_evidence,
                    "systemAging": sys_age_grade_evidence,
                    "supportedOS": supportedOS_evidence}
        resp = {r["name"]: r["grade"] for r in report_card}
        resp["evidence"] = evidence
        return resp

    async def processAssetData(self, data, domain=None):
        import cybercns_model
        ep = getESpandasConnection()
        # print(data.dict())
        if data.assetData.data.status == False and not data.assetData.asset_id:
            logger.info("Status %s, AssetId: %s, IpAddress: %s" % (
                data.assetData.data.status, data.assetData.asset_id, data.assetData.data.ip))
            # r = redis.Redis()
            # r.hset(f"jobupdater_{data.assetData.job_id}", str(uuid.uuid4()),
            #        json.dumps({"ipaddress": data.assetData.data.ip, "reason": data.assetData.data.vulnerability_resp,
            #                    "status": False, "pingStatus": data.assetData.data.pingStatus, "topPortsScan": data.assetData.data.topPortsScan}))
            # r.close()
            if not data.assetData.data.vulnerability_resp:
                data.assetData.data.vulnerability_resp = "Ping Failed"
            await agentCommunicator.AgentCommunicator().update_job(data.assetData.job_id, [{"ipaddress": data.assetData.data.ip,
                                                                                            "reason": data.assetData.data.vulnerability_resp,
                               "status": False, "pingStatus": data.assetData.data.pingStatus, "topPortsScan": data.assetData.data.topPortsScan}], domain)
            # print('Discarding Offline Asset')
            return
        # print(data.assetData.data.extraInfo)
        if data.assetData.companyid:
            companyData = await cybercns_model.Company().get(data.assetData.companyid, cyberTenant=domain)
        else:
            companyData = {}
        networkPortVersions = {}
        try:
            if data.assetData.data.noAuthVuls:
                CPE_URI_REGEX = re.compile("(o|a|h):(.*?):(.*?):(.*?):(.*?):(.*?)")
                for vul in data.assetData.data.noAuthVuls:
                    if str(vul.port) in networkPortVersions:
                        continue
                    if vul.result and vul.result.startswith("cpe:"):
                        cpe = CPE_URI_REGEX.search(vul.result + ":*:*:*:*:*")
                        if cpe:
                            type_, vendor_, name_, version_, update_, _ = cpe.groups()
                            if type_ == "a" and version_ and version_ not in ["*"]:
                                networkPortVersions[str(vul.port)] = {"name": name_, "full_name": name_, "port": vul.port,
                                                                      "publisher": vendor_, "version": version_, "cpe_product": name_, "ref": vul.result}
                                if vendor_:
                                    networkPortVersions[str(vul.port)]["cpe_vendor"] = vendor_
        except Exception as e:
            print(traceback.format_exc())
            print(e)
        agent_data = data.assetData.agent_data
        resp = await self.convert_to_schema(cybercns_model.Asset(), data.assetData, domain=domain)
        asset_data, asset_parameters, asset_id, vul_stats, oscap_data = resp['host_data'], resp['asset_parameters'], resp[
            'asset_id'], resp['vul_stats'], resp.get('oscap')
        try:
            agentData = await cybercns_model.Agent().get(agent_data.agent_id, cyberTenant=domain)
        except:
            agentData = {"_id": agent_data.agent_id, "host_name": agent_data.host_name,
                         "ostype": cybercns_enum.OSType[agent_data.ostype].value,
                         "name": agent_data.host_name, "version": agent_data.agent_version,
                         "ip": asset_data.get('host', {}).get('ip', agent_data.host_name)}
            if agent_data.agent_type.lower() == "lightweight":
                agent_data.agent_type = "LightWeight"
            if agent_data.agent_type.lower() == "lightweightinstalled":
                agent_data.agent_type = "LightWeightInstalled"
            # Allowing only agent to create without company if hostname is equal to server hostname
            if companyData:
                agentData['companyRef'] = {"id": companyData.id, "name": companyData.name}
            else:
                if socket.gethostname() != agent_data.host_name:
                    return False, "Companyid missing"
                else:
                    agent_data.agent_type = "ExternalScanAgent"
                    agentData["name"] = "ExternalScanAgent"
            agentData['agent_type'] = cybercns_enum.AgentType[agent_data.agent_type].value
            agentData = await cybercns_model.Agent(**agentData).create(cyberTenant=domain)
            if cybercns_enum.AgentType[agent_data.agent_type].value == 1:
                startip = asset_data.get('host', {}).get('ip')
                if not startip:
                    print("Error in getting Probe IP Address for agent %s" % agentData)
                else:
                    discoverySettings = {"discovery_type": "cidr", "ip_start": ".".join(startip.split(".")[0:3] + ["1"]),
                                         "ip_end": "", "subnet_mask": "/24", "isExcluded": False, "name": agent_data.host_name,
                                         "agentRef": {"id": agent_data.agent_id, "name": agent_data.host_name},
                                         "companyRef": {"id": companyData.id, "name": companyData.name}, "tags": []}
                    await cybercns_model.DiscoverySettings(**discoverySettings).create(cyberTenant=domain)
        if not companyData:
            logger.info("Companyid missing")
            return False, "Companyid missing"

        if asset_parameters.get("failedlogon"):
            asset_data['host']['failed_logins'] = asset_parameters['failedlogon'][0]['count']
        asset_data['companyRef']['name'] = companyData.name
        redisIns = redis.Redis()
        redisIns.hset("agentConnectionTime", data.assetData.agent_id, datetime.datetime.utcnow().strftime("%s"))
        redisIns.close()
        agentData = await cybercns_model.Agent().get(data.assetData.agent_id, cyberTenant=domain)
        if not asset_data['agentRef'].get("name"):
            asset_data['agentRef'].update({"name": agentData.name})
        if not asset_data['agentRef'].get("agent_type"):
            asset_data['agentRef'].update({"agent_type": agentData.agent_type})
        asset_data["lastdiscoveredtime"] = datetime.datetime.utcnow()
        asset_data["discoveredProtocols"] = []
        asset_data["isdeprecated"] = False
        if agentData.agent_type == 4:
            asset_data["discoveredProtocols"].append('EXTERNALSCAN')
        discoverysettings_tags = []
        if data.assetData.data.hostname:
            for host_name in data.assetData.data.hostname:
                if host_name.source.upper() not in asset_data["discoveredProtocols"]:
                    asset_data["discoveredProtocols"].append(host_name.source.upper())
        if data.assetData.data.discoverysettingsRef:
            asset_data['discoverysettingsRef'] = data.assetData.data.discoverysettingsRef
            # if len(data.assetData.data.discoverysettingsRef.tags) > 0:
            discoverySettings = await cybercns_model.DiscoverySettings().get(data.assetData.data.discoverysettingsRef.id, cyberTenant=domain)
            if not isinstance(discoverySettings, dict):
                discoverySettings = discoverySettings.dict()
            if discoverySettings.get('tags', []):
                discoverysettings_tags = discoverySettings.get('tags', [])
        if data.assetData.cred_id:
            asset_data["credid"] = data.assetData.cred_id
        if asset_id:
            oldData = await cybercns_model.Asset().get(asset_id, cyberTenant=domain)
            if oldData:
                if not isinstance(oldData, dict):
                    oldData = oldData.dict()
                if "discoveredProtocols" in oldData and oldData["discoveredProtocols"]:
                    for protocol in oldData["discoveredProtocols"]:
                        if protocol not in asset_data["discoveredProtocols"]:
                            asset_data["discoveredProtocols"].append(protocol)
                tags = oldData.get("tags", [])
                if len(discoverysettings_tags) > 0:
                    tags.extend(discoverysettings_tags)
                asset_data["tags"] = list(set(tags))
            asset_data['_id'] = asset_id
            response = await cybercns_model.Asset(**asset_data).update(cyberTenant=domain)
            # print(response.id)
        else:
            if len(discoverysettings_tags) > 0:
                asset_data["tags"] = discoverysettings_tags
            response = await cybercns_model.Asset(**asset_data).create(cyberTenant=domain)
        del asset_data["agentRef"]["agent_type"]

        reference = {"companyRef": asset_data["companyRef"],
                     "agentRef": asset_data["agentRef"]}
        if isinstance(response, dict):
            reference["assetRef"] = {"id": response['_id'], "ip": asset_data["host"]["ip"],
                                     "name": asset_data["host"].get("host_name", asset_data["host"]["ip"])}
        else:
            reference["assetRef"] = {"id": response.id, "ip": asset_data["host"]["ip"],
                                     "name": asset_data["host"].get("host_name", asset_data["host"]["ip"])}
        # todo:- Need to move create/update/delete to the AssetProcessor
        networkVuls = []
        if 'noAuthVuls' in asset_parameters:
            start_time = datetime.datetime.utcnow()
            noauth_vulstats, networkVuls = await self.saveNoauthVulnerabilities(ep, cybercns_model.Vulnerability, cybercns_model.InstalledProgram, reference,
                                                                                              asset_parameters[
                                                                                                  'noAuthVuls'], networkPortVersions, agentData.agent_type, domain=domain)
            end_time = datetime.datetime.utcnow()
            # print(f"Took {(end_time - start_time).seconds} Seconds For network vuls fetch")
            vul_stats.update(noauth_vulstats)
        network_vulscount = sum([vul_stats.get(variable, 0) for variable in
                                 ["count_of_critical_network_vuls", "count_of_high_network_vuls",
                                  "count_of_medium_network_vuls", "count_of_low_network_vuls",
                                  "count_of_info_network_vuls"]])
        vulstatus = True
        vulstatus_msg = "Success"
        auth_vul_stats = {}
        if 'package' in asset_parameters:
            status, auth_vul_stats, vul_resp = await self.getVulnerabilities(ep, cybercns_model.Vulnerability, cybercns_model.InstalledProgram,
                                                                                      cybercns_model.Remediation,
                                                                                      cybercns_model.RemediationSuppression, reference,
                                                                                      asset_data,
                                                                                      asset_parameters['package'], oscap_data, domain=domain)
            if not status:
                vulstatus = False
                vulstatus_msg = vul_resp
            job_id = data.assetData.job_id
            discovery_protocol = ""
            if asset_data["os"].get("platform") == "windows":
                discovery_protocol = 'SMB'
            else:
                discovery_protocol = 'SSH'
            vuls_count = sum([auth_vul_stats.get(variable, 0) for variable in
                              ["count_of_critical_vuls", "count_of_high_vuls", "count_of_medium_vuls",
                               "count_of_low_vuls"]])
            await agentCommunicator.AgentCommunicator().update_job(job_id, [{"assetRef": reference["assetRef"],
                                                                          "ipaddress": reference["assetRef"].get("ip", ""),
                                                                          "status": vulstatus, "reason": vulstatus_msg,
                                                                          "pingStatus": data.assetData.data.pingStatus,
                                                                          "topPortsScan": data.assetData.data.topPortsScan,
                                                                          "vulcount": vuls_count,
                                                                          "risk_score": auth_vul_stats.get("risk_score", 0),
                                                                          "noauth_vulscount": network_vulscount,
                                                                          "discoveredProtocol": discovery_protocol}], domain)
            if data.assetData.cred_id:
                asset_data["discoveredProtocols"].append(discovery_protocol)
                asset_data["credid"] = data.assetData.cred_id
            else:
                if "LIGHTWEIGHTAGENT" not in asset_data["discoveredProtocols"]:
                    asset_data["discoveredProtocols"].append("LIGHTWEIGHTAGENT")
            await cybercns_model.Asset(
                **{"_id": reference["assetRef"]["id"], "lastvul_scannedtime": datetime.datetime.utcnow()}).update(cyberTenant=domain)
            vul_stats.update(auth_vul_stats, cyberTenant=domain)
        else:
            if data.assetData.data.vulnerability_status == False:
                discovery_status = False
                errmsg = data.assetData.data.vulnerability_resp
                if agentData.agent_type == 4:
                    discovery_status = True
                else:
                    if not errmsg:
                        if data.assetData.data.pingStatus and not data.assetData.data.topPortsScan:
                            errmsg = "Ping Successfull, No Open ports"
                        else:
                            errmsg = "No Credentials Matched"
                await agentCommunicator.AgentCommunicator().update_job(data.assetData.job_id,
                                                                       [{"assetRef": reference["assetRef"], "ipaddress": reference["assetRef"].get("ip", ""),
                                   "pingStatus": data.assetData.data.pingStatus, "topPortsScan": data.assetData.data.topPortsScan,
                                   "status": discovery_status, "reason": errmsg, "noauth_vulscount": network_vulscount}], domain)
        try:
            vul_stats['asset_score'] = await ScoreEvaluator.ScoreEvaluator("asset", reference["assetRef"]["id"], domain).getScore()
        except Exception as e:
            logger.info("Exception in generating asset score %s" % e)
            print(traceback.format_exc())
        # Todo:- need to write an unique function for modifying the below conditions
        for key, details in {"interfaces": {"classname": "Interfaces",
                                            "dataCheck": {"exists": {"must": ["interface", "address", "assetRef.id"]}},"isUpdate":True},
                             "users": {"classname": "AssetUsers",
                                       "dataCheck": {"exists": {"must": ["username", "uid", "assetRef.id"]}},"isUpdate":True},
                             "ports": {"classname": "Ports",
                                       "dataCheck": {"exists": {"must": ["port", "service", "assetRef.id"]}},"isUpdate":True},
                             "disk": {"classname": "Storage",
                                      "dataCheck": {"exists": {"must": ["mountpoint", "total", "assetRef.id"]}},"isUpdate":True},
                             "firewall_policy": {"classname": "AssetFirewallPolicy",
                                                 "dataCheck": {"exists": {"must": ["policytype", "assetRef.id"]}},"isUpdate":True},
                             "compliance": {"classname": "Compliance",
                                            "dataCheck": {"exists": {"must": ["complaince_id", "assetRef.id"]}},"isUpdate":True},
                             "complianceCheckFiles": {"classname": "ComplianceChecks", "dataCheck": {
                                 "exists": {"must": ["filename", "isApplicable", "assetRef.id"]}},"isUpdate":True},
                             "running_process": {"classname": "AssetRunningProcess",
                                                 "dataCheck": {"exists": {"must": ["address", "port", "assetRef.id"]}},"isUpdate":False},
                             "reg_misconfiguration": {"classname": "RegistryMisConfiguration", "dataCheck": {
                                 "exists": {"must": ["found", "expected", "assetRef.id"]}},"isUpdate":False}}.items():
            if key in asset_parameters:
                class_ins = eval("cybercns_model."+details["classname"])
                records = await self.saveRecords(ep, details["dataCheck"], class_ins,
                                                                            reference, asset_parameters[key], domain=domain, isUpdate = details["isUpdate"])
        vul_timestats = {}
        vul_timestats.update(reference)
        vul_timestats["vul_stats"] = vul_stats
        if agentData.agent_type == 1:
            asset_data["discoveredProtocols"].append("NMAP")
        asset_data["discoveredProtocols"] = list(set(asset_data["discoveredProtocols"]))
        # print(asset_data["discoveredProtocols"])
        await cybercns_model.Asset(**{"vul_stats": vul_stats, "_id": reference["assetRef"]['id'], "discoveredProtocols": asset_data["discoveredProtocols"]}).update(cyberTenant=domain)
        await cybercns_model.AssetTimeStats(**vul_timestats).create(cyberTenant=domain)
        if asset_parameters.get("ssl_data") or agentData.agent_type == 4:
            await SslScanDataProcessor().saveSslData(ep, cybercns_model.SslScanTimeseries, cybercns_model.VulnerabilityTimeseries,
                                                                    reference, asset_parameters.get("ssl_data", {}), vul_stats,
                                                                    networkVuls,
                                                                    asset_parameters.get("ports", []), domain=domain)
        # Updating lightweightagent last scan time
        if agentData.agent_type in [2, 3]:
            agent_data = agentData.dict()
            agent_data["lastscannedtime"] = datetime.datetime.utcnow()
            await cybercns_model.Agent(**agent_data).update(cyberTenant=domain)


class SslScanDataProcessor():
    async def saveSslData(self, ep, ssl_timeseries_ins, no_auth_ins, referece_data, ssldata, vul_stats, noAuthVuls, ports, domain=None):
        uniqueId = str(uuid.uuid4())
        cipherKeys = {"logjam": "Logjam_443",
                      "poodle": "CVE-2014-3566",
                      "heartbeat": "SSL_HeartBleed_443",
                      "heartbleed": "SSL_HeartBleed_443"}

        ssldata["vul_stats"] = vul_stats
        c = u = datetime.datetime.utcnow()
        if ports:
            ssldata["ports"] = [port.dict() if not isinstance(port, dict) else port for port in ports]
        # noAuthList = [noAuth.shortName.lower() for noAuth in noAuthVuls]
        noAuthList = [rec['vul_id'] for rec in noAuthVuls]
        for name, string in cipherKeys.items():
            ssldata[name] = False
            if string.lower in noAuthList:
                ssldata[name] = True
        ssldata["freak"] = False
        if "export" in ",".join([cipher["name"] for cipher in ssldata.get("ciphers", [])]).lower():
            ssldata["freak"] = True
        if not ssldata.get('ciphers'):
            ssldata['ciphers'] = [{'name': '-'}]
        if ssldata.get('sslCert', {}):
            if not isinstance(ssldata["sslCert"], dict):
                ssldata["sslCert"] = ssldata["sslCert"]
        if 'sslCert' in ssldata and not ssldata['sslCert']:
            del ssldata['sslCert']
        ssldata["drown"] = False
        ssldata.update(referece_data)
        ssldata['uniqueid'] = uniqueId
        await ssl_timeseries_ins(**ssldata).create(cyberTenant=domain)
        vulnerability = []
        for vul in noAuthVuls:
            # vul = {"vul_id": record.shortName, "category": record.category, "severity": record.severity.title(),
            #        "title": record.title}
            # if record.result:
            #     vul['ref'] = record.result
            # if record.port:
            #     vul["port"] = record.port
            # if record.cvss:
            #     vul["score"] = {"cvss_score": record.cvss}
            # else:
            #     vul["score"] = {"cvss_score": 1}
            # if not record.result and record.title.startswith("cpe"):
            #     vul['ref'] = record.title
            # if record.product:
            #     vul["product"] = [record.product]
            if '_id' in vul:
                del vul['_id']
            vul.update(copy.deepcopy({**{"uniqueid": uniqueId}, **referece_data}))
            vulnerability.append(vul)
        classname = no_auth_ins().getclassname()
        indexName = await no_auth_ins().collection_name(domain)
        bulk_data_create = [{**no_auth_ins(**x).to_elastic(exclude_unset=False, exclude_none=True),
                             **{"c": c, "u": u, '_type_': classname}} for x in vulnerability]
        if bulk_data_create:
            ep.to_es(pd.DataFrame(bulk_data_create), indexName, doc_type='_doc', show_progress=False)


async def runOfflineScan(companyid, domain):
    print(f'running offline vulnerability scan for company {companyid}')
    cyberTenant = domain.split(".")[0]
    query = Helpers.buildElsQuery({"companyRef.id.keyword": companyid},
                                  mustExpression=[{"exists": {"field": "host.importance"}}, {"exists": {"field": "lastvul_scannedtime"}}],
                                  must_not={"isdeprecated": True})
    params = framework.queryparams.QueryParams()
    params.q = json.dumps(query)
    params.limit = 10000
    ins = framework.postgresmodel.PostgresModel()
    ins.Config.collection_name = 'test'
    asset_ins = cybercns_model.Asset()
    assetData = await asset_ins.get_all(params, cyberTenant=cyberTenant)
    jobid = str(uuid.uuid4())
    assets_processed = 0
    total = len(assetData['data'])
    success_count = 0
    jobData = {"job_data": {"status_message": f"Vulnerability Scanned For 0 / {total}, devices Publishing Results(Processed {assets_processed})",
                            "task": "Vulnerability Scan", "job_status": 3}, "_id": jobid, "companyRef": {"id": companyid}}
    await cybercns_model.Jobs(**jobData).create(cyberTenant=cyberTenant)
    ep = getESpandasConnection()
    jobUpdateData = []
    status_message = ""
    job_status = 3
    try:
        for asset in assetData['data']:
            print(f'running offline vulnerability scan for asset {asset["host"].get("host_name", asset["host"]["ip"])}')
            reference = {"companyRef": asset["companyRef"], "agentRef": asset["agentRef"]}
            reference["assetRef"] = {"id": asset['_id'], "ip": asset["host"]["ip"], "name": asset["host"].get("host_name", asset["host"]["ip"])}
            assets_processed += 1
            vul_stats = asset.get('vul_stats', {})
            vuls_count = sum([vul_stats.get(variable, 0) for variable in
                              ["count_of_critical_vuls", "count_of_high_vuls", "count_of_medium_vuls",
                               "count_of_low_vuls"]])
            if "windows" not in asset.get('os', {}).get("platform", "").lower():
                await cybercns_model.Asset(**{"_id": asset['_id'], "lastvul_scannedtime": datetime.datetime.utcnow()}).update(cyberTenant=cyberTenant)
                jobUpdateData.append({"assetRef": reference["assetRef"], "ipaddress": reference["assetRef"].get("ip", ""),
                                      "status": True, "reason": "Success", "vulcount": vuls_count,
                                      "risk_score": vul_stats.get("risk_score", 0), "discoveredProtocol": "OfflineScan"})
                success_count += 1
                continue
            installedprograms_query = Helpers.buildElsQuery({"assetRef.id.keyword": asset['_id'], "companyRef.id.keyword": companyid},
                                                            mustExpression=[{"exists": {"field": "publisher"}}, {"exists": {"field": "version"}}])
            params = framework.queryparams.QueryParams()
            params.q = json.dumps(installedprograms_query)
            params.limit = 10000
            installed_programs = await cybercns_model.InstalledProgram().get_all(params, cyberTenant=cyberTenant)
            status, vul_stats, errmsg = await AssetProcessor().getVulnerabilities(ep, cybercns_model.Vulnerability, cybercns_model.InstalledProgram,
                                                                                          cybercns_model.Remediation,
                                                                                          cybercns_model.RemediationSuppression, reference,
                                                                                          asset,
                                                                                          installed_programs['data'], None, domain=domain)
            if status:
                await cybercns_model.Asset(**{"vul_stats": vul_stats, "_id": asset['_id'], "lastvul_scannedtime": datetime.datetime.utcnow()}).update(cyberTenant=cyberTenant)
                vuls_count = sum([vul_stats.get(variable, 0) for variable in
                                  ["count_of_critical_vuls", "count_of_high_vuls", "count_of_medium_vuls",
                                   "count_of_low_vuls"]])
                jobUpdateData.append({"assetRef": reference["assetRef"], "ipaddress": reference["assetRef"].get("ip",""),
                                      "status": True, "reason": "Success", "vulcount": vuls_count,
                                      "risk_score": vul_stats.get("risk_score", 0), "discoveredProtocol": "OfflineScan"})
                success_count += 1
            else:
                jobUpdateData.append({"assetRef": reference["assetRef"], "ipaddress": reference["assetRef"].get("ip", ""),
                                      "status": False, "reason": errmsg, "discoveredProtocol": "OfflineScan"})
            await cybercns_model.Jobs(**{"_id": jobid, "job_data": {"status_message": f"Vulnerability Scan Completed For {success_count} / {total}, devices Publishing Results(Processed {assets_processed})",
                                                              "task": "Vulnerability Scan", "job_status": job_status}}).update(cyberTenant=cyberTenant)
        job_status = 5
        if success_count == 0:
            job_status = 6
        elif total - success_count > 0:
            job_status = 4
        status_message = f"Vulnerability Scan Completed For {success_count} / {total}, devices Publishing Results(Processed {assets_processed})"
    except Exception as e:
        print(f"Exception in fetching vulnerability for {companyid} with error {e} traceback {traceback.format_exc()}")
        job_status = 6
        status_message = "Error while running vulnerability scan"
    await agentCommunicator.AgentCommunicator().update_job(jobid, jobUpdateData, domain)
    jobData = {"job_data": {
        "status_message": status_message,  "task": "Vulnerability Scan", "job_status": job_status},
        "_id": jobid, "companyRef": {"id": companyid}}
    await cybercns_model.Jobs(**jobData).update(cyberTenant=cyberTenant)


async def offlineScanRunner(args):
    domainname = args["domain"]
    realm_name = framework.settings.domain_mapping.get(domainname, domainname).split(".")[0]
    status, cookie = reportProcessor.getCookie(f"{realm_name}", "reportProcessor", "")
    if not status or not cookie:
        print("Error in generating scheduled reports, unable to fetch cookie %s" % cookie)
    ins = framework.postgresmodel.PostgresModel()
    ins.Config.collection_name = 'test'
    for record in args["records"]:
        url = record["url"]
        doc = record["doc"]
        if not doc['companyid'] or "*" in doc['companyid']:
            query = Helpers.buildElsQuery(mustExpression=[{"exists": {"field": "description"}}],
                                          mustNotExpression=[{"exists": {"field": "companyRef"}}])
            params = framework.queryparams.QueryParams()
            params.q = json.dumps(query)
            params.limit = 10000
            resp = await ins.get_all(params, cyberTenant=realm_name)
            doc['companyid'] = [record['_id'] for record in resp['data']]
        for companyid in doc["companyid"]:
            print(f"Generating offline vulnerabiity scan for company {companyid}")
            try:
                await runOfflineScan(companyid, realm_name)
            except Exception as e:
                print(f"Exception in running offline scan for comapny {companyid}")


if __name__ == "__main__":
    filename = sys.argv[1]
    if not os.path.exists(filename):
        filename = base64.b64decode(filename).decode()
    with open(filename) as f:
        args = json.load(f)
    asyncio.run(offlineScanRunner(args))

