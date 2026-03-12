import json
import redis
import logger
import socket
import base64
import Helpers
import requests
import traceback
import urllib.error
import urllib.parse
import urllib.parse
import urllib.request

logr = logger.Logger.getInstance("connectwise")


class ConnectwiseAPI(object):
    def __init__(self, company, domain, publicKey, privateKey):
        self.company = company
        self.domain = self.cleanupDomain(domain)
        self.codeBase = 'v4_6_Release/'
        self.versionCode = None
        self.calledExecte = 0
        self.publicKey = publicKey
        self.privateKey = privateKey
        self.apiKey = ""
        self.cwClientId = "a76542ce-c2d9-4c16-a16d-5836d11564f2"
        self.errMsg = ''
        self.isConnected = False
        self.partnerId = self.domain + self.company
        self.endpointURL = "https://" + self.getApiDomain(self.domain) + "/" + self.codeBase + "apis/3.0/"

    def validateCredentials(self):
        status, errmsg = Helpers.gethostname(self.domain)
        if not status:
            return False, errmsg
        codebaseUrl = "https://%s/login/companyinfo/%s" % (self.domain, self.company)
        for i in range(2):
            try:
                response = requests.get(codebaseUrl, verify=False, timeout=10)
                if response.status_code == 200:
                    self.isConnected = True
                    decodedContent = json.loads(response.text)
                    if decodedContent:
                        self.codeBase = decodedContent['Codebase']
                        self.versionCode = decodedContent['VersionCode']
                        break
            except Exception as e:
                print(" getManageError: %s" % e)
                print(traceback.format_exc())

        if not self.isConnected:
            return False, "Unable to get partner manage company info"

        self.endpointURL = "https://" + self.getApiDomain(self.domain) + "/" + self.codeBase + "apis/3.0/"
        return True, "Success"

    def cleanupDomain(self, domain):
        # Cleanup the domain and make sure it is fine before inserting to db
        # In one of the issues we had the domain as "na.myconnectwise.net/" instead of just the domain name like "na.myconnectwise.net"
        parsedUrl = urllib.parse.urlparse(domain)
        if parsedUrl.hostname and len(parsedUrl.hostname):
            domain = parsedUrl.hostname.strip('/')
        else:
            domain = domain.strip('/')
        return domain

    def getApiDomain(self, domain):
        """
        API Domain
        """
        if domain.lower() in ['na.myconnectwise.net', 'eu.myconnectwise.net', 'au.myconnectwise.net',
                              'aus.myconnectwise.net', 'za.myconnectwise.net', 'staging.connectwisedev.com']:
            return 'api-' + domain.lower()
        return domain.lower()

    def _execService(self, serviceUrl, method, data=None, files=None):
        """
        Execute manage rest services
        """
        # logr.info(" Called CW Rest API Service: " + str(serviceUrl) + " method: " + str(method))
        if not self.domain or not self.company:
            return False, {"errMsg": "ConnectWise Manage account not configured"}

        if self.errMsg:
            return False, {"errMsg": self.errMsg}

        # PYTHON3: base64.encodestring is deprecated and only takes bytes-string as an arg, so directly used encodebytes method.
        basic_key = self.company + '+' + self.publicKey + ':' + self.privateKey
        auth = base64.encodebytes(basic_key.encode('utf-8')).decode('utf-8').replace('\n', '')

        headers = {'Authorization': 'Basic ' + auth, 'Content-Type': 'application/json; charset=UTF-8',
                   'Cache-Control': 'no-cache', 'x-cw-overridessl': 'true'}
        if files:
            headers = {'Authorization': 'Basic ' + auth, 'x-cw-overridessl': 'true'}

        headers["clientId"] = self.cwClientId

        if method == "GET":
            response = requests.get(serviceUrl, headers=headers, verify=False)
        elif method == "POST":
            if files:
                response = requests.post(serviceUrl, headers=headers, files=files, data=data, verify=False)
            else:
                response = requests.post(serviceUrl, headers=headers, data=json.dumps(data), verify=False)
        elif method == "PUT":
            response = requests.put(serviceUrl, headers=headers, data=json.dumps(data), verify=False)
        elif method == "PATCH":
            response = requests.patch(serviceUrl, headers=headers, data=json.dumps(data), verify=False)
        elif method == "DELETE":
            response = requests.delete(serviceUrl, headers=headers, verify=False)
        else:
            return False, "Invalid input method"
        try:
            content = response.text
            try:
                if content:
                    if response.headers["Content-Type"] != 'application/octet-stream':
                        content = json.loads(content)
                if 'code' in content and (content['code'] == 'Unauthorized' or content['code'] == 'Security'):
                    if "message" in content:
                        return False, {"errMsg": content['message']}
                    elif self.calledExecte == 0:
                        self.calledExecte = 1
                        return False, {"errMsg": content['code']}
                    else:
                        return False, {"errMsg": "Security/Authentication Error"}
            except Exception as err:
                logr.error(" Rest API Exception occured " + str(err))

            if response.status_code in [200, 201, 204]:
                return True, content
            else:
                logr.error(" Error in CW Rest API Service Response : %s " % response.text)
                resp = {}
                errCode = ''
                if not isinstance(content, dict):
                    try:
                        content = json.loads(content)
                    except ValueError:
                        pass
                if "code" in content:
                    errCode = content["code"]
                if 'errors' in content and content['errors'] and content['errors'] != 'null' and 'message' in \
                        content['errors'][0]:
                    errMsg = content['errors'][0]["message"]
                elif 'message' in content:
                    errMsg = content["message"]
                else:
                    errMsg = "Api call failed"
                resp["errMsg"] = errMsg
                resp["errCode"] = errCode
                return False, resp
        except Exception as e:
            logr.error(" manageCallError :%s, \ntraceback :%s" % (e, traceback.format_exc()))
            resp = {}
            resp["errMsg"] = "Unable to connect to connectwise server"
            logr.error(" Exception in CW Rest API Service response : " + str(resp))
            return False, resp

    def get(self, serviceType, serviceUri, fields=None, conditions=None, pageSize=None, page=None, orderBy=None,
            childCondition=None, customFieldCondition=None):
        """
        Connectwise manage get service
        """
        url = self.endpointURL + serviceType + "/" + serviceUri
        pageSize = pageSize if pageSize else 100
        url = url + "?pageSize=" + str(pageSize)
        if page:
            url = url + "&page=" + str(page)
        if orderBy:
            orderBy = self.generateOrderBy(orderBy)
            url = url + "&orderBy=" + urllib.parse.quote_plus(orderBy)
        if conditions:
            url = url + "&conditions=" + urllib.parse.quote_plus(conditions)
        if childCondition:
            url = url + "&childconditions=" + urllib.parse.quote_plus(childCondition)
        if customFieldCondition:
            url = url + "&customFieldConditions=" + urllib.parse.quote_plus(customFieldCondition)
        if fields:
            url = url + "&fields=" + fields

        return self._execService(url, "GET")

    def getReport(self, serviceType, serviceUri, columns=None, conditions=None, pageSize=None, page=None, orderBy=None):
        """
        Connectwise manage get report service
        """
        url = self.endpointURL + serviceType + "/" + serviceUri
        pageSize = pageSize if pageSize else 500
        url = url + "?pageSize=" + str(pageSize)
        if page:
            url = url + "&page=" + str(page)
        if orderBy:
            orderBy = self.generateOrderBy(orderBy)
            url = url + "&orderBy=" + urllib.parse.quote_plus(orderBy)
        if conditions:
            url = url + "&conditions=" + urllib.parse.quote_plus(conditions)
        if columns:
            cols = ','.join(columns.keys())
            url = url + "&columns=" + cols

        status, content = self._execService(url, "GET")

        if status:
            reportData = []

            if "row_values" in content:
                for row_value in content['row_values']:
                    rowData = {}
                    hCnt = 0
                    for row_header in content['column_definitions']:
                        header = list(row_header.keys())[0]
                        if columns and header in columns:
                            header = columns[header]
                        rowData[header] = row_value[hCnt]
                        hCnt = hCnt + 1
                    reportData.append(rowData)
                return True, reportData
        return status, content

    def post(self, serviceType, serviceUri, data, files=None):
        """
        Connectwise manage post service
        """
        url = self.endpointURL + serviceType + "/" + serviceUri
        return self._execService(url, "POST", data, files)

    def modify(self, serviceType, serviceUri, data):
        """
        Connectwise manage modify service
        """
        url = self.endpointURL + serviceType + "/" + serviceUri
        return self._execService(url, "PUT", data)

    def patch(self, serviceType, serviceUri, data):
        """
        Connectwise manage patch service
        """
        url = self.endpointURL + serviceType + "/" + serviceUri
        patchData = []
        for key, val in data.items():
            patchData.append({"op": "replace", "path": key, "value": val})

        return self._execService(url, "PATCH", patchData)

    def delete(self, serviceType, serviceUri):
        """
        Connectwise manage delete service
        """
        url = self.endpointURL + serviceType + "/" + serviceUri
        return self._execService(url, "DELETE")

    def generateOrderBy(self, orderBy):
        """
        Generate order by query
        """
        orderArr = []
        for order_by in orderBy:
            # print orderBy
            for key, val in order_by.items():
                if "." in key:
                    key = key.replace(".", "/")
                if val == -1:
                    orderArr.append(key + " desc")
                else:
                    orderArr.append(key)
        return ",".join(orderArr)

    def generatePerColQuery(self, condition):
        """
        Generate Per Col Query Method
        """
        conditions = []
        like = "%"
        for key, value in condition.items():
            if "/" in key:
                conditions.append('%s = "%s"' % (key, value))
            elif "." in key:
                conditions.append('%s LIKE "%s%s%s"' % (key.replace(".", "/"), like, value, like))
                # conditions.append(key.replace(".", "/") + ' LIKE "%' + str(value) + '%"')
            else:
                if isinstance(value, bool):
                    conditions.append('%s == %s' % (key, value))
                else:
                    conditions.append('%s LIKE "%s%s%s"' % (key, like, value, like))
        return " and ".join(conditions)

    def generateConditionQuery(self, condition):
        """
        Generate Condition Query Method
        """
        conditions = []
        for key, value in condition.items():
            conditions.append('%s = "%s"' % (key, value))
        return " and ".join(conditions)


class ConnectwiseManager(object):
    def __init__(self, settings):
        self.cwApi = ConnectwiseAPI(settings["company"], settings["domain"], settings['publicKey'], settings['privateKey'])

    def getServiceBoards(self, dummy, query={}):
        logr.error("Entered into getAll in class ConnectwiseServiceBoard " +str(query))
        skip, limit, orderBy = None, None, None
        if 'skip' in query:
            skip = int(query['skip'])
        if 'limit' in query:
            limit = int(query['limit'])
        if 'orderBy' in query:
            orderBy = query['orderBy']
        dataToGet = {'SR_Board_RecID': 'ServiceBoardId', 'Board_Name': 'BoardName',
                     'Inactive_Flag': "Inactive_Flag"}
        conditions = None
        if "condition" in query:
            conditions = query["condition"]
        elif "perColConditions" in query:
            conditions = self.cwApi.generatePerColQuery(query["perColConditions"])
        if conditions:
            conditions += " and Inactive_Flag=false"
        else:
            conditions = "Inactive_Flag=false"

        return self.cwApi.getReport('system', 'reports/ServiceBoard', columns=dataToGet,
                                    conditions=conditions, pageSize=limit, page=skip, orderBy=orderBy)

    def getServiceStatus(self, dummy, boardName):
        logr.error("Entered into getStatus in class ConnectwiseServiceBoard " +str(boardName))
        if boardName is not None:
            orderBy = [{"Sort_Order": "asc"}]
            conditions = "SR_Board_RecID = '%s'" % (boardName)
            dataToGet = {'Service_Status_Desc': 'Status', "Sort_Order": "Sort_Order",
                         "SR_Status_RecID": "SR_Status_RecID"}
            return self.cwApi.getReport('system', 'reports/ServiceStatus', columns=dataToGet, conditions=conditions,
                                        orderBy=orderBy)
        return False, {}

    def getServiceTypes(self, dummy, boardName):
        logr.error("Entered into getStatus in class ConnectwiseServiceBoard " +str(boardName))
        if boardName is not None:
            orderBy = [{"ServiceType": "asc"}]
            conditions = "SR_Board_RecID = '%s'" % (boardName)
            dataToGet = {'SR_Type_RecID': 'SR_Type_RecID', 'ServiceType': 'ServiceType'}
            status, resp = self.cwApi.getReport('system', 'reports/ServiceType', columns=dataToGet, conditions=conditions,
                                        orderBy=orderBy)
            if not status:
                return status, resp
            if isinstance(resp, dict):
                resp = [resp]
            filteredData = {}
            for item in resp:
                if item['SR_Type_RecID'] not in filteredData:
                    filteredData[item['SR_Type_RecID']] = item
            return True, list(filteredData.values())
        return False, {}

    def getServiceSubTypes(self, dummy, boardId, srtypeRecId):
        logr.error("Entered into getStatus in class ConnectwiseServiceBoard " + str(srtypeRecId))
        if srtypeRecId is not None:
            orderBy = []
            conditions = "SR_Board_RecID = '%s' and SR_Type_RecID = '%s'" % (boardId, srtypeRecId)
            dataToGet = {'SR_SubType_RecID': 'SR_SubType_RecID', 'ServiceSubTypeDesc': 'ServiceSubTypeDesc'}
            status, resp = self.cwApi.getReport('system', 'reports/ServiceSubType', columns=dataToGet, conditions=conditions,
                                        orderBy=orderBy)
            if not status:
                return status, resp
            if isinstance(resp, dict):
                resp = [resp]
            filteredData = {}
            for item in resp:
                if item['SR_SubType_RecID'] not in filteredData:
                    filteredData[item['SR_SubType_RecID']] = item
            return True, list(filteredData.values())
        return False, {}

    def getServiceItem(self, dummy, boardId, srtypeRecId, srSubtypeRecId):
        conditions = "SR_Board_RecID = '%s' and SR_Type_RecID = '%s' and SR_SubType_RecID = '%s'" % (boardId, srtypeRecId, srSubtypeRecId)
        orderBy = []
        dataToGet = {'SR_SubTypeItem_RecID': 'SR_SubTypeItem_RecID', 'ServiceItemDesc': 'ServiceItemDesc'}
        return self.cwApi.getReport('system', 'reports/ServiceItem', columns=dataToGet, conditions=conditions,
                                    orderBy=orderBy)

    def getTicketMapping(self, dummy):
        dataToGet = {'SR_Urgency_RecID': 'SR_Urgency_RecID', 'Service_Priority_Desc': 'Service_Priority_Desc'}
        return self.cwApi.getReport('system', 'reports/ServicePriority', columns=dataToGet, conditions="")

    def getCompanies(self, dummy, name="", pageSize=100, page=0):
        companiesList = []
        conditions = self.cwApi.generatePerColQuery({'deletedFlag': False})
        if name:
            conditions = self.cwApi.generatePerColQuery({'name': name, 'deletedFlag': False})
        status, resp = self.cwApi.get('company', 'companies', pageSize=pageSize, page=page, fields="id,identifier,name",
                                 conditions=conditions)
        for company in resp:
            companiesList.append({'id': company['id'], 'identifier': company['identifier'], 'name': company['name']})
        return True, companiesList

    def validateCredentials(self):
        try:
            status, resp = self.getServiceBoards('')
            if not status:
                return False, resp.get('errMsg', 'Error Validating Company Details')
            return status, resp
        except Exception as e:
            logr.info("Exception in validateBillingPlatform %s" % e)
            return False, str(e)

    def _updateTicketNotes(self, ticketId, doc, summary=None):
        ticketNoteEntry = dict()
        ticketNoteEntry['text'] = doc.get("notes")
        ticketNoteEntry['ticketId'] = ticketId
        ticketNoteEntry['detailDescriptionFlag'] = True
        ticketNoteEntry['externalFlag'] = True
        logr.info("Updating Ticket Notes for ticketId %s notes %s" % (ticketId, doc.get("notes")))
        if doc.get("files"):
            (status, updatedTkt) = self._uploadFiles(ticketId, "file", doc.get("files"))
        else:
            (status, updatedTkt) = self.cwApi.post('service', 'tickets/' + str(ticketId) + "/notes",
                                                   data=ticketNoteEntry)
        return status, updatedTkt

    def changeTicketStatus(self, ticketId, statusId, summary, companyRecId, board=None, ProblemDescription=None):
        logr.info("Changing ticket status for %s" % ticketId)
        tktdoc = dict()
        if board is not None:
            tktdoc['board/id'] = board
        tktdoc['company/id'] = companyRecId
        tktdoc['status/id'] = statusId
        st, uptkt = self.cwApi.patch('service', 'tickets/' + str(ticketId), data=tktdoc)
        if st and ProblemDescription is not None:
            self._updateTicketNotes(ticketId, {"notes":ProblemDescription})
        return st, uptkt

    def createTicket(self, doc, companyName, companyRecId):
        logr.info("Creating Ticket using doc %s company %s" % (doc, companyName))
        integration = doc['Integration']
        if not companyRecId:
            return False, "Company Not Mapped With Connectwise Company"
        tktdoc = dict()
        tktdoc['priority'] = {"id": integration.get(doc['Severity'].lower(), 1)}
        if "new" in integration:
            tktdoc['status'] = {"id": integration["new"]}
        tktdoc['company'] = {"id": int(companyRecId)}
        tktdoc['board'] = {"id": integration['sbId']}
        if integration.get('sbTypeId'):
            tktdoc['type'] = {"id": integration['sbTypeId']}
            if integration.get('sbSubTypeId'):
                tktdoc['subType'] = {"id": integration['sbSubTypeId']}
                if integration.get('sbSubTypeItem'):
                    tktdoc['item'] = {"id": integration['sbSubTypeItem']}

        # Get Company primary contact
        if not doc.get('contactId', ''):
            condition = "company/id=" + str(companyRecId) + " and defaultFlag=true"
            # childconditions = 'communicationItems/communicationType  = "Email" and communicationItems/defaultFlag = true'
            (status, contact) = self.cwApi.get('company', 'contacts', conditions=condition)
            if status and len(contact):
                tktdoc['contact'] = {"id": contact[0]["id"]}
        elif doc["contactId"]:
            tktdoc['contact'] = {"id": doc["contactId"]}

        summary = doc["Summary"]
        if len(summary) > 100:
            summary = summary[0:99]
        tktdoc['summary'] = summary
        if "ProblemDescription" in doc and len(doc["ProblemDescription"]):
            tktdoc['initialDescription'] = doc["ProblemDescription"]
        (status, createdTkt) = self.cwApi.post('service', 'tickets', data=tktdoc)
        tktConfigDoc = dict()
        if status and "deviceConfigId" in doc:
            tktConfigDoc["id"] = doc["deviceConfigId"]
            self.cwApi.post('service', 'tickets/' + str(createdTkt["id"]) + '/configurations', data=tktConfigDoc)
        return status, createdTkt
