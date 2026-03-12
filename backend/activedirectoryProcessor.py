import framework
import os
import csv
import json
import gzip
import yaml
import uuid
import redis
import Helpers
import datetime
import cybercns_enum
from io import StringIO
import ad_object_schema
import agentCommunicator
from dateutil import parser
import framework.queryparams
import framework.postgresmodel
from elasticsearch import helpers
from collections import defaultdict
logger = framework.Logger.getInstance('activedirectoryprocessor')


class ActiveDirectoryProcessor():
    def _getReferenceData(self, filename):
        companydetails = filename.strip().split("#@#")
        companyid = companydetails[0]
        agentid = companydetails[1]
        jobid = ""
        credid = ""
        if len(companydetails) > 3:
            jobid = companydetails[2]
        if len(companydetails) > 4:
            credid = companydetails[3]
        referenceData = {"companyRef": {"id": companyid}, "agentRef": {"id": agentid}}
        return referenceData, jobid, credid

    async def runpostFixes(self, indexName, companyid, agentid, jobid="", credid=""):
        logger.info("Run Post Fixes indexName:- %s companyid:- %s agentid:- %s jobid:- %s, credid:- %s" %
                    (indexName, companyid, agentid, jobid, credid))
        data = {}
        params = framework.queryparams.QueryParams()
        params.limit = 10000
        params.skip = 0
        ins = framework.postgresmodel.PostgresModel()
        ins.Config.collection_name = indexName

        for object_type in ["ad_users", "ad_groups", "ad_ou", "ad_gpo", "ad_computers"]:
            must = {'object_type.keyword': object_type, 'companyRef.id.keyword': companyid,
                    'agentRef.id.keyword': agentid}
            query = Helpers.buildElsQuery(must, mustExpression={"exists": {"field": "object_type"}})
            params.q = json.dumps(query)
            response = await ins.get_all(params)
            data[object_type] = response['data']
        ousInGpos = defaultdict(list)
        gpoMap = {rec['guid']: rec for rec in data['ad_gpo'] if rec.get('guid')}
        adLoops = {'ad_users': defaultdict(list),
                   'ad_groups': defaultdict(list),
                   'ad_computers': defaultdict(list)}
        finalData = []
        for k, v in adLoops.items():
            for collection in data.get(k, []):
                linkedOu = [x[3:] for x in collection.get("distinguishedName", "").split(",") if "OU=" in x]
                if linkedOu:
                    finalData.append({"_op_type": "update", "_id": collection["_id"],  "_index": await ins.collection_name(), "doc": {"linkedOus": linkedOu}})
                    for codata in linkedOu:
                        if codata and collection.get("samAccountName", '') not in v.get(codata[3:], []):
                            v[codata].append(collection.get("samAccountName", ''))
        for ous in data.get('ad_ou', []):
            tmpdict = {}
            if 'linkedGPO' not in ous or not ous.get('linkedGPO'):
                tmpdict['linkedGPO'] = []
                tmpdict["_id"] = ous['_id']
            if ous.get('gpLinks'):
                for link in ous['gpLinks']:
                    if link in gpoMap:
                        if 'linkedGPO' not in tmpdict:
                            tmpdict['linkedGPO'] = []
                        tmpdict['linkedGPO'].append({"name": gpoMap[link]["displayName"], "enforced": False,
                                                     "enabled": True if gpoMap[link].get("status", "") == "enabled" else False})
                ous['linkedGPO'] = tmpdict.get('linkedGPO', [])
                tmpdict["_id"] = ous['_id']
            for object_type in ['ad_computers', 'ad_groups', 'ad_users']:
                tmp = adLoops[object_type].get(ous.get("ouName", ""), [])
                if tmp:
                    tmpdict["linked" + object_type.split("ad_")[-1].title()] = tmp
                    tmpdict["_id"] = ous.get("_id", "")
            for gpos in ous.get('linkedGPO', []):
                if ous.get("ouName", "") not in ousInGpos[gpos.get("name", "")]:
                    ousInGpos[gpos.get("name", "")].append(ous.get("ouName", ""))
            if tmpdict:
                id = tmpdict['_id']
                del tmpdict['_id']
                finalData.append({"_op_type": "update", "_id": id, "_index": await ins.collection_name(),
                                  "doc": tmpdict})
        for gpos in data.get('ad_gpo', []):
            tmpdict = {}
            tmp = ousInGpos.get(gpos.get("displayName"), [])
            if tmp:
                tmpdict["_id"] = gpos["_id"]
                tmpdict["linkedOus"] = tmp
                finalData.append({"_op_type": "update", "_id": gpos["_id"], "_index": await ins.collection_name(),
                                  "doc": {"linkedOus": tmp}})
        step = 300
        client = await ins.client()
        for start in range(0, len(finalData), step):
            try:
                print(await helpers.async_bulk(
                    client, finalData[start:start + step], chunk_size=1000, request_timeout=200
                ))
            except Exception as e:
                logger.info("Exception in ad audit bulk upload %s" % e)

        if credid and jobid:
            query = Helpers.buildElsQuery({"_id": credid})
            params = framework.queryparams.QueryParams()
            params.limit = 1
            params.skip = 0
            params.q = json.dumps(query)
            credentials = await ins.get_all(params)
            must = {'object_type.keyword': "ad_computers", 'companyRef.id.keyword': companyid,
                    'agentRef.id.keyword': agentid, "assetcredentialsRef.id.keyword": credid}
            query = Helpers.buildElsQuery(must, mustExpression={"exists": {"field": "object_type"}})
            params = framework.queryparams.QueryParams()
            params.limit = 10000
            params.skip = 0
            params.q = json.dumps(query)
            response = await ins.get_all(params)
            extraData = {}

            scanIps = [computer["name"] for computer in response['data'] if computer.get('name')]
            for computer in response['data']:
                comp_info = {"host": computer['name'], "hostname": [{"name": computer["name"], "source": "ad"}],
                             "ostype": "windows"}
                extraData[comp_info["host"]] = comp_info
            scanData = {"extradata": extraData, "scanlist": scanIps, "jobId": jobid,
                        "taskName": "Active Directory Asset Inventory Scan", "ostype": "windows",
                        "scantype": "FullScan", "companyid": companyid, "scanrange": "",
                        "portstodiscard": await agentCommunicator.AgentCommunicator()._getExcludedPorts(companyid)}
            if credentials['data']:
                for cred in credentials['data']:
                    cred["credId"] = cred["_id"]
                    cred['driver'] = cybercns_enum.CredType(cred['cred_type']).name.lower()
                    del cred['_id']
                scanData["mastercredentils"] = {"windows": credentials["data"]}
                scanData['scanrange'] = credentials["data"][0]["domain"]
            redisIns = redis.Redis()
            resp = redisIns.lpush(agentid + "_work", json.dumps(scanData))
            redisIns.close()

    async def saveAdObjects(self, upload_file, cls_ins, object_type):
        referenceData, jobid, credid = self._getReferenceData(upload_file.filename)
        Helpers.execute("mkdir -p /data/cybertemp/activedirectorylogs")
        filename = os.path.join("/data/cybertemp/activedirectorylogs", upload_file.filename)
        with open(filename, "w+") as f:
            filecontent = gzip.open(upload_file.file, encoding='utf-8-sig', mode='rt').read()
            f.write(filecontent)
        objectData = json.loads(filecontent)
        if objectData.get('status'):
            if isinstance(objectData.get('data'), dict):
                objectData['data'] = [objectData['data']]

            collection_data = [{**Helpers.cast_datatype(i, eval(f"ad_object_schema.{object_type}")),
                                **referenceData,
                                **{"object_type": object_type}} for i in
                               objectData.get('data')]
            if credid:
                collection_data = [{**record, **{"assetcredentialsRef": {"id": credid}}} for record in collection_data]
            domain_name = collection_data[0]['domain']
            must = {'object_type.keyword': object_type, 'companyRef.id.keyword': referenceData["companyRef"]['id'],
                    'domain.keyword': domain_name}
                    # 'agentRef.id.keyword': referenceData["agentRef"]['id']}
            # if credid:
            #     must.update({"assetcredentialsRef.id.keyword": credid})
            query = Helpers.buildElsQuery(must, mustExpression={"exists": {"field": "object_type"}})
            client = await cls_ins().client()
            await client.delete_by_query(index=await cls_ins().collection_name(), body=query)

            [await cls_ins(**x).create() for x in collection_data]
        else:
            logger.info("Got Failed Status For Object %s" % object_type)

    async def uploadAdevents(self, els_ins, eventdata, companydata, agentdata):
        dict_reader = csv.DictReader(StringIO(eventdata), delimiter='|',
                                     fieldnames=['channel', 'datetime', 'task', 'level', 'provider_name',
                                         'provider_guid', 'domain', 'eventid', 'keywords', 'data', 'pid', 'tid'])

        # load the query template for active directory.
        if not os.path.exists("/data/agents/templateData/ADAudit/ccns-event-conf.yaml"):
            return []

        config_ = {}
        with open("/data/agents/templateData/ADAudit/ccns-event-conf.yaml", "r") as f:
            for k in yaml.safe_load(f).get("Events", []):
                config_[str(k['EventID'])] = {"Description": k['Description'], "Channel": k['Channel']}

            if k.get('Fields'):
                config_[str(k['EventID'])].update({"Fields": k['Fields']})

            if k.get('Filter'):
                config_[str(k['EventID'])].update({"Filters": {k['Filters']['Field']: set(k['Filters']['Value'])}})

            if k.get('Mapping'):
                config_[str(k['EventID'])].update({"Mapping": {k['Mapping']['Field']: k['Mapping']['Value']}})

        c = u = datetime.datetime.utcnow()
        base_doc = {
            "_index": f"test_{framework.ctx['tenant']}_ad_audit", "c": c, "u": u,
            "companyRef": {"id": companydata['id'], "name": companydata["name"]},
            "agentRef": {"id": agentdata["id"], "name": agentdata["host_name"]}
        }
        save_events = []
        for i in dict_reader:
            if not config_.get(i['eventid']):
                continue

            try:
                data = json.loads(i['data']).get('EventData')
                if not data:
                    continue
            except ValueError:
                continue

            event_info = config_[i['eventid']]
            tmp = {
                "Description": event_info['Description'], "Channel": event_info['Channel'], "EventID": i['eventid'],
                "EventDatetime": parser.parse(i['datetime']),
            }

            # Retain only fields defined in the config.yaml file & discard others...
            try:
                for k, v in data.items():
                    if k in event_info['Fields']:
                        tmp[k] = v
            except KeyError:
                tmp.update(data)

            # Filter out fields which does not match config (if filters are configured)..
            try:
                if any(data.get(k) and data[k] in v for k, v in event_info['Filter'].items()):
                    continue  # don't save the records to db & progress the outer for loop..
            except KeyError:
                pass

            try:
                for k, v in event_info['Mapping'].items():
                    if tmp.get(k) and v.get(tmp[k]):
                        tmp[k] = v[tmp[k]]
            except KeyError:
                pass

            save_events.append({**tmp, **base_doc, "_id": str(uuid.uuid4())})
        step = 300
        client = await els_ins.client()
        for start in range(0, len(save_events), step):
            try:
                print(await helpers.async_bulk(
                    client, save_events[start:start + step], chunk_size=1000, request_timeout=200
                ))
            except Exception as e:
                logger.info("Exception in ad audit bulk upload %s" % e)

    async def getAdStats(self, companyid):
        stats_data = {"ad_computers": {"enabled": 0, "disabled": 0, "lastloggedin30d": 0},
                      "ad_users": {"enabled": 0, "disabled": 0, "lastloggedin30d": 0},
                      "ad_groups": {"critical": 0, 'noncritical': 0, "empty": 0},
                      "ad_gpo": {'linked': 0, "unlinked": 0}}
        ins = framework.postgresmodel.PostgresModel()
        ins.Config.collection_name = 'test'
        client = await ins.client()

        # Computers
        query = Helpers.buildElsQuery({"object_type.keyword": 'ad_computers', "enabled": True,
                                       "companyRef.id.keyword": companyid},
                                      mustExpression={"exists": {'field': "object_type"}})
        resp = await client.count(index=await ins.collection_name(), body=query)
        stats_data['ad_computers']['enabled'] = resp['count']
        query = Helpers.buildElsQuery(
            {"object_type.keyword": 'ad_computers', "enabled": False, "companyRef.id.keyword": companyid},
            mustExpression={"exists": {'field': "object_type"}})
        resp = await client.count(index=await ins.collection_name(), body=query)
        stats_data['ad_computers']['disabled'] = resp['count']
        query = Helpers.buildElsQuery(
            {"object_type.keyword": 'ad_computers', "enabled": True, "companyRef.id.keyword": companyid},
            mustExpression=[{"exists": {'field': "object_type"}}, {"range": {"lastLogonDate": {"lte": "now-30d"}}}])
        resp = await client.count(index=await ins.collection_name(), body=query)
        stats_data['ad_computers']['lastloggedin30d'] = resp['count']

        # users
        query = Helpers.buildElsQuery(
            {"object_type.keyword": 'ad_users', "enabled": True, "companyRef.id.keyword": companyid},
            mustExpression={"exists": {'field': "object_type"}})
        resp = await client.count(index=await ins.collection_name(), body=query)
        stats_data['ad_users']['enabled'] = resp['count']
        query = Helpers.buildElsQuery(
            {"object_type.keyword": 'ad_users', "enabled": False, "companyRef.id.keyword": companyid},
            mustExpression={"exists": {'field': "object_type"}})
        resp = await client.count(index=await ins.collection_name(), body=query)
        stats_data['ad_users']['disabled'] = resp['count']
        query = Helpers.buildElsQuery(
            {"object_type.keyword": 'ad_users', "enabled": True, "companyRef.id.keyword": companyid},
            mustExpression=[{"exists": {'field': "object_type"}}, {"range": {"lastLogonDate": {"lte": "now-30d"}}}])
        resp = await client.count(index=await ins.collection_name(), body=query)
        stats_data['ad_users']['lastloggedin30d'] = resp['count']

        # Groups
        query = Helpers.buildElsQuery(
            {"object_type.keyword": 'ad_groups', "isCriticalSystemObj": True, "companyRef.id.keyword": companyid},
            mustExpression={"exists": {'field': "object_type"}})
        resp = await client.count(index=await ins.collection_name(), body=query)
        stats_data['ad_groups']['critical'] = resp['count']
        query = Helpers.buildElsQuery(
            {"object_type.keyword": 'ad_groups', "isCriticalSystemObj": False, "companyRef.id.keyword": companyid},
            mustExpression={"exists": {'field': "object_type"}})
        resp = await client.count(index=await ins.collection_name(), body=query)
        stats_data['ad_groups']['noncritical'] = resp['count']
        query = Helpers.buildElsQuery(
            {"object_type.keyword": 'ad_groups', "empty": True, "companyRef.id.keyword": companyid},
            mustExpression=[{"exists": {'field': "object_type"}}])
        resp = await client.count(index=await ins.collection_name(), body=query)
        stats_data['ad_groups']['empty'] = resp['count']

        # Gpo
        query = Helpers.buildElsQuery(
            {"object_type.keyword": 'ad_gpo', "companyRef.id.keyword": companyid},
            mustExpression=[{"exists": {'field': "object_type"}}, {"exists": {'field': "linkedOus"}}])
        resp = await client.count(index=await ins.collection_name(), body=query)
        stats_data['ad_gpo']['linked'] = resp['count']
        query = Helpers.buildElsQuery(
            {"object_type.keyword": 'ad_gpo', "companyRef.id.keyword": companyid},
            mustExpression={"exists": {'field': "object_type"}},mustNotExpression={"exists":{"field": "linkedOus"}})
        resp = await client.count(index=await ins.collection_name(), body=query)
        stats_data['ad_gpo']['unlinked'] = resp['count']
        return stats_data

