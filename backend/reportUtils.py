import framework.queryparams
import framework.postgresmodel
import os
import Helpers
import reportProcessor
from docx.shared import Mm
from docxtpl import InlineImage
import apiProcessor
import graphGenerator
import json
from collections import defaultdict


class PptxExternalCalls():
    def __init__(self):
        self.reportpath = "/data/agents/runtimereports"
        if not os.path.exists(self.reportpath):
            os.makedirs(self.reportpath)
        self.reportTemplatePath = "/data/ReportTpl"
        self.ins = framework.postgresmodel.PostgresModel()
        self.ins.Config.collection_name = 'test'
        self.process = reportProcessor.ReportGenerator()

    async def overallriskScore(self, shape, transformeddata, extraparams):
        # inserting last and current month score and deleting remaining shapes
        currentGrade = transformeddata.get("currentGrade", [{}])
        lastGrade = transformeddata.get("lastGrade", [{}])
        currentGrade = currentGrade[0] if currentGrade else {}
        lastGrade = lastGrade[0] if lastGrade else {}
        riskScore = {'currentGrade': await self.process.letterGrade(
            currentGrade.get("company_score", 0)),
                     'lastGrade': await self.process.letterGrade(
                         lastGrade.get("company_score", 0))}
        if shape.name in ['currentGrade', 'lastGrade']:
            await self.process.insertPptxText(shape, riskScore[shape.name])
        if shape.name in ["decreased", "increased", "unchanged", "gradeStatus"]:
            if riskScore['currentGrade'] > riskScore['lastGrade']:
                if shape.name == "gradeStatus":
                    await self.process.insertPptxText(shape, "Decreased")
                elif shape.name in ["increased", "unchanged"]:
                    await self.process.deletePptxShape(shape)
            elif riskScore['currentGrade'] < riskScore['lastGrade']:
                if shape.name == "gradeStatus":
                    await self.process.insertPptxText(shape, "Increased")
                elif shape.name in ["decreased", "unchanged"]:
                    await self.process.deletePptxShape(shape)
            else:
                if shape.name == "gradeStatus":
                    await self.process.insertPptxText(shape, "Unchanged")
                elif shape.name in ["increased", "decreased"]:
                    await self.process.deletePptxShape(shape)

    async def vulSevTrending(self, shape, transformeddata, extraparams):
        critical = [x.get("CRITICAL", {}).get("value", 0) if x.get("CRITICAL", {}).get("value", 0) else 0 for x in
                    transformeddata.get("resp", [])]
        high = [x.get("HIGH", {}).get("value", 0) if x.get("HIGH", {}).get("value", 0) else 0 for x in
                transformeddata.get("resp", [])]
        label = [dates.get('key_as_string', "") for dates in transformeddata.get("resp", [])]
        await self.process.insertPptxChart(shape, {"labels": label, "values": {"CRITICAL": critical, "HIGH": high}})
        if len(label) > 1 and sum(high) + sum(critical):
            return 1
        else:
            return 0

    async def osVulsChart(self, shape, transformeddata, extraparams):
        data = await apiProcessor.RemediationProcessor().getCompanyVulnerabilities(transformeddata.get("companyid"))
        data = sorted(data, key=lambda x: (x['critical_vuls'], x['high_vuls'], x['medium_vuls'], x['low_vuls']),
                      reverse=True)
        labels = []
        values = {"Critical": [], "High": [], "Medium": [], "Low": []}
        for os in data[:5]:
            labels.append(os.get("osname", ""))
            values["Critical"].append(os.get("critical_vuls", 0))
            values["High"].append(os.get("high_vuls", 0))
            values["Medium"].append(os.get("medium_vuls", 0))
            values["Low"].append(os.get("low_vuls", 0))
        await self.process.insertPptxChart(shape, {"labels": labels, "values": values})
        if len(labels) and sum(values["Critical"]) + sum(values["High"]) + sum(values["Medium"]) + sum(values["Low"]):
            return 1
        else:
            return 0


class DocxExternalCalls():
    def __init__(self):
        self.reportpath = "/data/agents/runtimereports"
        if not os.path.exists(self.reportpath):
            os.makedirs(self.reportpath)
        self.reportTemplatePath = "/data/ReportTpl"
        self.ins = framework.postgresmodel.PostgresModel()
        self.ins.Config.collection_name = 'test'
        self.ins_timeseries = framework.postgresmodel.PostgresModel()
        self.ins_timeseries.Config.collection_name = 'test_timeseries'
        self.process = reportProcessor.ReportGenerator()

    async def vulSevrend(self, tpl, data, graphtype):
        keys = [x.get("key_as_string", "") for x in data]
        critical = [x.get("CRITICAL", {}).get("value", 0) if x.get("CRITICAL", {}).get("value", 0) else 0 for x in
                    data]
        high = [x.get("HIGH", {}).get("value", 0) if x.get("HIGH", {}).get("value", 0) else 0 for x in data]
        if len(keys) > 1 and sum(critical) + sum(high):
            if graphtype == "area":
                imageFile = await graphGenerator.areaStack("Vulnerability Trending", keys, [critical, high],
                                                           ["CRITICAL", "HIGH"], ["#10adea", "#0ebbd2"])
            else:
                imageFile = await graphGenerator.lineStack("Severity Trending", keys, [critical, high],
                                                           ["CRITICAL", "HIGH"], ["#10adea", "#0ebbd2"])
            return {"image": InlineImage(tpl, imageFile, height=Mm(100))}, [imageFile]
        else:
            return {"image": ""}, []

    async def networkScanFindings(self, tpl, extractedData, extraparams):
        extractedData["networkfinding"] = await apiProcessor.RemediationProcessor().getNetworkVulsData(
            extractedData.get("companyid", ""))
        return extractedData, []

    async def externalScanAndSsl(self, tpl, extractedData, extraparams):
        certs = []
        for data in extractedData.get("externalScan", []):
            self.ins.Config.collection_name = 'test_timeseries'
            index = await self.ins.collection_name()
            params = framework.queryparams.QueryParams()
            params.limit = 1
            params.fields = []
            params.skip = 0
            params.sort = json.dumps([{"u": {"order": "desc"}}])
            params.q = json.dumps({"query": {"bool": {
                "must": [{"exists": {"field": "uniqueid"}}, {"exists": {"field": "ciphers"}},
                         {"match": {"companyRef.id.keyword": extractedData["companyid"]}},
                         {"match": {"assetRef.id.keyword": data["_id"]}}]}}})
            sslData = (await self.ins.get_all(params)).get("data", [])
            sslData = sslData[0] if sslData else {}
            self.ins.Config.collection_name = 'test'
            index = await self.ins.collection_name()
            params = framework.queryparams.QueryParams()
            params.limit = 1000
            params.fields = ["title", "severity", "port", "score.cvss_score"]
            params.skip = 0
            params.sort = json.dumps([{"u": {"order": "desc"}}])
            params.q = json.dumps({"query": {"bool": {
                "must": [{"exists": {"field": "vul_id"}}, {"exists": {"field": "score.cvss_score"}},
                         {"range": {"score.cvss_score": {"gt": 0}}},
                         {"match": {"companyRef.id.keyword": extractedData["companyid"]}},
                         {"match": {"assetRef.id.keyword": data["_id"]}}]}}})
            assetvuls = (await self.ins.get_all(params)).get("data", [])
            assetvuls.sort(
                key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(x['severity'].strip().upper(), 4))
            if sslData and assetvuls:
                sslData["sslCert"] = sslData["sslCert"] if sslData.get("sslCert") else {}
                sslData["sslCert"]["ext_key_usage"] = ", ".join(sslData.get("sslCert", {}).get("ext_key_usage", []))
                sslData["sslCert"]["subjectAltNames"] = ", ".join(sslData.get("sslCert", {}).get("subjectAltNames", []))
                for addcerts in sslData.get("additional_certs", []):
                    addcerts["ext_key_usage"] = ", ".join(addcerts.get("ext_key_usage", []))
                    addcerts["subjectAltNames"] = ", ".join(addcerts.get("subjectAltNames", []))
                sslData["assetvuls"] = assetvuls
                certs.append(sslData)
        extractedData["sslData"] = certs
        return extractedData, []

    async def diskUsage(self, data):
        for k, v in {"0-25 %": "0.0-25.0", "25-50 %": "25.0-50.0", "50-75 %": "50.0-75.0",
                     "75-100 %": "75.0-101.0"}.items():
            data[k] = data.pop(v)
        return data

    async def executiveSummary(self, tpl, extractedData, extraparams):
        chartimage = []
        extractedData["vulTrending"], images = await self.vulSevrend(tpl, extractedData.get("vulTrending", []), "area")
        chartimage.extend(images)
        extractedData["sevTrending"], images = await self.vulSevrend(tpl, extractedData.get("sevTrending", []), "line")
        chartimage.extend(images)
        if extractedData.get("diskUsage", {}):
            extractedData["diskUsage"] = await self.diskUsage(extractedData.get("diskUsage", {}))
        return extractedData, chartimage

    async def assetLevelMissingPatches(self, tpl, extractedData, extraparams):
        extractedData, chartImages = await self.remediationGraph(tpl, extractedData, extraparams)
        assetList = defaultdict(list)
        for remediations in await apiProcessor.RemediationProcessor().getCompanyRemediationPolicy(
                extractedData.get("companyid", "")):
            for assets in remediations.get("assets"):
                if int(remediations.get("vulsCount", 0)):
                    assetList[assets.get("name", "") + "~id~" + assets.get("id", "")].append(
                        {"os": remediations.get("product", ""),
                         "version": assets.get("evidence", {}).get("version", "-"),
                         "critical": int(remediations.get("critical_vuls_count", 0)),
                         "high": int(remediations.get("high_vuls_count", 0)),
                         "medium": int(remediations.get("medium_vuls_count", 0)),
                         "low": int(remediations.get("low_vuls_count", 0)),
                         "total": int(remediations.get("vulsCount", 0))})
        assetFinal = []
        for k, v in assetList.items():
            try:
                client = await self.ins.client()
                assetData = (await client.get(index=await self.ins.collection_name(), id=k.split("~id~")[1],
                                              _source=["host.ip", "vul_stats.asset_score"])).get("_source")
                assetFinal.append({
                    "asset": k.split("~id~")[0],
                    "applications": sorted(v,
                                           key=lambda x: (x['critical'], x['high'], x['medium'], x['low']),
                                           reverse=True),
                    "vulTotal": sum([x.get("total", 0) for x in v]),
                    "ip": assetData.get("host", {}).get("ip", 0),
                    "assetscore": await self.process.letterGrade(
                        assetData.get("vul_stats", {}).get("asset_score", 0))})
            except Exception as e:
                print(k, e)
        currentGrade = extractedData.get("currentGrade", [{}])
        lastGrade = extractedData.get("lastGrade", [{}])
        currentGrade = currentGrade[0] if currentGrade else {}
        lastGrade = lastGrade[0] if lastGrade else {}
        extractedData['currentGrade'] = await self.process.letterGrade(
            currentGrade.get("company_score", 0))
        extractedData['lastGrade'] = await self.process.letterGrade(
            lastGrade.get("company_score", 0))
        extractedData["assetData"] = sorted(assetFinal, key=lambda x: (x['vulTotal']), reverse=True)
        return extractedData, chartImages

    async def assetReport(self, tpl, extractedData, extraparams):
        for assets in extractedData.get("assetTable", []):
            query = Helpers.buildElsQuery({"assetRef.id.keyword": assets.get("_id", "")},
                                          mustExpression=[{"exists": {"field": "mountpoint"}},
                                                          {"exists": {"field": "device"}}])

            query["size"] = 1
            client = await self.ins.client()
            await self.ins.collection_name()
            assets["os"] = {"full_name": assets.get("os", {}).get("full_name", ""),
                            "version": assets.get("os", {}).get("version", "")}
            ram = assets.get("host", {}).get("physical_memory")
            assets["host"] = {"host_name": assets.get("host", {}).get("host_name", ""),
                              "ip": assets.get("host", {}).get("ip", ""),
                              "cpu_core": assets.get("host", {}).get("cpu_core", "")}
            assets["ram"] = str(round(int(ram) / 1073741824, 1, )) + " GB" if ram else ""
            for response in (await client.search(index=await self.ins.collection_name(),
                                                 body=query)).get("hits", {}).get("hits", []):
                used = response.get("_source", {}).get("used")
                assets["used"] = str(round(int(used) / 1073741824, 1, )) + " GB" if used and isinstance(used,
                                                                                                        int) else ""
                free = response.get("_source", {}).get("free")
                assets["free"] = str(round(int(free) / 1073741824, 1, )) + " GB" if free and isinstance(free,
                                                                                                        int) else ""
                total = response.get("_source", {}).get("total")
                assets["total"] = str(round(int(total) / 1073741824, 1, )) + " GB" if total and isinstance(total,
                                                                                                           int) else ""
                assets["encryption"] = {0: "Not Encrypted",
                                        1: "Encrypted",
                                        2: "Unknown"}.get(response.get("_source", {}).get("encrypted", ""), "")
        return extractedData, []

    async def remediationGraph(self, tpl, extractedData, extraparams):
        chartImages = []
        graph = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for remediations in await apiProcessor.RemediationProcessor().getCompanyRemediationPolicy(
                extractedData.get("companyid", "")):
            graph["CRITICAL"] += remediations.get("critical_vuls_count", 0)
            graph["HIGH"] += remediations.get("high_vuls_count", 0)
            graph["MEDIUM"] += remediations.get("medium_vuls_count", 0)
            graph["LOW"] += remediations.get("low_vuls_count", 0)
        values = [round(v) for k, v in graph.items()]
        if sum(values):
            imageFile = await graphGenerator.pieChart(keys=[k for k, v in graph.items()],
                                                      values=values,
                                                      colours=["#10adea", "#0ebbd2", "#0ed287", "#a2e215"])
            extractedData["summaryChart"] = {"image": InlineImage(tpl, imageFile, height=Mm(100))}
            chartImages.append(imageFile)
        else:
            extractedData["summaryChart"] = {"image": ""}
        return extractedData, chartImages


class XlsxExternalCalls():
    def __init__(self):
        self.reportpath = "/data/agents/runtimereports"
        if not os.path.exists(self.reportpath):
            os.makedirs(self.reportpath)
        self.ins = framework.postgresmodel.PostgresModel()
        self.ins.Config.collection_name = 'test'
        self.ins_timeseries = framework.postgresmodel.PostgresModel()
        self.ins_timeseries.Config.collection_name = 'test_timeseries'
        self.process = reportProcessor.ReportGenerator()

    async def assetReportXlsx(self, extractedData, extraparams):
        extractedData, list = await DocxExternalCalls().assetReport({}, extractedData, "")
        return extractedData

    async def installedPrograms(self, extractedData, extraparams):
        versummary = []
        for pgms in extractedData.get("versionSummary", []):
            for versions in pgms.get("assets", {}).get("buckets", []):
                versummary.append({"name": pgms.get("key", ""),
                                   "version": versions.get("key", ""),
                                   "count": versions.get("doc_count", 0)})
            if not pgms.get("buckets", []):
                versummary.append({"name": pgms.get("key", ""),
                                   "version": "",
                                   "count": 0})
        extractedData["versionSummary"] = versummary
        return extractedData

    async def activeDirectoryUserTransforms(self, extractedData, extraparams):
        extractedData["usersdomainAdmin"], extractedData["usersenterpriseAdmin"] = [], []
        for users in extractedData.get("allUsers", []):
            dataDict = {"samAccountName": users.get("samAccountName", ""), "name": users.get("name", ""),
                        "lastLogonTimestamp": users.get("lastLogonTimestamp", ""),
                        "distinguishedName": users.get("distinguishedName", ""),
                        "emailAddress": users.get("emailAddress", ""), "domain": users.get("domain", "")}
            if "cn=domain admins" in ",".join(users.get("memberOf", [])).lower() or users.get("domainAdmin", False):
                users["domainAdmin"] = True
                extractedData["usersdomainAdmin"].append(dataDict)
            if "cn=enterprise admins" in ",".join(users.get("memberOf", [])).lower() or users.get("enterpriseAdmin",
                                                                                                  False):
                users["enterpriseAdmin"] = True
                extractedData["usersenterpriseAdmin"].append(dataDict)
        return extractedData

