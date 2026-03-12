import re
import os
import json
import yaml
import copy
import math
import numpy
import Helpers
import datetime
import traceback
import json_flatten
import assetProcessor
import framework.queryparams
logger = framework.Logger.getInstance('snmpprocessor')


# 1.3.6.1.4.1.2021.100.2.0 for sophos
# 1.3.6.1.4.1.3097.6.3.1 watchgaurd
# 1.3.6.1.4.1.25053.3.1.5.15.8 Ruckus Wireless ZD1200
osMapper = {'cyberoam-utm': 'sophos', 'sonicwall': 'sonicos', 'ciscosb': 'cisco'}
entityData = {'type': 'mibwalk', 'oids': {"1.3.6.1.2.1.47.1.1.1.1.13": {"model": {}},
                                          "1.3.6.1.2.1.47.1.1.1.1.12": {"vendor": {'expression': '.*', 'group': 'group().lower().strip()'}},
                                          "1.3.6.1.2.1.47.1.1.1.1.10": {"version": {}},
                                          "1.3.6.1.2.1.47.1.1.1.1.18": {"hwversion": {}}}}

vendorMap = {"edgeos": "Ubiquiti"}

versionMapper = {
    'ios': {'type': 'expression', 'key': 'description', 'expression': 'Version\s?(.+?),', 'group': 'group(1).strip()'},
    '3com': {'type': 'expression', 'key': 'description', 'expression': 'Version\s?(.+?)\s',
             'group': 'group(1).strip()'},
    'draytek': {'type': 'expression', 'key': 'description', 'expression': 'Version:\s?(.+?),',
                'group': 'group(1).strip()'},
    'vmware': {'type': 'expression', 'key': 'description', 'expression': 'esxi\s?(.+?)\s', 'group': 'group(1).strip()'},
    'linux': {'type': 'expression', 'key': 'description', 'expression': '([0-9].*)?#', 'group': 'group(1).strip()'},
    'fireware': {'type': 'expression', 'key': 'description', 'expression': '.*', 'group': 'group().strip()'},
    'edgeswitch': {'type': 'expression', 'key': 'description', 'expression': ',\s?(.+?),', 'group': 'group(1).strip()'},
    'apc': {'type': 'expression', 'key': 'description', 'expression': 'PF:v\s?(.+?)\s', 'group': 'group(1).strip()'},
    'junos': {'type': 'expression', 'key': 'description', 'expression': 'JUNOS\s?(.+?),', 'group': 'group(1).strip()',
              'vendor': 'juniper'},
    'hiveos-wireless': {'type': 'expression', 'key': 'description', 'expression': 'HiveOS\s?(.+?)\s',
                        'group': 'group(1).strip()'},
    'adtran-aos': {'type': 'expression', 'key': 'description', 'expression': 'Version:\s?(.+?),',
                   'group': 'group(1).strip()'},
    'ironware': {'type': 'expression', 'key': 'description', 'expression': 'Version\s?(.+?)\s',
                 'group': 'group(1).strip()'},
    'fortigate': {'type': 'mibwalk', 'vendor': 'fortinet', 'oids':
        {
            '1.3.6.1.2.1.47.1.1.1.1.10': {
                'version': {'expression': '(.*v|.*\s)([\d.]+)', 'group': 'group(2).lower().strip()'},
                'product': {'expression': '\s?(.+?)\s', 'group': 'group(1).lower().strip()', 'default': 'fortinet'}
            },
            '1.3.6.1.2.1.47.1.1.1.1.12': {'vendor': {'expression': '.*', 'group': 'group().lower().strip()', 'default': 'fortinet'}},
            '1.3.6.1.2.1.47.1.1.1.1.13': {'model': {}}
        }},
    'ciscosb': {**entityData, **{'vendor': 'ciscosb', 'type': 'mibwalk'}},
    'procurve': {**entityData, **{'type': 'mibwalk'}},
    'sonicwall': {'type': 'expression', 'key': 'description', 'expression': 'Enhanced\s?(.+?)\)',
                  'group': 'group(1).strip()'}
}


class YamlLoader():
    def __init__(self):
        self.strategies = []
        delayedattach = []
        fname = []
        # for root, d_names, f_names in os.walk('/Users/venu/PycharmProjects/Smaster-Srv_Els/data/managed/osDefenitions/'):
        for root, d_names, f_names in os.walk('/data/osDefinitions/'):
            for f in f_names:
                fname.append(os.path.join(root, f))

        for yamlfile in fname:
            try:
                x = yaml.load(open(yamlfile))
                if x.get("os", "") in ["linux"]:
                    delayedattach.append(x)
                else:
                    self.strategies.append(x)
            except Exception as e:
                logger.info("Error loading file ", yamlfile)
                raise e
        self.strategies.extend(delayedattach)

    def buildStratergies(self, sysDoc):
        try:
            if not sysDoc.get('sysObjectId'):
                return {}
            self.system_id = sysDoc['sysObjectId']
            if not self.system_id.startswith("."):
                self.system_id = "." + self.system_id
            self.system_description = sysDoc['description']
            strategy = self.discoverOs()
            osname = strategy.get('os', 'Generic')
            if osname and osname in osMapper:
                osname = osMapper[osname]
            deviceInfo = {"os": osname, "device_type": strategy.get('type', '')}
            if strategy.get('group', ''):
                deviceInfo['vendor'] = strategy.get('group', '')
            if not deviceInfo.get('vendor') and strategy.get('mib_dir', []):
                deviceInfo['vendor'] = strategy['mib_dir'][0]
                if deviceInfo['os'] in osMapper:
                    deviceInfo['os'] = osMapper[deviceInfo['os']]
            if deviceInfo['os'] in vendorMap:
                deviceInfo['vendor'] = vendorMap[deviceInfo['os']]
            return deviceInfo
        except Exception as e:
            logger.info("Exception in buildStratergies:%s" % e)
            print(traceback.format_exc())
            return False, ''

    def default(self, o):
        if isinstance(o, numpy.int64): return int(o)

    def isMatched(self, strategy, key, value, defaultreturn):
        if key not in strategy:
            return defaultreturn
        if isinstance(strategy[key], str):
            strategy[key] = [strategy[key]]
        for comparevals in strategy[key]:
            try:
                if key == 'sysObjectID':
                    if (re.search(re.escape(comparevals.strip('/')), value)):
                        return True
                else:
                    if (re.search(comparevals.strip('/'), value)):
                        return True
            except Exception as e:
                raise e
        return False

    def discoverOs(self):
        for strategy in self.strategies:
            for x in strategy.get("discovery", []):
                sysoidmatch = self.isMatched(x, 'sysObjectID', self.system_id, True)
                sysdescrmatch = self.isMatched(x, 'sysDescr', self.system_description, True)
                sysoidregexmatch = self.isMatched(x, 'sysObjectID_regex', self.system_id, True)
                sysdescrregexmatch = self.isMatched(x, 'sysDescr_regex', self.system_description, True)
                notsysoidmatch = not (self.isMatched(x, 'sysObjectID_except', self.system_id, False))
                notsysdescrmatch = not self.isMatched(x, 'sysDescr_except', self.system_description, False)
                notsysoidregexmatch = not self.isMatched(x, 'sysObjectID_regex_except', self.system_id, False)
                notsysdescrregexmatch = not self.isMatched(x, 'sysDescr_regex_except', self.system_description, False)
                snmpgetmatch = True
                if x.get("snmpget"):
                    snmpgetmatch = False
                if (
                        sysoidmatch and sysdescrmatch and sysoidregexmatch and sysdescrregexmatch and notsysoidmatch and notsysdescrmatch and notsysoidregexmatch and notsysdescrregexmatch and snmpgetmatch):
                    return strategy
        return {"os": "Generic"}


class ProcessSnmpData():
    def _getSnmpData(self, valuetosave):
        try:
            deviceInfo = YamlLoader().buildStratergies(valuetosave)
            osname = deviceInfo.get('os')
            vendor = deviceInfo.get('vendor', osname)
            device_type = deviceInfo.get('device_type', '')
            if not osname or osname.lower() in ['generic', "linux", "windows"] or device_type in ["server"]:
                return False, 'Os Not Valid'
            if osname != 'Generic':
                valuetosave.update(deviceInfo)
                valuetosave['ostype'] = vendor
            with open('osMapper.json') as f:
                versionMapper = json.load(f)
            versionMap = versionMapper.get(osname)
            if not versionMap:
                return False, "Not Supported"
            if versionMap['type'] == 'expression':
                expData = {}
                regexFlags = re.IGNORECASE | re.MULTILINE
                for key, details in versionMap['data'].items():
                    if details['type'] == "regex":
                        resp = re.search(r'%s' % details['expression'], valuetosave.get(details['key'], ''),
                                         flags=regexFlags)
                        if resp:
                            try:
                                expData[key] = eval("resp.%s" % details['group'])
                            except Exception as e:
                                # log.info('Exception in version group for %s Group %s' % (resp, details['group']))
                                logger.info('Exception in version group for %s Group %s' % (resp, details['group']))
                    elif details['type'] == "execution":
                        try:
                            output = eval("'%s'%s" % (valuetosave.get(details['key'], ''), details['expression']))
                            if output:
                                if not isinstance(output, list):
                                    output = [output]
                                for index, value in enumerate(output):
                                    if value in details.get('mapper', {}):
                                        output[index] = details['mapper'][value]
                                expData[key] = " ".join(output)
                            elif details.get('default'):
                                expData[key] = details['default']
                        except Exception as e:
                            # log.info('Exception in version group for %s Group %s' % (resp, details['group']))
                            logger.info('Exception in version execution for %s' % e)
                if expData:
                    valuetosave.update(expData.copy())
                    expData.update({'type': 'vulscan'})
                    if not expData.get('vendor'):
                        expData['vendor'] = vendor
                    if not expData.get('os'):
                        expData['os'] = osname
                    if expData.get('product'):
                        valuetosave['model'] = expData['product']
                    return True, expData
            elif versionMap['type'] == 'mibwalk':
                versionMap['os'] = osname
                versionMap['vendor'] = vendor
                return True, versionMap
        except Exception as e:
            logger.info("Exception in getsnmpdata:%s" % e)
        return False, "Not Supported"

    async def process_data(self, asset_ins, vul_ins, job_ins, assetins_timeseries, snmpDetails):
        # Todo:- Need to update snmp Vulnerability details to jobs
        jobid = snmpDetails.get("jobid", "")
        snmp_data = []
        for record in snmpDetails.get("snmpData", []):
            basicDetails = {r["oid"]: r["value"][0] for r in record["snmpBaseDetails"]}
            valuetosave = {"snmp": basicDetails.copy(), "_id": record["assetid"], "snmp_credid": record.get("credid", "")}
            status, resp = self._getSnmpData(basicDetails)
            vulscan = False
            vendor = ""
            product = ""
            if status:
                vendor = resp["vendor"]
                if resp.get("type") == "vulscan":
                    valuetosave["os"] = {"os": resp["os"], "platform": "network_device", "version": resp["version"], "full_name": "%s %s" % (resp["vendor"], resp["os"]), "codename": resp.get("vendor", "")}
                    vulscan = True
                elif resp.get("type") == "mibwalk":
                    valuetosave["os"] = {"os": resp["os"], "platform": resp.get("device_type", ""),
                                         "version": resp["version"],
                                         "full_name": "%s %s" % (resp["vendor"], resp["os"])}
                    if record.get("snmpExtendedDetails", []):
                        snmpExtendedDetails = {r["oid"]: r["value"] for r in record["snmpExtendedDetails"]}
                        versionData = {}
                        for oid, expressionDetails in resp["oids"].items():
                            if snmpExtendedDetails.get(oid, []):
                                respData = "\n".join(list(set(snmpExtendedDetails.get("value", []))))
                                for key, expression in expressionDetails.items():
                                    if expression.get('expression'):
                                        search = re.search(r'%s' % expression['expression'], respData,
                                                           flags=re.MULTILINE | re.IGNORECASE)
                                        if search:
                                            try:
                                                versionData[key] = eval('search.%s' % expression['group'])
                                            except Exception as e:
                                                if expression.get('default'):
                                                    versionData[key] = expression['default']
                                    else:
                                        respData = respData if respData else expression.get('default', '')
                                        if respData:
                                            versionData[key] = respData
                        if versionData:
                            vulscan = True
                            vendor = versionData.get('vendor', "")
                            if not vendor:
                                vendor = resp.get("vendor", "")
                            os_name = versionData.get('os', )
                            if not os_name:
                                os_name = resp.get('os', )
                            product = versionData.get('product', "")
                            if not product:
                                product = resp.get('model', resp['vendor'])
                            if os_name:
                                valuetosave["os"] = {"os": os_name, "version": versionData.get('version', ""), "platform": "network_device", "full_name": "%s %s" % (vendor, os_name), "codename": vendor}
                    else:
                        vulscan = False
            assetData = await asset_ins.get(valuetosave['_id'])
            assetData = assetData.dict()
            valuetosave["discoveredProtocols"] = assetData.get("discoveredProtocols", [])
            valuetosave["discoveredProtocols"].append("SNMP")
            valuetosave["discoveredProtocols"] = list(set(valuetosave["discoveredProtocols"]))
            valuetosave["host"] = assetData["host"]
            if valuetosave["snmp"].get("sysName"):
                valuetosave["host"]["host_name"] = valuetosave["snmp"]["sysName"]
            basedata = {"assetRef": {"id": assetData['id'], "ip": valuetosave["host"].get("ip", ""),
                                     "name": valuetosave["host"].get("host_name", valuetosave["host"].get("ip", ""))},
                        "agentRef": assetData["agentRef"],
                        "companyRef": assetData["companyRef"]}
            await asset_ins(**valuetosave).update()
            if not assetData.get('os'):
                assetData['os'] = {}
            doc = {"os": assetData["os"], "host": assetData["host"], "platform": "network_device"}
            if not vendor and not product:
                resp = {'msg': {'cve_info': [], 'remediation': []}}
                # snmp_data.append({"assetRef": basedata["assetRef"],
                #                   "status": False, "reason": "Network device model not found",
                #                   "discoveredProtocol": "SNMP"})
                # continue
            else:
                doc["os"]["vendor"] = vendor
                doc["os"]["product"] = product
                doc["os"]["platform"] = "network_device"
                status, resp = assetProcessor.AssetProcessor()._centralServer("/usermgmt/api/central_services/dummy/find_vulnerabilities",
                                                   {"doc": doc})
                if not status or not isinstance(resp, dict) or not isinstance(resp.get("msg"), dict):
                    resp['msg'] = {'cve_info': [], 'remediation': []}
                    # snmp_data.append({"assetRef": basedata["assetRef"],
                    #                   "status": False, "reason": "Network device model not found",
                    #                   "discoveredProtocol": "SNMP"})
                    # continue

            logger.info("Vuls Count %s Remediation Count %s" % (len(resp['msg']['cve_info']),
                                                                len(resp['msg']['remediation'])))
            # print(resp["msg"])
            # print(json.dumps(resp['msg']['cve_info']))
            query = Helpers.buildElsQuery({"assetRef.id": basedata['assetRef']['id']},
                                          mustExpression=[{"exists": {"field": "assetRef.id"}},
                                                          {"exists": {"field": "score.base_score"}},
                                                          {"range": {"score.base_score": {"gt": 0}}}])
            params = framework.queryparams.QueryParams()
            params.skip = 0
            params.limit = 10000
            params.q = json.dumps(query)
            responseData = await vul_ins().get_all(params)
            discovered_vulnerabilities = {record['vul_id']: record['_id'] for record in responseData['data']}
            vul_stats = assetData.get('vul_stats', {})
            if not vul_stats:
                vul_stats = {}
            vulnerability = {}
            softwares_vuls = {"critical": [], 'high': [], 'medium': [], "low": []}
            for vul in resp['msg']['cve_info']:
                vul = json_flatten.unflatten(vul)
                vul = vul['vulnerability']
                vul.update(copy.deepcopy(basedata))
                if vul['vul_id'] in discovered_vulnerabilities:
                    vul['_id'] = discovered_vulnerabilities[vul['vul_id']]
                vulnerability[vul['vul_id']] = vul
                vul_stats[f"count_of_{vul['severity'].lower()}_vuls"] += 1

            if resp['msg'].get('cve_info'):
                max_base_score = max(resp['msg']['cve_info'], key=lambda x: x['vulnerability.score.base_score'])[
                    'vulnerability.score.base_score']
            else:
                max_base_score = 0

            if resp['msg'].get('cve_info'):
                max_exp_score = max(resp['msg']['cve_info'], key=lambda x: x['vulnerability.score.exploit_score'])[
                    'vulnerability.score.exploit_score']
            else:
                max_exp_score = 0

            if math.isnan(max_base_score):
                max_base_score = 0
            if max_base_score:
                vul_risk = (max_base_score * 5) + (max_exp_score * 2) + (assetData["host"]["importance"] / 10) * 3
            else:
                vul_risk = 0
            vul_stats['risk_score'] = vul_risk
            vul_stats['base_score'] = max_base_score
            new_vuls = [record for _, record in vulnerability.items() if '_id' not in record]
            for record in new_vuls:
                if f"count_of_{record['severity'].lower()}_vuls_new" not in vul_stats:
                    vul_stats[f"count_of_{record['severity'].lower()}_vuls_new"] = 0
                vul_stats[f"count_of_{record['severity'].lower()}_vuls_new"] += 1
            modified_vuls = [record for _, record in vulnerability.items() if '_id' in record]
            deleted_vuls = list(set(list(discovered_vulnerabilities.keys())) - set(list(vulnerability.keys())))
            deleted_vuls = [discovered_vulnerabilities[key] for key in deleted_vuls]
            tmpData = [await vul_ins(**x).create() for x in new_vuls]
            tmpData = [await vul_ins(**x).update() for x in modified_vuls]
            tmpData = [await vul_ins().delete(x) for x in deleted_vuls]
            await asset_ins(**{"_id": basedata["assetRef"]["id"], "lastvul_scannedtime": datetime.datetime.utcnow(), "vul_stats": vul_stats}).update()
            vul_timestats = {}
            vul_timestats.update(basedata)
            vul_timestats["vul_stats"] = vul_stats
            await assetins_timeseries(**vul_timestats).create()
            snmp_data.append({"assetRef": basedata["assetRef"],
                                                         "status": True, "reason": "Success",
                                                         "vulcount": len(vulnerability), "risk_score": vul_stats['risk_score'],
                              "discoveredProtocol": "SNMP"})
        try:
            if jobid and snmp_data:
                job_data = await job_ins().get(jobid)
                if not isinstance(job_data, dict):
                    job_data = job_data.dict()
                job_message = job_data.get("job_message", {})
                job_message["assetSnmpJobStatus"] = snmp_data
                job_data["job_data"]["job_message"] = job_message
                await job_ins(**job_data).update()
        except Exception as e:
            logger.info('Error in updating jobdata %s' % e)



