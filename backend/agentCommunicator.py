import framework
import os
import gzip
import json
import uuid
import redis
import random
import socket
import netaddr
import Helpers
import aioredis
import datetime
import ipaddress
import snmpProcessor
import cybercns_enum
import connectwiseApi
import reportProcessor
from copy import deepcopy
import framework.redispool
import framework.queryparams
import framework.postgresmodel
logger = framework.Logger.getInstance('agentcommunicator')

integration = {'active': True, 'name': 'new board', 'sbId': 19, 'sbTypeId': 89, 'sbSubTypeId': 130, 'new': 91, 'closed': 155, 'critical': 2, 'high': 1, 'medium': 4, 'low': 3, 'sbName': 'Alerts', 'credId': '5c41b09c-c979-4508-be53-e3307dbb3127', 'product': 'connectwise', 'family': 'integrations', 'species': 'ticketing', 'updated': 1618222478, 'created': 1618222478, '_id': '3gmTxXgBIY1ot-eIdf6z', 'Severity': 'High'}
settings = {'company': 'platform_c', 'domain': 'staging.connectwisedev.com', 'publicKey': 'QUwXmz3yZBC6dttd', 'privateKey': 'GhoM161Ms5bZI53R'}
defaultExcludedPorts = ["9100-9120", "515", "6101", "631", "59100", "10001"]

class AgentCommunicator():
    async def _getExcludedPorts(self, companyid):
        excluded_ports = []
        ins = framework.postgresmodel.PostgresModel()
        ins.Config.collection_name = 'test'
        query = Helpers.buildElsQuery({"companyRef.id.keyword": companyid},
                                      mustExpression={"exists": {"field": "excludedPorts"}})
        params = framework.queryparams.QueryParams()
        params.q = json.dumps(query)
        params.limit = 1
        resp = await ins.get_all(params)
        if resp["data"]:
            excluded_ports = [port for port in resp["data"][0].get("excludedPorts", [])]
        else:
            query = Helpers.buildElsQuery(mustExpression={"exists": {"field": "excludedPorts"}},
                                          mustNotExpression={"exists": {"field": "companyRef.id.keyword"}})
            params = framework.queryparams.QueryParams()
            params.q = json.dumps(query)
            params.limit = 1
            resp = await ins.get_all(params)
            if resp["data"]:
                excluded_ports = [port for port in resp["data"][0].get("excludedPorts", [])]
        for port in defaultExcludedPorts:
            if port not in excluded_ports:
                excluded_ports.append(port)
        return list(set(excluded_ports))

    async def getWork(self, agent_id):
        redisIns = await framework.redispool.get_redis_connection()
        # redisIns = redis.Redis()
        try:
            await redisIns.hset("agentConnectionTime", agent_id, datetime.datetime.utcnow().strftime("%s"))
            resp = await redisIns.rpop(agent_id + "_work")
            while resp:
                if isinstance(resp, bytes):
                    resp = resp.decode()
                schData = json.loads(resp)
                # Skipping Jobs If Jobs Created More Than 30 Minutes
                if schData.get("schtime"):
                    if (int(datetime.datetime.utcnow().strftime("%s")) - int(schData["schtime"])) > (30 * 60):
                        print("Agent Job Greater Than 30 min (%s) skipping" % (int(datetime.datetime.utcnow().strftime("%s")) - int(schData["schtime"])))
                        resp = await redisIns.rpop(agent_id + "_work")
                        continue
                    del schData["schtime"]
                return True, schData
            return False, {}
        finally:
            pass
            # redisIns.close()

    async def uninstallAgent(self, agent_ins, agent_id):
        agentData = await agent_ins().get(agent_id, cyberTenant=framework.ctx["tenant"])
        if not isinstance(agentData, dict):
            agentData = agentData.dict()
        if agentData['agent_type'] == 4:
            return False, "Not Allowed"
        # redisIns = redis.Redis()
        redisIns = await framework.redispool.get_redis_connection()
        scan_data = {"scantype": "agentUninstall"}
        resp = await redisIns.lpush(agent_id + "_work", json.dumps(scan_data))
        # redisIns.close()
        return True, "Initiated"

    async def uninstallCompanyAgents(self, company_ins, companyid):
        query = Helpers.buildElsQuery({"companyRef.id.keyword": companyid},
                                      mustExpression=[{"exists": {"field": "agent_type"}}])
        params = framework.queryparams.QueryParams()
        params.q = json.dumps(query)
        params.limit = 10000
        params.skip = 0
        resp = await company_ins().get_all(params)
        # redisIns = redis.Redis()
        redisIns = await framework.redispool.get_redis_connection()
        scan_data = {"scantype": "agentUninstall"}
        for agent in resp['data']:
            resp = await redisIns.lpush(agent['_id'] + "_work", json.dumps(scan_data))
        # redisIns.close()

    async def uploadagentlogs(self, upload_file):
        if not os.path.exists("/data/cybertemp/agentlogs"):
            os.makedirs("/data/cybertemp/agentlogs")
        filename = os.path.join("/data/cybertemp/agentlogs", upload_file.filename)
        with open(filename, "w+") as f:
            filecontent = gzip.open(upload_file.file, encoding='utf-8-sig', mode='rt').read()
            f.write(filecontent)
        return ""

    async def getAgentStatus(self, agent_id):
        # redisIns = redis.Redis()
        redisIns = await framework.redispool.get_redis_connection()
        resp = await redisIns.hget("agentConnectionTime", agent_id)
        # redisIns.close()
        if not resp:
            return False, 0
        if isinstance(resp, bytes):
            resp = resp.decode()
        lastConnectedTime = int(resp)
        if int(datetime.datetime.utcnow().strftime("%s")) - lastConnectedTime > (10 * 60):
            return False, lastConnectedTime
        return True, lastConnectedTime

    async def cybertemplates(self, template_type):
        # redisIns = redis.Redis()
        redisIns = await framework.redispool.get_redis_connection()
        if template_type == "osquery_executables":
            resp = await redisIns.get("cyberQueryExecutables")
            if resp:
                if isinstance(resp, bytes):
                    resp = resp.decode()
                return True, json.loads(resp)
        elif template_type == "templates":
            resp = await redisIns.get("cyberQueryTemplates")
            if resp:
                if isinstance(resp, bytes):
                    resp = resp.decode()
                return True, json.loads(resp)
        else:
            resp = await redisIns.get(template_type)
            if resp:
                if isinstance(resp, bytes):
                    resp = resp.decode()
                return True, json.loads(resp)
        # elif template_type == "probe_deps":
        #     resp = redisIns.get("probe_deps")
        #     if resp:
        #         return True, json.loads(resp.decode())
        return True, {}

    async def startAssetScan(self, job_ins, asset_ins, scantype, asset_id):
        ins = framework.postgresmodel.BasePostgresModel()
        ins.Config.collection_name = job_ins.Config.collection_name
        client = await ins.client()
        assetData = await client.get(index=await ins.collection_name(), id=asset_id)
        assetData = {**assetData["_source"], **{"_id": assetData['_id']}}
        agentData = await client.get(index=await ins.collection_name(), id=assetData["agentRef"]["id"])
        agentData = agentData["_source"]
        if agentData['agent_type'] == 3:
            scan_data = {"scantype": scantype.name}
        elif agentData['agent_type'] in [1, 4]:
            if scantype.value == 6:
                return await self.snmpScan(job_ins, asset_ins, assetData["companyRef"]["id"],
                                           assetData["agentRef"]["id"], assetid=asset_id)
            scanIps = [assetData["host"]["ip"]]
            jobid = str(uuid.uuid4())
            extraData = {}
            mastercredentials = {}
            excluded_ports = await self._getExcludedPorts(assetData["companyRef"]["id"])
            if assetData.get("credid"):
                # If credid not available go for all creds
                try:
                    creds = await client.get(index=await ins.collection_name(), id=assetData.get("credid"))
                    creds = {**creds["_source"], **{"_id": creds['_id']}}
                    ostype = cybercns_enum.CredType(creds['cred_type']).name.lower()
                    mastercredentials = {ostype: [creds]}
                except:
                    pass
            if len(mastercredentials) == 0:
                params = framework.queryparams.QueryParams()
                params.limit = 100
                params.skip = 0
                credentialsQuery = Helpers.buildElsQuery({"agentRef.id.keyword": assetData["agentRef"]["id"]},
                                                         mustExpression=[{"exists": {"field": "cred_type"}}])
                params.q = json.dumps(credentialsQuery)
                response = await ins.get_all(params)
                for credential in response['data']:
                    ostype = cybercns_enum.CredType(credential['cred_type']).name.lower()
                    credential['driver'] = ostype
                    credential['credId'] = credential['_id']
                    del credential['_id']
                    if ostype not in mastercredentials:
                        mastercredentials[ostype] = []
                    mastercredentials[ostype].append(credential)
            jobData = {"job_data": {"status_message": "Network Scan Initiated, Waiting For Agent Response",
                                    "task": "External Scan" if agentData['agent_type'] == 4 else "Asset Inventory Scan", "job_status": 2}}
            jobData.update({"companyRef": {"id": assetData["companyRef"]["id"]},
                            "agentRef": {"id": assetData["agentRef"]["id"]}})
            jobData["_id"] = jobid
            await job_ins(**jobData).create()
            scan_data = {"extradata": extraData, "scanlist": scanIps, "jobId": jobid,
                         "schtime": int(datetime.datetime.utcnow().strftime("%s")),
                         "taskName": "External Scan" if agentData['agent_type'] == 4 else "Asset Inventory Scan",
                         "scantype": scantype.name, "mastercredentils": mastercredentials, "portstodiscard": excluded_ports,
                         "companyid": assetData["companyRef"]["id"], "scanrange": scanIps[0]}
        else:
            return False, "Unsupported scan type"
        # redisIns = redis.Redis()
        redisIns = await framework.redispool.get_redis_connection()
        resp = await redisIns.lpush(assetData["agentRef"]["id"] + "_work", json.dumps(scan_data))
        # redisIns.close()
        return True, "Success"

    def _getIpDetails(self, discoverSettings, agent_type):
        scanIps = []
        subnets = []
        extraData = {}
        if discoverSettings['discovery_type'] == 'cidr':
            subnet = netaddr.IPNetwork(discoverSettings['ip_start'] + discoverSettings['subnet_mask'])
            sub_net = str(subnet.cidr)
            if sub_net not in subnets:
                subnets.append(sub_net)
            ips = [str(ip) for ip in subnet]
            extraData.update({ip: {"subnet": sub_net, "discoverysettingsRef": {"id": discoverSettings['_id'],
                                                                                    "name": discoverSettings.get("name", "")}} for ip in ips})
            scanIps.extend(ips)
            scanIps = list(set(scanIps))
        elif discoverSettings['discovery_type'] == 'fromto':
            if discoverSettings['ip_start'].rsplit(".", 1)[0] == discoverSettings['ip_end'].rsplit(".", 1)[0]:
                startIp = discoverSettings['ip_start'].rsplit(".", 1)[0] + ".0"
                endIp = discoverSettings['ip_end'].rsplit(".", 1)[0] + ".255"
                cidrs = netaddr.iprange_to_cidrs(startIp, endIp)
            else:
                cidrs = netaddr.iprange_to_cidrs(discoverSettings['ip_start'], discoverSettings['ip_end'])
            for subnet in cidrs:
                sub_net = str(subnet)
                if sub_net not in subnets:
                    subnets.append(sub_net)
                ips = []
                if len(cidrs) == 1 and sub_net.endswith("/24"):
                    startip = int(discoverSettings['ip_start'].rsplit(".", 1)[-1])
                    endip = int(discoverSettings['ip_end'].rsplit(".", 1)[-1])
                    for ip in subnet:
                        if int(str(ip).rsplit(".", 1)[-1]) < startip:
                            continue
                        elif int(str(ip).rsplit(".", 1)[-1]) > endip:
                            break
                        else:
                            ips.append(str(ip))
                else:
                    ips = [str(ip) for ip in subnet]
                extraData.update({ip: {"subnet": sub_net, "discoverysettingsRef": {"id": discoverSettings['_id'],
                                                                                    "name": discoverSettings.get("name", "")}} for ip in ips})
                scanIps.extend(ips)
        elif discoverSettings['discovery_type'] in ['static', 'staticDomain']:
            ip = discoverSettings['ip_start']
            try:
                netaddr.IPNetwork(ip)
                extraData[ip] = {"subnet": ".".join(ip.split(".")[:-1]) + ".0/24", "DiscoverySettingsAssetRef": {"id": discoverSettings['_id'],
                                                                                    "name": discoverSettings.get("name", "")}}
            except:
                hostname = ip
                extra_info = {}
                if agent_type == 4:
                    ip = self.gethostname(ip)
                    extra_info['assetName'] = hostname
                extraData[ip] = {"subnet": "", "discoverysettingsRef": {"id": discoverSettings['_id'],
                                                                                    "name": discoverSettings.get("name", "")}, **extra_info}
            scanIps.append(ip)
            if ip not in subnets:
                subnets.append(ip)
        scanIps = list(set(scanIps))
        return scanIps, extraData, subnets

    def gethostname(self, hostname):
        try:
            host = socket.gethostbyname(hostname)
            return host
        except socket.error:
            return hostname
        except Exception as e:
            return hostname

    async def createExternalScanAssets(self, asset_ins, discoverysettings):
        if not isinstance(discoverysettings, dict):
            discoverysettings = discoverysettings.dict()
        companyref = discoverysettings["companyRef"]
        agentref = discoverysettings["agentRef"]
        ip_address = []
        if discoverysettings['discovery_type'] == "fromto":
            if discoverysettings['ip_start'].rsplit(".", 1)[0] == discoverysettings['ip_end'].rsplit(".", 1)[0]:
                startIp = discoverysettings['ip_start'].rsplit(".", 1)[0] + ".0"
                endIp = discoverysettings['ip_end'].rsplit(".", 1)[0] + ".255"
                cidrs = netaddr.iprange_to_cidrs(startIp, endIp)
            else:
                cidrs = netaddr.iprange_to_cidrs(discoverysettings['ip_start'], discoverysettings['ip_end'])
            for subnet in cidrs:
                sub_net = str(subnet)
                if len(cidrs) == 1 and sub_net.endswith("/24"):
                    startip = int(discoverysettings['ip_start'].rsplit(".", 1)[-1])
                    endip = int(discoverysettings['ip_end'].rsplit(".", 1)[-1])
                    for ip in subnet:
                        if int(str(ip).rsplit(".", 1)[-1]) < startip:
                            continue
                        elif int(str(ip).rsplit(".", 1)[-1]) > endip:
                            break
                        else:
                            ip_address.append(str(ip))
                else:
                    ip_address.extend([str(ip) for ip in subnet])
        elif discoverysettings['discovery_type'] in ['static', 'staticDomain']:
            ip_address.append(discoverysettings["ip_start"])
        discoverysettingsRef = {"name": discoverysettings["name"]}
        if "_id" in discoverysettings:
            discoverysettingsRef["id"] = discoverysettings["_id"]
        elif "id" in discoverysettings:
            discoverysettingsRef["id"] = discoverysettings["id"]
        for ip in ip_address:
            host_name = ip
            ip_ = self.gethostname(ip)
            should = {"host.ip.keyword": [ip_]}
            try:
                ipaddress.ip_address(host_name).version
            except:
                should['host.host_name.keyword'] = [host_name]

            query = Helpers.buildElsQuery({"companyRef.id.keyword": companyref["id"]}, should=should, mustExpression=[{"exists": {"field": "host.importance"}}])
            params = framework.queryparams.QueryParams()
            params.q = json.dumps(query)
            params.limit = 1
            params.fields = ["host.ip", "host.host_name"]
            resp = await asset_ins.get_all(params)
            if resp["data"]:
                continue
            else:
                asset = {"host":{"host_name": host_name, "ip": ip_, "importance": 100, "status": True}, "agentRef": agentref,"companyRef": companyref}
                asset.update({"discoverysettingsRef": discoverysettingsRef, "discoveredProtocols": ["EXTERNALSCAN"],
                              "vul_stats": {"count_of_open_ports": 0}, "name": ip})
                await asset_ins(**asset).create()

    async def getLightAgentIps(self, companyid):
        skip_ips = []
        try:
            ins = framework.postgresmodel.BasePostgresModel()
            ins.Config.collection_name = 'test'
            client = await ins.client()
            query = Helpers.buildElsQuery(must={"agentRef.agent_type": 3, "companyRef.id.keyword": companyid}, mustExpression={"exists": {"field": "host.importance"}})
            query['_source'] = ["host.ip"]
            query['size'] = 10000
            response = await client.search(index=await ins.collection_name(), body=query)
            assets = [{**record['_source'], **{"_id": record["_id"]}} for record in response.get('hits', {}).get("hits", [])]
            skip_ips = [asset["host"]["ip"] for asset in assets]
            asset_ids = [record['_id'] for record in assets]
            query = Helpers.buildElsQuery(must={"companyRef.id.keyword": companyid},
                                          mustExpression=[{"exists": {"field": "interface"}}, {"exists": {"field": "mac"}}, {"exists": {"field": "address"}},
                                                          {"terms": {"assetRef.id.keyword": asset_ids}}])
            query['_source'] = ["address"]
            query['size'] = 10000
            response = await client.search(index=await ins.collection_name(), body=query)
            for interface in [{**record['_source'], **{"_id": record["_id"]}} for record in response.get('hits', {}).get("hits", [])]:
                if interface.get("address"):
                    try:
                        if ipaddress.ip_address(interface["address"]).version == 4:
                            skip_ips.append(interface["address"])
                    except:
                        continue
        except Exception as e:
            logger.info("Exception in get light ips %s" % e)
        return list(set(skip_ips))

    async def startGlobalExternalScan(self, job_ins, agent_ins, scantype, agent_id, companyid):
        if companyid:
            return await self.startAgentScan(job_ins, agent_ins, scantype, agent_id, companyid)
        ins = framework.postgresmodel.BasePostgresModel()
        ins.Config.collection_name = 'test'
        client = await ins.client()
        query = Helpers.buildElsQuery(mustExpression=[{"exists": {"field": "description"}}],
                                      mustNotExpression=[{"exists": {"field": "companyRef"}}])
        query['size'] = 10000
        client = await agent_ins().client()
        response = await client.search(index=await agent_ins().collection_name(), body=query)
        global_companies = [record["_id"] for record in response.get('hits', {}).get("hits", [])]
        for company in global_companies:
            status, resp = await self.startAgentScan(job_ins, agent_ins, scantype, agent_id, company)
            if not status:
                logger.info(f"External scan start failed for company {company} - {resp}")
        return True, "Success"

    async def startAgentScan(self, job_ins, agent_ins, scantype, agent_id, companyid):
        ins = framework.postgresmodel.BasePostgresModel()
        ins.Config.collection_name = 'test'
        client = await ins.client()
        agentData = await client.get(index=await ins.collection_name(), id=agent_id)
        agentData = agentData["_source"]
        redisIns = await framework.redispool.get_redis_connection()
        if agentData['agent_type'] in [1, 4]:
            if scantype.value == 6:
                return await self.snmpScan(job_ins, agent_ins, companyid, agent_id)
            excluded_ports = await self._getExcludedPorts(companyid)
            mastercredentials = {}
            activeDirectoryCreds = []
            oldcredmapping = []
            if scantype.value != 4:
                params = framework.queryparams.QueryParams()
                params.limit = 100
                params.skip = 0
                credentialsQuery = Helpers.buildElsQuery({"agentRef.id.keyword": agent_id, "companyRef.id.keyword": companyid},
                                                         mustExpression=[{"exists": {"field": "cred_type"}}])
                params.q = json.dumps(credentialsQuery)
                response = await ins.get_all(params)
                for credential in response['data']:
                    ostype = cybercns_enum.CredType(credential['cred_type']).name.lower()
                    credential['driver'] = ostype
                    credential['credId'] = credential['_id']
                    del credential['_id']
                    if ostype not in mastercredentials:
                        mastercredentials[ostype] = []
                    mastercredentials[ostype].append(credential)
                    if credential.get("hostname") and credential.get("domain"):
                        activeDirectoryCreds.append(credential)

                credids_query = Helpers.buildElsQuery({"agentRef.id.keyword": agent_id, "companyRef.id.keyword": companyid},
                                                     mustExpression=[{"exists": {"field": "host.importance"}}, {"exists": {"field": "credid"}}])
                params = framework.queryparams.QueryParams()
                params.limit = 10000
                params.skip = 0
                params.q = json.dumps(credids_query)
                params.fields = ["host.ip", "host.host_name", "credid"]
                response = await ins.get_all(params)
                for asset in response["data"]:
                    oldcredmapping.append({"ip": asset["host"]["ip"], "hostname": asset["host"]["host_name"], "credid": asset["credid"]})
            subnetsQuery = Helpers.buildElsQuery({"agentRef.id.keyword": agent_id, "companyRef.id.keyword": companyid},
                                                 mustExpression=[{"exists": {"field": "discovery_type"}}])
            params = framework.queryparams.QueryParams()
            params.limit = 100
            params.skip = 0
            params.q = json.dumps(subnetsQuery)
            response = await ins.get_all(params)
            if len(response.get('data')) == 0 and len(activeDirectoryCreds) == 0:
                return False, "Discovery Settings Not Available For The Given Agent"
            scanIps = []
            extraData = {}
            subnets = []
            excludes = []
            for discoverSettings in response['data']:
                if discoverSettings.get('isExcluded'):
                    scan_ips, _, _ = self._getIpDetails(discoverSettings, agentData['agent_type'])
                    excludes.extend(scan_ips)
            excludes = list(set(excludes))
            for discoverSettings in response['data']:
                if discoverSettings.get('isExcluded'):
                    continue
                scan_ips, extra_data, sub_nets = self._getIpDetails(discoverSettings, agentData['agent_type'])
                filter_ips = list(set(scan_ips) - set(excludes))
                scanIps.extend(filter_ips)
                extraData.update({ip: {**extra_data[ip], **{"companyid": companyid}} for ip in filter_ips})
                for subnet in sub_nets:
                    if subnet not in subnets:
                        subnets.append(subnet)
            scanIps = list(set(scanIps))
            scanIps = list(set(scanIps) - set(await self.getLightAgentIps(companyid)))
            if len(scanIps) == 0 and len(activeDirectoryCreds) == 0:
                return False, "No Ips Found To Scan"
            # redisIns = redis.Redis()
            if scantype.value in [1, 2, 3, 4] and scanIps:
                if scanIps == 1:
                    scanrange = scanIps[0]
                else:
                    scanrange = "\n".join(subnets)
                jobid = str(uuid.uuid4())
                jobData = {"job_data": {"status_message": "Network Scan Initiated, Waiting For Agent Response",
                                        "task": "External Scan" if agentData['agent_type'] == 4 else "Asset Inventory Scan", "job_status": 2}}
                jobData.update({"companyRef": {"id": companyid}, "agentRef": {"id": agent_id}})
                jobData["_id"] = jobid
                await job_ins(**jobData).create()
                scan_data = {"extradata": extraData, "scanlist": scanIps, "jobId": jobid,
                             "taskName": "External Scan" if agentData['agent_type'] == 4 else "Asset Inventory Scan",
                             "schtime": int(datetime.datetime.utcnow().strftime("%s")),
                             "scantype": scantype.name, "mastercredentils": mastercredentials, "companyid": companyid,
                             "portstodiscard": excluded_ports,
                             "scanrange": scanrange, "oldcredmapping": oldcredmapping}
                resp = await redisIns.lpush(agent_id + "_work", json.dumps(scan_data))
            if scantype.value in [1, 5] and activeDirectoryCreds:
                for cred in activeDirectoryCreds:
                    jobid = str(uuid.uuid4())
                    scan_data = {"extradata": {}, "scanlist": [], "jobId": jobid,
                                 "taskName": "Active Directory Scan",
                                 "schtime": int(datetime.datetime.utcnow().strftime("%s")),
                                 "scantype": "ActiveDirectoryScan", "mastercredentils": {"windows": [cred]},
                                 "companyid": companyid}
                    jobData = {"job_data": {"status_message": "Active Directory Scan Initiated, Waiting For Agent Response",
                                            "task": scan_data["taskName"], "job_status": 2}}
                    jobData.update({"companyRef": {"id": companyid}, "agentRef": {"id": agent_id}})
                    jobData["_id"] = jobid
                    await job_ins(**jobData).create()
                    resp = await redisIns.lpush(agent_id + "_work", json.dumps(scan_data))
            # redisIns.close()
        elif agentData['agent_type'] == 3:
            scan_data = {"scantype": scantype.name, "schtime": int(datetime.datetime.utcnow().strftime("%s")),}
            # redisIns = redis.Redis()
            resp = await redisIns.lpush(agent_id + "_work", json.dumps(scan_data))
            # redisIns.close()
        else:
            return False, "Agent not supported for work post"
        return True, "Success"

    async def startCompanyScan(self, job_ins, agent_ins, companyid, scantype):
        if scantype.value != 4:
            must = {"companyRef.id.keyword": companyid}
            if scantype == 7:
                must['agent_type'] = 3
            query = Helpers.buildElsQuery(must,
                                          mustExpression={"exists": {"field": "agent_type"}})
            params = framework.queryparams.QueryParams()
            params.limit = 10000
            params.skip = 0
            params.q = json.dumps(query)
            response = await agent_ins().get_all(params)
            for agent in response['data']:
                await self.startAgentScan(job_ins, agent_ins, scantype, agent['_id'], companyid)
        if scantype.value in [1, 4]:
            query = Helpers.buildElsQuery({"agent_type": 4},
                                          mustExpression={"exists": {"field": "agent_type"}},
                                          mustNotExpression={"exists": {"field": "companyRef.id.keyword"}})
            params = framework.queryparams.QueryParams()
            params.limit = 1
            params.skip = 0
            params.q = json.dumps(query)
            response = await agent_ins().get_all(params)
            for agent in response['data']:
                await self.startAgentScan(job_ins, agent_ins, scantype, agent['_id'], companyid)
            return True, "%s Initiated" % scantype.name

    async def snmpScan(self, job_ins, asset_ins, companyid, agentid, jobid="", assetid=""):
        if assetid:
            response = await asset_ins.get(assetid)
            if not isinstance(response, dict):
                response = response.dict()
            hostDetails = {response["host"]["ip"]: response["id"]}
        else:
            must = {"companyRef.id.keyword": companyid}
            if jobid:
                must["host.jid.keyword"] = jobid
            if agentid:
                must["agentRef.id.keyword"] = agentid
            query = Helpers.buildElsQuery(must, mustExpression={"exists": {"field": "host.jid"}})
            params = framework.queryparams.QueryParams()
            params.limit = 10000
            params.skip = 0
            params.q = json.dumps(query)
            response = await asset_ins.get_all(params)
            hostDetails = {record["host"]["ip"]: record["_id"] for record in response["data"]}
        if not hostDetails:
            return False, "No Assets Found"
        oids = []
        if not jobid:
            jobid = str(uuid.uuid4())
            #todo:- create job here
        for key, values in snmpProcessor.versionMapper.items():
            for oid, _ in values.get("oids", {}).items():
                oids.append(oid)
        snmpCreds = []
        snmpData = {'snmphostDetails': hostDetails, 'oids': list(set(oids)), "jobId": str(uuid.uuid4()),
                    "scantype": "SnmpScan", "snmpCreds": [],
                    "schtime": int(datetime.datetime.utcnow().strftime("%s")),}
        ins = framework.postgresmodel.PostgresModel()
        ins.Config.collection_name = asset_ins.Config.collection_name
        # SnmpV1/V2
        query = Helpers.buildElsQuery({"companyRef.id.keyword": companyid, "agentRef.id.keyword": agentid},
                                      mustExpression=[{"exists": {"field": "snmpVersion"}},
                                                      {"exists": {"field": "community"}}])
        params = framework.queryparams.QueryParams()
        params.limit = 10000
        params.skip = 0
        params.q = json.dumps(query)
        resp_v2 = await ins.get_all(params)
        communitystrings = []
        for cred in resp_v2['data']:
            cred["credId"] = cred["_id"]
            if cred["snmpVersion"] == "v1":
                cred["version"] = 0
            else:
                cred["version"] = 1
            if cred.get("port", 0) == 0:
                cred["port"] = 161
            snmpCreds.append(cred)
            communitystrings.append(cred["community"])
        query = Helpers.buildElsQuery({"companyRef.id.keyword": companyid, "agentRef.id.keyword": agentid},
                                      mustExpression=[{"exists": {"field": "securityName"}}])
        params = framework.queryparams.QueryParams()
        params.limit = 10000
        params.skip = 0
        params.q = json.dumps(query)
        resp_v3 = await ins.get_all(params)
        for cred in resp_v3['data']:
            cred["credId"] = cred["_id"]
            cred["version"] = 3
            if cred.get("port", 0) == 0:
                cred["port"] = 161
            snmpCreds.append(cred)
        for community in ["public", "Public", "admin", "Admin", "test", "private", "Private", "cisco"]:
            if community not in communitystrings:
                snmpCreds.append({"community": community, "version": 1})
        if snmpCreds:
            jobData = {"job_data": {"status_message": "Snmp Scan Initiated, Waiting For Agent Response",
                                    "task": "Snmp Scan", "job_status": 2}}
            jobData.update({"companyRef": {"id": companyid}, "agentRef": {"id": agentid}, "_id": snmpData["jobId"]})
            await job_ins(**jobData).create()
            snmpData['snmpCreds'] = snmpCreds
            # redisIns = redis.Redis()
            redisIns = await framework.redispool.get_redis_connection()
            resp = await redisIns.lpush(agentid + "_work", json.dumps(snmpData))
            # redisIns.close()
        return True, "Initiated"

    async def update_job(self, jobid, data, tenantName):
        import cybercns_model
        try:
            job_data = await cybercns_model.Jobs().get(jobid, cyberTenant=tenantName)
            if not isinstance(job_data, dict):
                job_data = job_data.dict()
        except:
            return
        try:
            job_message = job_data.get('job_data', {}).get("job_message", {})
            if not job_message:
                job_message = {}
            if not job_message.get('assetJobStatus'):
                job_message['assetJobStatus'] = []
            job_message["assetJobStatus"].extend(data)
            job_data["job_data"]["job_message"] = job_message
            await cybercns_model.Jobs(**job_data).update(cyberTenant=tenantName)
        except Exception as e:
            # Checking session available else doing print to avoid logger permission issues
            try:
                framework.ctx["tenenat"]
                logger.info('Error in updating jobdata %s' % e)
            except:
                print('Error in updating jobdata %s' % e)

    async def updateJobsData(self, jobid, tenantName=None):
        r = await framework.redispool.get_redis_connection()
        # r = redis.Redis()
        if await r.exists(f"jobupdater_{jobid}"):
            data = await r.hgetall(f"jobupdater_{jobid}")
            await r.delete(f"jobupdater_{jobid}")
            if data:
                data = [json.loads(d.decode() if isinstance(d, bytes) else d) for _, d in data.items()]
                await self.update_job(jobid, data, tenantName)
                # data = [json.loads(d.decode() if isinstance(d, bytes) else d) for _, d in data.items()]
                # try:
                #     job_message = job_data.get("job_message", {})
                #     if not job_message.get('assetJobStatus'):
                #         job_message['assetJobStatus'] = []
                #     job_message["assetJobStatus"].extend(data)
                #     job_data["job_data"]["job_message"] = job_message
                #     await cybercns_model.Jobs(**job_data).update(cyberTenant=tenantName)
                # except Exception as e:
                #     # Checking session available else doing print to avoid logger permission issues
                #     try:
                #         framework.ctx["tenenat"]
                #         logger.info('Error in updating jobdata %s' % e)
                #     except:
                #         print('Error in updating jobdata %s' % e)
        # r.close()

    async def discoveryCompleted(self, job_ins, asset_ins, companyid, agentid, jobid):
        await self.updateJobsData(jobid)
        return await self.snmpScan(job_ins, asset_ins, companyid, agentid, jobid)

    async def terminateJob(self, job_ins, jobid):
        try:
            response = await job_ins().get(jobid)
            if not isinstance(response, dict):
                response = response.dict()
            agent_id = response['agentRef']['id']
            redisIns = await framework.redispool.get_redis_connection()
            # redisIns = redis.Redis()
            scan_data = {"scantype": "agentRestart", "jobId": jobid}
            resp = await redisIns.rpush(agent_id + "_work", json.dumps(scan_data))
            # redisIns.close()
            # updating the job
            jobData = {"job_data": {"status_message": "Initiated Job Termination",
                                    "task": response['job_data']["task"], "job_status": 4}}
            jobData["_id"] = jobid
            await job_ins(**jobData).update()

            return True, "Initiated Job Termination"
        except Exception as e:
            return False, "Job Not Found"

    async def updateJob(self, job_ins, agent_ins, jobid, companyid, agent_id, asset_id, jobData):
        job_message = {}
        try:
            response = await job_ins().get(jobid)
            if not isinstance(response, dict):
                response = response.dict()
            job_message = response.get('job_data', {}).get("job_message", {})
            if not job_message:
                job_message = {}
        except:
            response = None
        if not job_message.get('assetJobStatus'):
            job_message['assetJobStatus'] = []
        redisIns = await framework.redispool.get_redis_connection()
        # r = redis.Redis()
        job_updater = await redisIns.hgetall(f"jobupdater_{jobid}")
        recordids = []
        if job_updater:
            recordids = [d.decode() if isinstance(d, bytes) else d for d, _ in job_updater.items()]
            job_updater = [json.loads(d.decode() if isinstance(d, bytes) else d) for _, d in job_updater.items()]
        else:
            job_updater = []
        job_message["assetJobStatus"].extend(job_updater)
        if recordids:
            for id in recordids:
                await redisIns.hdel(f"jobupdater_{jobid}", id)
        # r.close()
        if jobData.get("message"):
            message = json.loads(jobData["message"])
            del jobData["message"]
            if message.get("AssetInventory"):
                job_message["assetInventoryStatus"] = message.get("AssetInventory")[0]
        jobData["job_message"] = job_message
        if response and not jobData.get("task") and response.get("job_data", {}).get("task", ""):
            jobData["task"] = response["job_data"]["task"]
        job_data = {"job_data": jobData, "companyRef": {"id": companyid}, "_id": jobid}
        if agent_id:
            job_data["agentRef"]: {"id": agent_id}
        if asset_id:
            job_data['assetRef'] = {"id": asset_id}
        if response:
            await job_ins(**job_data).update()
        else:
            await job_ins(**job_data).create()
        if jobData["job_status"] in [5, 6]:
            agentData = await agent_ins().get(agent_id)
            agentData.lastscannedtime = datetime.datetime.utcnow()
            await agent_ins(**agentData.dict()).update()
        return True, "Success"

    async def applyRemediationPatch(self, rem_ins, agent_ins, remediationId, integrationId):
        # ins = framework.postgresmodel.PostgresModel()
        # ins.Config.collection_name = "test"
        try:
            remediationData = await rem_ins().get(remediationId)
            remediationData = remediationData.dict()
        except Exception as e:
            logger.info("Exception in getting remediation data %s" % e)
            return False, "Remediation Data Not Available"
        if not remediationData.get("chocoName"):
            return False, "Package is not allowed for patching"
        agentId = remediationData['agentRef']['id']
        assetId = remediationData['assetRef']['id']
        try:
            agentData = await agent_ins().get(agentId)
            agentData = agentData.dict()
        except Exception as e:
            logger.info("Exception in getting agent data %s" % e)
            return False, "Agent Data Not Available"
        if agentData["agent_type"] != 3:
            return False, "This Feature Supported Only For Installed LightWeight Agents"
        # Todo:- Create connectwise ticket
        summary = "Patch update For %s Agent %s" % (remediationData["product"], agentData['name'])
        desc = "Patch Installing For:-  %s\n" % remediationData["product"]
        desc += "Present Version:-       %s\n" % remediationData.get("version", "-")
        desc += "Available Version:-     %s\n" % remediationData.get("fix", "-")
        desc += "Total Vulnerabilities:- %s\n" % remediationData.get("vulcount", "-")
        desc += "Host Name:-             %s\n" % agentData.get("host_name", "-")
        ins = connectwiseApi.ConnectwiseManager(settings)
        status, resp = ins.createTicket({"Integration": integration, 'Severity': 'Critical', 'Summary': summary, 'ProblemDescription': desc}, remediationData["companyRef"]["name"], "148")
        logger.info("Ticket Creation status:%s resp:%s" % (status, resp))
        if status:
            ticketId = resp["id"]
            print(await rem_ins(**{"ticketId": ticketId, "_id": remediationData['id']}).update())
        # save ticketid to remediation
        patchData = {"scantype": "ApplicationPatching", "patchapplications": [{"name": remediationData["product"],
                                                                               "choconame": remediationData["chocoName"]}],
                     "schtime": int(datetime.datetime.utcnow().strftime("%s")),}
        redisIns = await framework.redispool.get_redis_connection()
        # redisIns = redis.Redis()
        resp = await redisIns.lpush(agentId+"_work",  json.dumps(patchData))
        # redisIns.close()
        return True, "Success"

    async def verifyScheduler(self, sch_ins, inputData):
        if not inputData.get("name"):
            return False, "Empty key name not allowed to save"
        query = Helpers.buildElsQuery(must={"name.keyword": inputData["name"]},
                                      mustExpression=[{"exists": {"field": "settings"}}],
                                      mustNotExpression=[{"exists": {"field": "scanType"}}])
        params = framework.queryparams.QueryParams()
        params.limit = 1
        params.skip = 0
        params.q = json.dumps(query)
        try:
            scheulerData = await sch_ins().get_all(params)
        except Exception as e:
            scheulerData = {"data": [], "count": 0, "total": 0}
        if scheulerData['data']:
            return False, "Duplicate scheduler name not supported"
        return True, "Success"

    # scheduleType will tell update/create or to delete
    async def updateScheduler(self, serving_domain, schedulerData, agent_ins, schedulerDbData, scheduleType=True):
        import cybercns_enum
        schedue_data = schedulerData.settings.dict()
        schedulerDbData = schedulerDbData.get("data", {})
        if not isinstance(schedulerDbData, dict):
            schedulerDbData = schedulerDbData.dict()
        print("schedulerDbData: ",schedulerDbData)
        jobId = schedulerDbData.get('_id', schedulerDbData.get('id'))
        if not schedulerData.isActive:
            scheduleType = False
        templateData = {t['uniqueId']: t for t in await self.getScheduleTemplates()}
        if schedulerData.uniqueid not in templateData:
            return False, "Not Supported"
        templateData = templateData[schedulerData.uniqueid]
        sch_type = templateData.get('scheduleType', '')
        if sch_type == 'agent':
            scantype = cybercns_enum.ScanType(templateData['defaultKeys']['scantype'])
            redisIns = await framework.redispool.get_redis_connection()
            # redisIns = redis.Redis()
            if schedulerData.isGlobal == False and schedulerData.companyRef:
                for company in schedulerData.companyRef:
                    must = {"companyRef.id.keyword": company.id}
                    if scantype.value == 4:
                        must = {"agent_type": 4}
                    elif scantype.value == 6:
                        must["agent_type"] = 1
                    elif scantype.value == 7:
                        must["agent_type"] = 3
                    query = Helpers.buildElsQuery(must, mustExpression={"exists": {"field": "agent_type"}})
                    params = framework.queryparams.QueryParams()
                    params.limit = 10000
                    params.skip = 0
                    params.q = json.dumps(query)
                    agent_data = await agent_ins().get_all(params)
                    for agent in agent_data["data"]:
                        if schedue_data.get("hours"):
                            if not schedue_data.get("mins"):
                                schedue_data["mins"] = [1]
                        work = {"scheduletype": scheduleType, "scheduledata": {**schedue_data, **{"taskname": scantype.name, "taskid": jobId}},
                                "scantype": "Scheduler"}
                        if agent["agent_type"] == 4:
                            work["scheduledata"]["companyid"] = company.id
                        resp = await redisIns.lpush(agent["_id"] + "_work", json.dumps(work))
            elif schedulerData.isGlobal == False and schedulerData.agentRef:
                for agent in schedulerData.agentRef:
                    if schedue_data.get("hours"):
                        if not schedue_data.get("mins"):
                            schedue_data["mins"] = [1]
                    work = {"scheduletype": True, "scheduledata": {**schedue_data, **{"taskname": scantype.name, "taskid": jobId}},
                            "scantype": "Scheduler"}
                    resp = await redisIns.lpush(agent.id + "_work", json.dumps(work))
            elif schedulerData.isGlobal:
                must = {}
                if scantype.value == 4:
                    must["agent_type"] = 4
                elif scantype.value == 6:
                    must["agent_type"] = 1
                elif scantype.value == 7:
                    must["agent_type"] = 3
                query = Helpers.buildElsQuery(must, mustExpression={"exists": {"field": "agent_type"}})
                params = framework.queryparams.QueryParams()
                params.limit = 10000
                params.skip = 0
                params.q = json.dumps(query)
                agent_data = await agent_ins().get_all(params)
                if schedue_data.get("hours"):
                    if not schedue_data.get("mins"):
                        schedue_data["mins"] = [1]
                for agent in agent_data["data"]:
                    work = {"scheduletype": scheduleType,
                            "scheduledata": {**schedue_data, **{"taskname": scantype.name, "taskid": jobId}},
                            "scantype": "Scheduler"}
                    if agent["agent_type"] == 4:
                        # for companyRef in schedulerDbData.get("companyRef", []):
                        #     work["scheduledata"]["companyid"] = companyRef["id"]
                        work['companyid'] = ''
                        resp = await redisIns.lpush(agent["_id"] + "_work", json.dumps(work))
                    else:
                        resp = await redisIns.lpush(agent["_id"] + "_work", json.dumps(work))
            # redisIns.close()
        else:
            if not isinstance(schedulerData, dict):
                schedulerData = schedulerData.dict()
            if scheduleType and 'isActive' in schedulerData and schedulerData['isActive']:
                scanType = schedulerData.get('scanType', '')
                schSettings = schedulerData['settings']
                schType = schedulerData.get('scheduler', '')

                hour = schSettings.get('hour', 0)
                if isinstance(hour, list):
                    if hour:
                        hour = hour[0]
                    else:
                        hour = 0
                hour = int(hour)

                minute = schSettings.get('mins', 0)
                if isinstance(minute, list):
                    if minute:
                        minute = minute[0]
                    else:
                        minute = 0
                minute = int(minute)

                schargs = {}
                if schType == "every_15_mins":
                    schargs = {'hour': '*', 'minute': '*/15', 'second': random.randint(5, 55)}
                elif schType == "hourly":
                    schargs = {'hour': '*/1', 'minute': 2, 'second': random.randint(5, 55)}
                elif schType == "daily" or schType == "every_day":
                    schargs = {'hour': hour, 'minute': minute, 'second': random.randint(5, 55)}
                elif schType == "monthly":
                    schargs = {'hour': hour, 'minute': minute, 'second': random.randint(5, 55)}
                    days = schSettings.get('days', [])
                    if days:
                        days = ",".join(str(day) for day in days)
                        schargs['day'] = days
                elif schType == "days_in_a_month":
                    schargs = {'hour': hour, 'minute': minute, 'second': random.randint(5, 55)}
                    if schSettings.get('days', []):
                        schargs['day'] = ",".join(str(day) for day in schSettings.get('days', []))
                elif schType == "weekly":
                    weekdayMap = {"1": "1st", "2": "2nd", "3": "3rd", "4": "4th", "5": "5th"}
                    schargs = {'hour': hour, 'minute': minute, 'second': random.randint(5, 55)}
                    weekDays = schSettings.get('weekdays', [])
                    weekDayNames = {"0": "sun", "1": "mon", "2": "tue", "3": "wed", "4": "thu", "5": "fri", "6": "sat"}
                    days = []
                    weeks = [weekdayMap[str(week)] for week in schSettings.get("week", [])]
                    for week_day in weekDays:
                        for week in weeks:
                            days.append("%s %s" % (week, weekDayNames.get(str(week_day), str(week_day))))
                    if days:
                        schargs['day'] = ",".join(str(day) for day in days)
                elif schType == "yearly":
                    schargs = {'hour': hour, 'minute': minute, 'second': random.randint(5, 55)}
                    if schSettings.get('days', []):
                        schargs['day'] = ",".join(str(day) for day in schSettings.get('days', []))
                    schargs['month'] = ",".join(str(day) for day in schSettings.get('months', []))
                else:
                    return False, "%s is not a supported scheduler format" % scanType
                basedoc = {}
                for param in templateData['params']:
                    if param["key"] == "companyRef":
                        basedoc["companyid"] = [comp["id"] for comp in schedulerData.get(param["key"], param["type"])]
                    elif param["key"] == "agentRef":
                        basedoc["agentid"] = [comp["id"] for comp in schedulerData.get(param["key"], param["type"])]
                    else:
                        basedoc[param["param"]] = schedulerData.get(param["key"], param["type"])
                basedoc.update(templateData.get('defaultKeys', {}))
                urldata = {"urldata": {"baseurl": serving_domain, "doc": basedoc, "url": templateData['url']},
                           "executionData": {"verb": templateData.get("verb", ""), "path": templateData.get("path", ""),
                                             "method": templateData.get("method", "")}}
                datadoc = {'func': 'webcall', 'cron': schargs, 'type': 'addjob', 'jobId': jobId,
                           'kwargs': urldata}
                redisIns = await aioredis.create_redis("redis://localhost:6379"),
                redisIns = redisIns[0]
                redisIns.xadd('CyberCNS.Schedulerconfiguration', {"doc": json.dumps(datadoc)})
                redisIns.close()
                return True, "Schedule jobs sent"
            else:
                datadoc = {'type': 'deletejob', 'jobId': jobId}
                redisIns = await aioredis.create_redis("redis://localhost:6379"),
                redisIns = redisIns[0]
                redisIns.xadd('CyberCNS.Schedulerconfiguration', {"doc": json.dumps(datadoc)})
                redisIns.close()
            return False, "Success"

    async def getScheduledActionsParams(self, agent_ins, scheduler_ins, agentId):
        schedulers = []
        agentData = await agent_ins().get(agentId)
        if not isinstance(agentData, dict):
            agentData = agentData.dict()
        companies = []
        scheduleTemplates = await self.getScheduleTemplates(False)
        scheduleTemplates = {record["uniqueId"]: record for record in scheduleTemplates}
        if agentData["agent_type"] == 4:
            query = Helpers.buildElsQuery({"uniqueid.keyword": "external_scan"},
                                          mustExpression=[{"exists": {"field": "uniqueid"}},
                                                          {"exists": {"field": "settings"}}])
            params = framework.queryparams.QueryParams()
            params.limit = 10000
            params.skip = 0
            params.q = json.dumps(query)
            resp = await scheduler_ins().get_all(params)
            for record in resp['data']:
                if record['settings'].get("hours"):
                    if not record["settings"].get("mins"):
                        record["settings"]["mins"] = [1]
                schedulers.append({**record["settings"], **{"taskname": cybercns_enum.ScanType(4).name, "taskid": record['_id']}})
            # # Getting all agent level schedulers
        else:
            # companies.append(agentData["companyRef"]["id"])
            # for companyId in companies:
            #     print(companyId)
            companyId = agentData["companyRef"]["id"]
            # Getting all company level schedulers
            must = {'companyRef.id.keyword': companyId, "isGlobal": False}
            must_not = {}
            if agentData["agent_type"] == 4:
                must["uniqueid.keyword"] = "external_scan"
            else:
                must_not["uniqueid.keyword"] = "external_scan"
            query = Helpers.buildElsQuery(must, mustExpression=[{"exists": {"field": "uniqueid"}},
                                                                {"exists": {"field": "settings"}}], must_not=must_not)
            params = framework.queryparams.QueryParams()
            params.limit = 10000
            params.skip = 0
            params.q = json.dumps(query)
            resp = await scheduler_ins().get_all(params)
            for record in resp['data']:
                if scheduleTemplates[record["uniqueid"]].get("defaultKeys", {}).get('scantype'):
                    if record['settings'].get("hours"):
                        if not record["settings"].get("mins"):
                            record["settings"]["mins"] = [1]
                    schedulers.append({**record["settings"], **{"taskname": cybercns_enum.ScanType(scheduleTemplates[record["uniqueid"]]["defaultKeys"]['scantype']).name, "taskid": record['_id']}})
            # # Getting all agent level schedulers
            query = Helpers.buildElsQuery({'agentRef.id.keyword': agentId, "isGlobal": False},
                                          mustExpression=[{"exists": {"field": "scantype"}},
                                                          {"exists": {"field": "settings"}}])
            params = framework.queryparams.QueryParams()
            params.limit = 10000
            params.skip = 0
            params.q = json.dumps(query)
            resp = await scheduler_ins().get_all(params)
            for record in resp['data']:
                if not record.get('scantype'):
                    continue
                if record['settings'].get("hours"):
                    if not record["settings"].get("mins"):
                        record["settings"]["mins"] = [1]
                schedulers.append(
                    {**record["settings"], **{"taskname": cybercns_enum.ScanType(record['scantype']).name}})
            # Getting all global schedulers
            must = {"isGlobal": True}
            must_not = {}
            if agentData["agent_type"] == 4:
                must["uniqueid.keyword"] = "external_scan"
            else:
                must_not["uniqueid.keyword"] = "external_scan"
            query = Helpers.buildElsQuery(must,
                                          mustExpression=[{"exists": {"field": "uniqueid"}},
                                                          {"exists": {"field": "settings"}}], must_not=must_not)
            params = framework.queryparams.QueryParams()
            params.limit = 10000
            params.skip = 0
            params.q = json.dumps(query)
            resp = await scheduler_ins().get_all(params)
            for record in resp['data']:
                if not record.get('scantype'):
                    continue
                if scheduleTemplates[record["uniqueid"]].get("defaultKeys", {}).get('scantype'):
                    if record.get('scheduler') != "hourly":
                        if record['settings'].get("hours"):
                            del record['settings']['hours']
                    if record['settings'].get("hours"):
                        if not record["settings"].get("mins"):
                            record["settings"]["mins"] = [1]
                    schedulers.append(
                        {**record["settings"], **{"taskname": cybercns_enum.ScanType(record['scantype']).name, "taskid": record['_id']}})
        return schedulers

    async def getSublevelData(self, sublevel):
        tempData = {}
        if sublevel == "reports":
            reports_list = [{"name": "All", "value": "*"}]
            reports = await reportProcessor.ReportGenerator().getReportsList()
            for section in reports:
                for report in section['Reports']:
                    reports_list.append(
                        {"name": "%s(%s)" % (report['title'], section['Section']), "value": report['title']})
            tempData["sublevel"] = True
            tempData["sublevelData"] = {"key": "reports_titles", "title": "Select Reports", "isReq": True,
                                        "options": reports_list}
        return tempData

    async def getScheduleTemplates(self, detailed=True):
        with open(f"{framework.settings.smartrecon_path}scheduleTemplate.json") as f:
            scheduleTemplates = json.load(f)
        if detailed:
            for record in scheduleTemplates:
                if record.get('sublevel'):
                    record.update(await self.getSublevelData(record['sublevel']))
        return scheduleTemplates


class QuickScanner():
    def getResults(self, hostname):
        filename = f"/data/externalscanresults/{hostname}.json"
        if not os.path.exists(filename):
            return False, "Results Not Available"
        with open(filename) as f:
            return True, json.load(f)
        # todo:- convert to the format which ui required

    async def startScan(self, hostname, force=False):
        filename = f"/data/externalscanresults/{hostname}.json"
        if not force and os.path.exists(filename) and os.stat(filename).st_size > 0:
            if int(datetime.datetime.now().strftime('%s')) - int(os.stat(filename).st_mtime) < (60 * 60 * 6):
                return self.getResults(hostname)
        cmd = f"/data/CyberCNSAgentV2/cybercnsagentv2_linux --externalAssetArguments {hostname}#@#{filename}"
        # print(cmd)
        status, out, err = await Helpers.asyncioExecute(cmd)
        # print(status, out, err)
        return self.getResults(hostname)

