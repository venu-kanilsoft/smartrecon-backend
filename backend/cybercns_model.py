
import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum





class UsersCreate(framework.postgresmodel.BasePostgresModel):
    name: str
    firstname: str
    lastname: str
    email: str
    phone: str
    password: str
    apiKey: str
    role: typing.Optional[str] = pydantic.Field("", **{})

    
    class Config:
        collection_name = 'users'
    

    

class Users(framework.postgresmodel.PostgresModel):
    name: typing.Optional[str]
    firstname: typing.Optional[str]
    lastname: typing.Optional[str]
    email: typing.Optional[str]
    phone: typing.Optional[str]
    password: typing.Optional[str]
    apiKey: typing.Optional[str]
    role: typing.Optional[str] = pydantic.Field("", **{})
    
    class Config:
        collection_name = 'users'
    

    


class UsersGetResp(pydantic.BaseModel):
    data: typing.List[Users]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)



users_router = fastapi.APIRouter(prefix='/users')


@users_router.post('/', response_model=Users, tags=['Users'])
async def create(inputObj: UsersCreate):
    
    return await inputObj.create()





@users_router.put('/', response_model=Users, tags=['Users'])
async def update(inputObj: Users):

    return await inputObj.update()


@users_router.get('/{id}', response_model=Users, tags=['Users'])
async def get(id: str):
    return await Users.get(id)


@users_router.get('/', response_model=UsersGetResp, tags=['Users'])
async def get_all(params = fastapi.Depends(framework.queryparams.QueryParams)):
    return await Users.get_all(params)


@users_router.delete('/{id}', tags=['Users'])
async def delete(id: str):
    return await Users.delete(id)




import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum





class SnmpInfoCreate(framework.postgresmodel.BasePostgresModel):
    description: typing.Optional[str] = pydantic.Field("", **{})
    deviceLocation: typing.Optional[str] = pydantic.Field("", **{})
    serial: typing.Optional[str] = pydantic.Field("", **{})
    sysContact: typing.Optional[str] = pydantic.Field("", **{})
    sysName: typing.Optional[str] = pydantic.Field("", **{})
    sysObjectId: typing.Optional[str] = pydantic.Field("", **{})









import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum





class HostCreate(framework.postgresmodel.BasePostgresModel):
    architecture: typing.Optional[str] = pydantic.Field("", **{})
    cpu_core: typing.Optional[int] = pydantic.Field(0, **{})
    discovered: typing.Optional[datetime.date]
    host_name: typing.Optional[str] = pydantic.Field("", **{})
    icon: typing.Optional[str] = pydantic.Field("", **{})
    status: bool
    importance: int
    serial_number: typing.Optional[str] = pydantic.Field("", **{})
    ip: str
    jid: typing.Optional[str] = pydantic.Field("", **{})
    mac: typing.Optional[str] = pydantic.Field("", **{})
    manufacturer: typing.Optional[str] = pydantic.Field("", **{})
    physical_memory: typing.Optional[str] = pydantic.Field("", **{})
    failed_logins: typing.Optional[int] = pydantic.Field(0, **{})
    uptime: typing.Optional[str] = pydantic.Field("", **{})









import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum





class OSCreate(framework.postgresmodel.BasePostgresModel):
    build: typing.Optional[str] = pydantic.Field("", **{})
    product_type: typing.Optional[str] = pydantic.Field("", **{})
    codename: typing.Optional[str] = pydantic.Field("", **{})
    full_name: typing.Optional[str] = pydantic.Field("", **{})
    kernel: typing.Optional[str] = pydantic.Field("", **{})
    name: typing.Optional[str] = pydantic.Field("", **{})
    platform: typing.Optional[str] = pydantic.Field("", **{})
    version: typing.Optional[str] = pydantic.Field("", **{})
    install_date: typing.Optional[int] = pydantic.Field(0, **{})
    patches: typing.Optional[typing.List[str]] = pydantic.Field([], **{})









import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum





class ProductTypesCreate(framework.postgresmodel.BasePostgresModel):
    port: int
    product: str









import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum





class NoAuthVulsCreate(framework.postgresmodel.BasePostgresModel):
    title: str
    definition: typing.Optional[str] = pydantic.Field("", **{})
    remediation: typing.Optional[str] = pydantic.Field("", **{})
    cvss: typing.Optional[float] = pydantic.Field(0.0, **{})
    product: typing.Optional[str] = pydantic.Field("", **{})
    shortName: str
    result: typing.Optional[str] = pydantic.Field("", **{})
    category: str
    severity: str
    port: int









import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum





class ExtraInfoCreate(framework.postgresmodel.BasePostgresModel):
    script: typing.Optional[str] = pydantic.Field("", **{})
    output: typing.Optional[str] = pydantic.Field("", **{})
    port: typing.Optional[int] = pydantic.Field(0, **{})








import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum





class SmbSharesCreate(framework.postgresmodel.BasePostgresModel):
    path: str
    anonymous_access: str









import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum





class HostNamesCreate(framework.postgresmodel.BasePostgresModel):
    name: str
    source: str









import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum





class PortsInternalCreate(framework.postgresmodel.BasePostgresModel):
    port: int
    service: str
    version: typing.Optional[str] = pydantic.Field("", **{})
    name: typing.Optional[str] = pydantic.Field("", **{})
    path: typing.Optional[str] = pydantic.Field("", **{})
    vulCount: typing.Optional[int] = pydantic.Field(0, **{})
    isSecure: typing.Optional[bool] = pydantic.Field(False, )









import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum





class AgentDataCreate(framework.postgresmodel.BasePostgresModel):
    ostype: str
    agent_type: str
    host_name: str
    agent_id: str
    agent_version: typing.Optional[str] = pydantic.Field("", **{})









import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum





class CiphersCreate(framework.postgresmodel.BasePostgresModel):
    kex_info: typing.Optional[str] = pydantic.Field("", **{})
    name: typing.Optional[str] = pydantic.Field("", **{})
    strength: typing.Optional[str] = pydantic.Field("", **{})
    protocol: typing.Optional[str] = pydantic.Field("", **{})









import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum





class EnumCiphersCreate(framework.postgresmodel.BasePostgresModel):
    tlsversion: str
    port: typing.Optional[int] = pydantic.Field(0, **{})
    ciphers: typing.Optional[typing.List['CiphersCreate']]









import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum





class SslCertificateCreate(framework.postgresmodel.BasePostgresModel):
    issuer_cn: typing.Optional[str] = pydantic.Field("", **{})
    issued_o: typing.Optional[str] = pydantic.Field("", **{})
    issuer_c: typing.Optional[str] = pydantic.Field("", **{})
    issuer_ou: typing.Optional[str] = pydantic.Field("", **{})
    issued_to: typing.Optional[str] = pydantic.Field("", **{})
    ext_key_usage: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    valid_from: typing.Optional[str] = pydantic.Field("", **{})
    valid_till: typing.Optional[str] = pydantic.Field("", **{})
    validity_days: typing.Optional[int] = pydantic.Field(0, **{})
    days_left: typing.Optional[int] = pydantic.Field(0, **{})
    subjectAltNames: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    cert_bytes: typing.Optional[int] = pydantic.Field(0, **{})
    cert_type: typing.Optional[str] = pydantic.Field("", **{})
    verify_cert: typing.Optional[bool] = pydantic.Field(False, )
    verify_host: typing.Optional[bool] = pydantic.Field(False, )
    public_exponent: typing.Optional[int] = pydantic.Field(0, **{})
    sn: typing.Optional[str] = pydantic.Field("", **{})
    sha1: typing.Optional[str] = pydantic.Field("", **{})
    fingerprint: typing.Optional[str] = pydantic.Field("", **{})
    ver: typing.Optional[int] = pydantic.Field(0, **{})
    alg: typing.Optional[str] = pydantic.Field("", **{})
    cert_expired: typing.Optional[bool] = pydantic.Field(False, )









import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum





class ProtocolsCreate(framework.postgresmodel.BasePostgresModel):
    name: str
    port: typing.Optional[int] = pydantic.Field(0, **{})
    isSecure: bool

    

    





import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum



class DiscoverySettingsReferenceCreate(framework.postgresmodel.BasePostgresModel):
    id: typing.Optional[str] = pydantic.Field("", **{})
    name: typing.Optional[str] = pydantic.Field("", **{})
    tags: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    

    






import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum





class AssetDataCreate(framework.postgresmodel.BasePostgresModel):
    assetName: typing.Optional[str] = pydantic.Field("", **{})
    cpeMatches: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    hostname: typing.Optional[typing.List['HostNamesCreate']]
    ip: typing.Optional[str] = pydantic.Field("", **{})
    jid: typing.Optional[str] = pydantic.Field("", **{})
    uptime: typing.Optional[int] = pydantic.Field(0, **{})
    lastboot: typing.Optional[str] = pydantic.Field("", **{})
    mac: typing.Optional[str] = pydantic.Field("", **{})
    nmapresptype: typing.Optional[str] = pydantic.Field("", **{})
    os: typing.Optional[str] = pydantic.Field("", **{})
    ostype: typing.Optional[str] = pydantic.Field("", **{})
    osversion: typing.Optional[str] = pydantic.Field("", **{})
    pingStatus: typing.Optional[bool] = pydantic.Field(False, )
    topPortsScan: typing.Optional[bool] = pydantic.Field(False, )
    status: bool
    subnet: typing.Optional[str] = pydantic.Field("", **{})
    isPrinter: typing.Optional[bool] = pydantic.Field(False, )
    enumCiphers: typing.Optional[typing.List['EnumCiphersCreate']]
    sslGrade: typing.Optional[str] = pydantic.Field("", **{})
    sslCert: typing.Optional['SslCertificateCreate']
    valid_cert: typing.Optional[bool] = pydantic.Field(False, )
    verify_cert: typing.Optional[bool] = pydantic.Field(False, )
    verify_host: typing.Optional[bool] = pydantic.Field(False, )
    additional_certs: typing.Optional[typing.List['SslCertificateCreate']]
    discoverysettingsRef: typing.Optional['DiscoverySettingsReferenceCreate']
    ports: typing.Optional[typing.List['PortsInternalCreate']]
    vendor: typing.Optional[str] = pydantic.Field("", **{})
    insecure_ports: typing.Optional[typing.List[int]] = pydantic.Field([], **{})
    insecure_ports_status: typing.Optional[bool] = pydantic.Field(False, )
    osMatches: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    smbshares: typing.Optional[typing.List['SmbSharesCreate']]
    noAuthVuls: typing.Optional[typing.List['NoAuthVulsCreate']]
    extraInfo: typing.Optional[typing.List['ExtraInfoCreate']]
    vulnerability_resp: typing.Optional[str] = pydantic.Field("", **{})
    vulnerability_status: typing.Optional[bool] = pydantic.Field(False, )
    compliance_resp: typing.Optional[str] = pydantic.Field("", **{})
    compliance_status: typing.Optional[bool] = pydantic.Field(False, )









import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum





class AssetCollectionCreate(framework.postgresmodel.BasePostgresModel):
    asset_id: str
    companyid: str
    agent_version: str
    ad_asset_id: typing.Optional[str] = pydantic.Field("", **{})
    job_id: typing.Optional[str] = pydantic.Field("", **{})
    agent_id: str
    local_agent_id: typing.Optional[str] = pydantic.Field("", **{})
    cred_id: typing.Optional[str] = pydantic.Field("", **{})
    agent_data: typing.Optional['AgentDataCreate']
    data: 'AssetDataCreate'









import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum





class FieldMapCreate(framework.postgresmodel.BasePostgresModel):
    field: str
    renameas: str









import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum





class SnmpOidDataCreate(framework.postgresmodel.BasePostgresModel):
    oid: str
    value: typing.List[str]





import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum





class ruleMapCreate(framework.postgresmodel.BasePostgresModel):
    id: str
    normal: int
    risk: int



import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum





class SnmpAssetDataCreate(framework.postgresmodel.BasePostgresModel):
    assetid: str
    ip: str
    credid: str
    agentid: str
    snmpBaseDetails: typing.List['SnmpOidDataCreate']
    snmpExtendedDetails: typing.Optional[typing.List['SnmpOidDataCreate']]









import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum


class CustomerAddressCreate(framework.postgresmodel.BasePostgresModel):
    country: typing.Optional[str] = pydantic.Field("", **{})
    state: typing.Optional[str] = pydantic.Field("", **{})
    city: typing.Optional[str] = pydantic.Field("", **{})
    zipCode: typing.Optional[str] = pydantic.Field("", **{})
    address: typing.Optional[typing.List[str]] = pydantic.Field([], **{})


class CustomerInfoCreate(framework.postgresmodel.BasePostgresModel):
    name: typing.Optional[str] = pydantic.Field("", **{})
    address: typing.Optional[CustomerAddressCreate]
    uniqueIdentifier: typing.Optional[str] = pydantic.Field("", **{})


class CompanyCreate(framework.postgresmodel.BasePostgresModel):
    name: str = pydantic.Field(**{'max_length': 256})
    description: str
    customerInfo: typing.Optional[CustomerInfoCreate]
    source: 'cybercns_enum.CompanySource'
    isMigrated: typing.Optional[bool] = pydantic.Field(False, )
    source_id: typing.Optional[str] = pydantic.Field("", **{})
    tags: typing.Optional[typing.List[str]] = pydantic.Field([], **{})


    class Config:
        collection_name = 'test'
        changeLogEnabled = True
        filterkey = '_id'




class Company(framework.postgresmodel.PostgresModel):
    name: typing.Optional[str] = pydantic.Field(**{'max_length': 256})
    description: typing.Optional[str]
    customerInfo: typing.Optional[CustomerInfoCreate]
    isMigrated: typing.Optional[bool] = pydantic.Field(False, )
    source: typing.Optional['cybercns_enum.CompanySource']
    source_id: typing.Optional[str] = pydantic.Field("", **{})
    tags: typing.Optional[typing.List[str]] = pydantic.Field([], **{})

    class Config:
        collection_name = 'test'
        changeLogEnabled = True
        filterkey = '_id'






class CompanyGetResp(pydantic.BaseModel):
    data: typing.List[Company]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)



company_router = fastapi.APIRouter(prefix='/company')
import Helpers

@company_router.post('/', response_model=Company, tags=['Company'])
async def create(inputObj: CompanyCreate):
    query = Helpers.buildElsQuery(must={"name.keyword": inputObj.name}, mustExpression=[{"exists": {"field": "description"}}], mustNotExpression=[{"exists": {"field": "companyRef"}}])
    params = framework.queryparams.QueryParams()
    params.limit = 1
    params.skip = 0
    params.q = json.dumps(query)
    resp = await Company().get_all(params)
    if resp['data']:
        return {"_id": "Company Exists With Same Name"}
    return await inputObj.create()




import apiProcessor
@company_router.put('/', response_model=Company, tags=['Company'])
async def update(inputObj: Company):
    oldData = await inputObj.get(inputObj.id)

    resp = await inputObj.update()
    if oldData.name != inputObj.name:
        await apiProcessor.modifyCompanyName(inputObj.id, inputObj.name)
    return resp


@company_router.get('/{id}', response_model=Company, tags=['Company'])
async def get(id: str):
    return await Company.get(id)


@company_router.get('/', response_model=CompanyGetResp, tags=['Company'])
async def get_all(params = fastapi.Depends(framework.queryparams.QueryParams)):
    return await Company.get_all(params)


@company_router.delete('/{id}', tags=['Company'])
async def delete(id: str):
    await agentCommunicator.AgentCommunicator().uninstallCompanyAgents(Company, id)
    # Generate Cascade delete in Company for below:
    # Delete Agent
    await Agent.delete_bulk({'companyRef.id.keyword': id})
    # Delete Asset
    await Asset.delete_bulk({'companyRef.id.keyword': id})
    # Delete AssetSnmpTable
    await AssetSnmpTable.delete_bulk({'companyRef.id.keyword': id})
    # Delete SslScanTimeseries
    await SslScanTimeseries.delete_bulk({'companyRef.id.keyword': id})
    # Delete AssetTimeStats
    await AssetTimeStats.delete_bulk({'companyRef.id.keyword': id})
    # Delete SmbSharePaths
    await SmbSharePaths.delete_bulk({'companyRef.id.keyword': id})
    # Delete AssetRunningProcess
    await AssetRunningProcess.delete_bulk({'companyRef.id.keyword': id})
    # Delete DiscoverySettings
    await DiscoverySettings.delete_bulk({'companyRef.id.keyword': id})
    # Delete SnmpV2Credentials
    await SnmpV2Credentials.delete_bulk({'companyRef.id.keyword': id})
    # Delete SnmpV3Credentials
    await SnmpV3Credentials.delete_bulk({'companyRef.id.keyword': id})
    # Delete AssetCredentials
    await AssetCredentials.delete_bulk({'companyRef.id.keyword': id})
    # Delete Ports
    await Ports.delete_bulk({'companyRef.id.keyword': id})
    # Delete Interfaces
    await Interfaces.delete_bulk({'companyRef.id.keyword': id})
    # Delete InstalledProgram
    await InstalledProgram.delete_bulk({'companyRef.id.keyword': id})
    # Delete Storage
    await Storage.delete_bulk({'companyRef.id.keyword': id})
    # Delete Vulnerability
    await Vulnerability.delete_bulk({'companyRef.id.keyword': id})
    # Delete VulnerabilityTimeseries
    await VulnerabilityTimeseries.delete_bulk({'companyRef.id.keyword': id})
    # Delete Compliance
    await Compliance.delete_bulk({'companyRef.id.keyword': id})
    # Delete ComplianceChecks
    await ComplianceChecks.delete_bulk({'companyRef.id.keyword': id})
    # Delete AssetFirewallPolicy
    await AssetFirewallPolicy.delete_bulk({'companyRef.id.keyword': id})
    # Delete AssetBestPractices
    await AssetBestPractices.delete_bulk({'companyRef.id.keyword': id})
    # Delete CustomPortSettings
    await CustomPortSettings.delete_bulk({'companyRef.id.keyword': id})
    # Delete RemediationSuppression
    await RemediationSuppression.delete_bulk({'companyRef.id.keyword': id})
    # Delete Remediation
    await  Remediation.delete_bulk({'companyRef.id.keyword': id})
    # Delete Jobs
    await Jobs.delete_bulk({'companyRef.id.keyword': id})
    # Delete AssetUsers
    await AssetUsers.delete_bulk({'companyRef.id.keyword': id})
    # Delete ApplicationBaseline
    await ApplicationBaseline.delete_bulk({'companyRef.id.keyword': id})
    # Delete RegistryMisConfiguration
    await RegistryMisConfiguration.delete_bulk({'companyRef.id.keyword': id})
    # Delete ADComputers
    await ADComputers.delete_bulk({'companyRef.id.keyword': id})
    # Delete ADUsers
    await ADUsers.delete_bulk({'companyRef.id.keyword': id})
    # Delete ADOu
    await ADOu.delete_bulk({'companyRef.id.keyword': id})
    # Delete ADGpo
    await ADGpo.delete_bulk({'companyRef.id.keyword': id})
    # Delete ADGroups
    await ADGroups.delete_bulk({'companyRef.id.keyword': id})
    # Delete FSMORoles
    await FSMORoles.delete_bulk({'companyRef.id.keyword': id})
    # Delete PasswordPolicy
    await PasswordPolicy.delete_bulk({'companyRef.id.keyword': id})
    # Delete CompanyStats
    await CompanyStats.delete_bulk({'companyRef.id.keyword': id})
    # Delete CompanyStatsTimeseries
    await CompanyStatsTimeseries.delete_bulk({'companyRef.id.keyword': id})

    return await Company.delete(id)



class CompanyprocessAssetDataParams(pydantic.BaseModel):
    assetData: 'AssetCollectionCreate'

import socket
import assetProcessor
import agentCommunicator
import json
import traceback
import jsonpickle
import snmpProcessor
import asyncAssetProcessor
@company_router.post('/{id}/processAssetData', tags=['Company'])
async def CompanyprocessAssetData(id: str, data: CompanyprocessAssetDataParams):
    try:
        await asyncAssetProcessor._RedisQueue('assetProcessor').put(jsonpickle.dumps({"tenant": framework.ctx['tenant'], "data": data}))
        # await assetProcessor.AssetProcessor().processAssetData(data)
    except Exception as e:
        print("Exception in Process AssetData %s" % e)
        print("Data: %s" % data.dict() )
        print("TraceBack: %s" % traceback.format_exc())

class CompanyprocessSnmpDataParams(pydantic.BaseModel):
    snmpData: typing.List['SnmpAssetDataCreate']
    jobid: typing.Optional[str] = pydantic.Field("", **{})

@company_router.post('/{id}/processSnmpData', tags=['Company'])
async def CompanyprocessSnmpData(id: str, data: CompanyprocessSnmpDataParams):
    await snmpProcessor.ProcessSnmpData().process_data(Asset, Vulnerability, Jobs, AssetTimeStats, data.dict())


class CompanydiscoveryCompletedParams(pydantic.BaseModel):
    companyid: str
    agentid: str
    jobid: str

import apiProcessor
@company_router.post('/{id}/discoveryCompleted', tags=['Company'])
async def CompanydiscoveryCompleted(id: str, data: CompanydiscoveryCompletedParams):
    return await agentCommunicator.AgentCommunicator().discoveryCompleted(Jobs, Asset, data.companyid, data.agentid, data.jobid)


class CompanycompanyDashboardsParams(pydantic.BaseModel):
    companyid: str
    assetid: typing.Optional[str] = pydantic.Field("", **{})

@company_router.post('/{id}/companyDashboards', tags=['Company'])
async def CompanycompanyDashboards(id: str, data: CompanycompanyDashboardsParams):
    return apiProcessor.CompanycompanyDashboards(data.companyid, data.assetid)


class CompanygetReportListParams(pydantic.BaseModel):
    ...

import reportProcessor

@company_router.post('/{id}/getReportList', tags=['Company'])
async def CompanygetReportList(id: str, data: CompanygetReportListParams):
    return await reportProcessor.ReportGenerator().getReportsList()


class CompanygenerateReportParams(pydantic.BaseModel):
    companyid: str
    assetid: typing.Optional[str] = pydantic.Field("", **{})
    reportid: str


class uploadReportTemplateParams(pydantic.BaseModel):
    ...

@company_router.post('/{id}/uploadReportTemplate', tags=['Company'])
async def CompanyuploadReportTemplate(id: str, custom_doc: fastapi.UploadFile = fastapi.File(...)):
    return await reportProcessor.ReportGenerator().uploadCustomTemplate(id,custom_doc)


class removeReportTemplateParams(pydantic.BaseModel):
    reportid: str

@company_router.post('/{id}/removeReportTemplate', tags=['Company'])
async def CompanyremoveReportTemplate(id: str,data: removeReportTemplateParams):
    return await reportProcessor.ReportGenerator().removeCustomTemplate(data.reportid)

class CompanygetDashboardLoginDataParams(pydantic.BaseModel):
    ...


@company_router.post('/{id}/getDashboardLoginData', tags=['Company'])
async def CompanygetDashboardLoginData(request: fastapi.Request, id: str, data: CompanygetDashboardLoginDataParams):
    return await apiProcessor.getDashboardLoginData(request.base_url.hostname)


class CompanygetCompanyAgentsParams(pydantic.BaseModel):
    companyid: str


@company_router.post('/{id}/getCompanyAgents', tags=['Company'])
async def CompanygetCompanyAgents(request: fastapi.Request, id: str, data: CompanygetCompanyAgentsParams):
    return await apiProcessor.getCompanyAgents(Agent(), data.companyid)



import reportProcessor
import agentCommunicator

@company_router.post('/{id}/generateReport', tags=['Company'])
async def CompanygenerateReport(id: str, data: CompanygenerateReportParams):
    return await reportProcessor.ReportGenerator().generateReport(data.companyid,data.reportid)


class CompanygenerateCompanyBulkReportsParams(pydantic.BaseModel):
    companyid: str
    reportid: typing.List[str]
    email: typing.Optional[typing.List[str]] = pydantic.Field([], **{})


@company_router.post('/{id}/generateCompanyBulkReports', tags=['Company'])
async def CompanygenerateCompanyBulkReports(request: fastapi.Request, id: str, data: CompanygenerateCompanyBulkReportsParams):
    return await reportProcessor.ReportGenerator().generateBulkReports(request.cookies.get("framework", None), data.companyid, data.reportid, data.email)


class CompanyscanParams(pydantic.BaseModel):
    companyid: str
    scantype: 'cybercns_enum.ScanType'

@company_router.post('/{id}/scan', tags=['Company'])
async def Companyscan(id: str, data: CompanyscanParams):
    return await agentCommunicator.AgentCommunicator().startCompanyScan(Jobs, Agent, data.companyid, data.scantype)


class CompanygetAgentSecretsParams(pydantic.BaseModel):
    companyid: str

import keyCloakManager
@company_router.post('/{id}/getAgentSecrets', tags=['Company'])
async def CompanygetAgentSecrets(id: str, data: CompanygetAgentSecretsParams):
    resp = await Company().get(data.companyid)
    if not resp:
        return False, "Company Not Found"
    return keyCloakManager.KeyClockSecret().create_client(data.companyid)


class CompanycreateMSPParams(pydantic.BaseModel):
    mspdomain: str
    email: str

import keyCloakManager
@company_router.post('/{id}/createMSP', tags=['Company'])
async def CompanycreateMSP(id: str, data: CompanycreateMSPParams):
    return await keyCloakManager.KeyClockSecret().create_msp(data.mspdomain, data.email)


class CompanygetRemediationDataParams(pydantic.BaseModel):
    companyid: typing.Optional[str] = pydantic.Field("", **{})
    remediationstatus: typing.Optional[str] = pydantic.Field("", **{})


@company_router.post('/{id}/getRemediationData', tags=['Company'])
async def CompanygetRemediationData(id: str, data: CompanygetRemediationDataParams):
    if data.companyid:
        resp = await Company().get(data.companyid)
        if not resp:
            return False, "Company Not Found"
        return await apiProcessor.RemediationProcessor().getCompanyRemediationPolicy(data.companyid, data.remediationstatus)
    else:
        return await apiProcessor.RemediationProcessor().getGlobalRemediationPolicy(data.remediationstatus)



class CompanyprocessBaseLineParams(pydantic.BaseModel):
    companyid: typing.Optional[str] = pydantic.Field("", **{})
    ruleid: typing.Optional[str] = pydantic.Field("", **{})


import AppBaseLineProcessor
@company_router.post('/{id}/processBaseLine', tags=['Company'])
async def CompanyprocessBaseLine(id: str, data: CompanyprocessBaseLineParams):
    ap = AppBaseLineProcessor.AppBaseLineProcessor()
    if data.ruleid:
        return await ap.rule_evaluator(data.ruleid, framework.ctx['tenant'])
    await ap.get_processor()
    return "Processed"

class CompanygetVulnerabilityOsViewParams(pydantic.BaseModel):
    companyId: typing.Optional[str] = pydantic.Field("", **{})

@company_router.post('/{id}/getVulnerabilityOsView', tags=['Company'])
async def CompanygetVulnerabilityOsView(id: str, data: CompanygetVulnerabilityOsViewParams):
    return await apiProcessor.VulnersProcessor().getVulnerabilityOsView(data.companyId)

class CompanygetVulnerabilityProductViewParams(pydantic.BaseModel):
    companyId: typing.Optional[str] = pydantic.Field("", **{})
    os: typing.Optional[str] = pydantic.Field("", **{})
    severity: typing.Optional[str] = pydantic.Field("", **{})

@company_router.post('/{id}/getVulnerabilityProductView', tags=['Company'])
async def CompanygetVulnerabilityProductView(id: str, data: CompanygetVulnerabilityProductViewParams):
    return await apiProcessor.VulnersProcessor().getVulnerabilityProductView(data.companyId, data.os, data.severity)

class CompanygetVulnerabilityViewParams(pydantic.BaseModel):
    companyId: typing.Optional[str] = pydantic.Field("", **{})
    os: typing.Optional[str] = pydantic.Field("", **{})
    severity: typing.Optional[str] = pydantic.Field("", **{})
    productName: typing.Optional[str] = pydantic.Field("", **{})

@company_router.post('/{id}/getVulnerabilityView', tags=['Company'])
async def CompanygetVulnerabilityView(id: str, data: CompanygetVulnerabilityViewParams):
    return await apiProcessor.VulnersProcessor().getVulnerabilityView(data.companyId, data.os, data.severity, data.productName)


class CompanygetNetworkVulsDataParams(pydantic.BaseModel):
    companyid: typing.Optional[str] = pydantic.Field("", **{})


@company_router.post('/{id}/getNetworkVulsData', tags=['Company'])
async def CompanygetNetworkVulsData(id: str, data: CompanygetNetworkVulsDataParams):
    resp = await Company().get(data.companyid)
    if not resp:
        return False, "Company Not Found"
    return await apiProcessor.RemediationProcessor().getNetworkVulsData(data.companyid)


class CompanygetGlobalNetworkVulsDataParams(pydantic.BaseModel):
    ...


@company_router.post('/{id}/getGlobalNetworkVulsData', tags=['Company'])
async def CompanygetGlobalNetworkVulsData(id: str, data: CompanygetGlobalNetworkVulsDataParams):
    return await apiProcessor.RemediationProcessor().getGlobalNetworkVulsData()


class CompanygetUniqueApplicationParams(pydantic.BaseModel):
    appName: str
    companyid: typing.Optional[str] = pydantic.Field("", **{})


@company_router.post('/{id}/getUniqueApplication', tags=['Company'])
async def CompanygetUniqueApplication(id: str, data: CompanygetUniqueApplicationParams):
    return await apiProcessor.RemediationProcessor().getUniqueApplication(data.appName, data.companyid)


class CompanygetVulnerabilityStatsParams(pydantic.BaseModel):
    companyid: typing.Optional[str] = pydantic.Field("", **{})


@company_router.post('/{id}/getVulnerabilityStats', tags=['Company'])
async def CompanygetVulnerabilityStats(id: str, data: CompanygetVulnerabilityStatsParams):
    return await apiProcessor.RemediationProcessor().getCompanyVulnerabilities(data.companyid)

class CompanygetVulnerabilityAssetStatsParams(pydantic.BaseModel):
    companyid: str
    osname: str

@company_router.post('/{id}/getVulnerabilityAssetStats', tags=['Company'])
async def CompanygetVulnerabilityAssetStats(id: str, data: CompanygetVulnerabilityAssetStatsParams):
    ...


class CompanysearchCVEParams(pydantic.BaseModel):
    companyid: typing.Optional[str] = pydantic.Field("", **{})
    cve: str


@company_router.post('/{id}/searchCVE', tags=['Company'])
async def CompanysearchCVE(id: str, data: CompanysearchCVEParams):
    return await apiProcessor.RemediationProcessor().searchCVE(data.cve, data.companyid)


class CompanypostInternalErrorParams(pydantic.BaseModel):
    error_id: str
    error_msg: str

import apiProcessor
import activedirectoryProcessor
@company_router.post('/{id}/postInternalError', tags=['Company'])
async def CompanypostInternalError(id: str, data: CompanypostInternalErrorParams):
    ...


class CompanygetReportCardTemplateParams(pydantic.BaseModel):
    ...

@company_router.post('/{id}/getReportCardTemplate', tags=['Company'])
async def CompanygetReportCardTemplate(id: str, data: CompanygetReportCardTemplateParams):
    return apiProcessor.RemediationProcessor().getReportCardTemplate()


class CompanyupdateCompanyScoreParams(pydantic.BaseModel):
    ...

import ScoreEvaluator
@company_router.post('/{id}/updateCompanyScore', tags=['Company'])
async def CompanyupdateCompanyScore(id: str, data: CompanyupdateCompanyScoreParams):
    return await ScoreEvaluator.CompanyScoreStats().getCompanyStats()

class CompanygetScoreTemplatesParams(pydantic.BaseModel):
    ...
@company_router.post('/{id}/getScoreTemplates', tags=['Company'])
async def CompanygetScoreTemplates(id: str, data: CompanygetScoreTemplatesParams):
    return await ScoreEvaluator.CompanyScoreStats().getScoreTemplates()


class CompanyupdateScoreTemplatesParams(pydantic.BaseModel):
    type: str
    rules: typing.List['ruleMapCreate']
    
@company_router.post('/{id}/updateScoreTemplates', tags=['Company'])
async def CompanyupdateScoreTemplates(id: str, data: CompanyupdateScoreTemplatesParams):
    return await ScoreEvaluator.CompanyScoreStats().updateScoreTemplates(data.type, data.rules)


class CompanygetMastertemplateDataParams(pydantic.BaseModel):
   ...

@company_router.post('/{id}/getMastertemplateData', tags=['Company'])
async def CompanygetMastertemplateData(id: str, data: CompanygetMastertemplateDataParams):
    return apiProcessor.RemediationProcessor().getMasterTemplates()


class CompanygetActivedirectoryStatsParams(pydantic.BaseModel):
    companyid: str

@company_router.post('/{id}/getActivedirectoryStats', tags=['Company'])
async def CompanygetActivedirectoryStats(id: str, data: CompanygetActivedirectoryStatsParams):
    return await activedirectoryProcessor.ActiveDirectoryProcessor().getAdStats(data.companyid)


import activedirectoryProcessor
class CompanyactivedirectoryScanCompletedParams(pydantic.BaseModel):
    companyid: str
    agentid: str
    jobid: typing.Optional[str] = pydantic.Field("", **{})
    credid: typing.Optional[str] = pydantic.Field("", **{})

@company_router.post('/{id}/activedirectoryScanCompleted', tags=['Company'])
async def CompanyactivedirectoryScanCompleted(id: str, data: CompanyactivedirectoryScanCompletedParams):
    await activedirectoryProcessor.ActiveDirectoryProcessor().runpostFixes(ADOu().Config.collection_name, data.companyid, data.agentid, data.jobid, data.credid)

import apiProcessor
# from alert_model import *

class CompanygetxlsxreportParams(pydantic.BaseModel):
    query: str
    classname: str
    fieldmap: typing.Optional[typing.List['FieldMapCreate']]
    filename: str

@company_router.post('/{id}/getxlsxreport', tags=['Company'])
async def Companygetxlsxreport(id: str, data: CompanygetxlsxreportParams):
    return await apiProcessor.XlsxreportGenerator().generateXlsxReport(eval(data.classname), data.classname, data.query, data.filename, data.fieldmap)


class CompanyquickExternalScanParams(pydantic.BaseModel):
    hostname: str
    forceScan: typing.Optional[bool] = pydantic.Field(False, )

import agentCommunicator
@company_router.post('/{id}/quickExternalScan', tags=['Company'])
async def CompanyquickExternalScan(id: str, data: CompanyquickExternalScanParams):
    return await agentCommunicator.QuickScanner().startScan(data.hostname, data.forceScan)


class CompanyquickExternalScanResultsParams(pydantic.BaseModel):
    hostname: str


@company_router.post('/{id}/quickExternalScanResults', tags=['Company'])
async def CompanyquickExternalScanResults(id: str, data: CompanyquickExternalScanResultsParams):
    return agentCommunicator.QuickScanner().getResults(data.hostname)


class CompanygetApiRolesParams(pydantic.BaseModel):
    ...

@company_router.post('/{id}/getApiRoles', tags=['Company'])
async def CompanygetApiRoles(id: str, data: CompanygetApiRolesParams):
    return  apiProcessor.getApiRoles()


import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum


class schedulerSettingCreate(framework.postgresmodel.BasePostgresModel):
    mins: typing.Optional[typing.List[int]] = pydantic.Field([], **{})
    hour: typing.Optional[typing.List[int]] = pydantic.Field([], **{})
    hours: typing.Optional[typing.List[int]] = pydantic.Field([], **{})
    days: typing.Optional[typing.List[int]] = pydantic.Field([], **{})
    week: typing.Optional[typing.List[int]] = pydantic.Field([], **{})
    months: typing.Optional[typing.List[int]] = pydantic.Field([], **{})
    weekdays: typing.Optional[typing.List[int]] = pydantic.Field([], **{})


class CompanySchedulerRef(pydantic.BaseModel):
    id: str
    name: typing.Optional[str] = pydantic.Field(**{'max_length': 256})


    async def load(self):
        data = await Company.get(self.id)
        super().__init__(**data.dict())

class AgentSchedulerRef(pydantic.BaseModel):
    id: str
    name: typing.Optional[str]


    async def load(self):
        data = await Agent.get(self.id)
        super().__init__(**data.dict())


class SchedulerCreate(framework.postgresmodel.BasePostgresModel):
    name: str
    uniqueid: str
    reconId: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    stmtdate: typing.Optional[str] = pydantic.Field("", **{})
    settings: 'schedulerSettingCreate'
    scheduler: typing.Optional[str] = pydantic.Field("", **{})
    isGlobal: typing.Optional[bool] = pydantic.Field(False, )
    isActive: typing.Optional[bool] = pydantic.Field(False, )
    email: typing.Optional[typing.List[str]] = pydantic.Field([], **{})


    class Config:
        collection_name = 'scheduler'



    async def loadRefs(self):

        [await x.load() for x in self.companyRef] if self.companyRef else ...



        [await x.load() for x in self.agentRef] if self.agentRef else ...



class Scheduler(framework.postgresmodel.PostgresModel):
    name: typing.Optional[str]
    uniqueid: typing.Optional[str]
    reconId: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    stmtdate: typing.Optional[str] = pydantic.Field("", **{})
    settings: typing.Optional['schedulerSettingCreate']
    scheduler: typing.Optional[str] = pydantic.Field("", **{})
    isGlobal: typing.Optional[bool] = pydantic.Field(False, )
    isActive: typing.Optional[bool] = pydantic.Field(False, )
    email: typing.Optional[typing.List[str]] = pydantic.Field([], **{})

    class Config:
        collection_name = 'scheduler'



    async def loadRefs(self):
        [await x.load() for x in self.companyRef] if self.companyRef else ...

        [await x.load() for x in self.agentRef] if self.agentRef else ...



class SchedulerGetResp(pydantic.BaseModel):
    data: typing.List[Scheduler]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)



scheduler_router = fastapi.APIRouter(prefix='/scheduler')


@scheduler_router.post('/', response_model=Scheduler, tags=['Scheduler'])
async def create(request: fastapi.Request, inputObj: SchedulerCreate):

    # await inputObj.loadRefs()
    # status, resp = await agentCommunicator.AgentCommunicator().verifyScheduler(Scheduler, inputObj.dict())
    # if not status:
    #     return {"_id": resp}
    resp = await inputObj.create()
    await agentCommunicator.AgentCommunicator().updateScheduler(request.base_url.hostname, inputObj, Agent, resp, True)
    # return resp    
    return {"status": True, "message": 'Success', "data": resp}





@scheduler_router.put('/', response_model=Scheduler, tags=['Scheduler'])
async def update(request: fastapi.Request, inputObj: Scheduler):

    # await inputObj.loadRefs()

    resp = await inputObj.update()
    await agentCommunicator.AgentCommunicator().updateScheduler(request.base_url.hostname, inputObj, Agent, resp, True)
    # return resp
    return {"status": True, "message": 'Success', "data": resp}


@scheduler_router.get('/{id}', response_model=Scheduler, tags=['Scheduler'])
async def get(id: str):
    return await Scheduler.get(id)


@scheduler_router.get('/', response_model=SchedulerGetResp, tags=['Scheduler'])
async def get_all(params = fastapi.Depends(framework.queryparams.QueryParams)):
    try:
        return await Scheduler.get_all(params)
    except Exception as e:
        return {"status": False, "message": "No Data Found", "data": []}


@scheduler_router.delete('/{id}', tags=['Scheduler'])
async def delete(request: fastapi.Request, id: str):
    scheduleData = await Scheduler.get(id)
    if isinstance(scheduleData, dict):
        scheduleData = Scheduler(**scheduleData)
    await agentCommunicator.AgentCommunicator().updateScheduler(request.base_url.hostname, scheduleData, Agent, scheduleData, False)
    return await Scheduler.delete(id)



class SchedulergetScheduleTemplatesParams(pydantic.BaseModel):
    pass

@scheduler_router.post('/{id}/getScheduleTemplates', tags=['Scheduler'])
async def SchedulergetScheduleTemplates(id: str, data: SchedulergetScheduleTemplatesParams):
    return await agentCommunicator.AgentCommunicator().getScheduleTemplates()


import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum

async def AgentIndex():
    spec = []
    spec.append(('companyRef', 1))
    await AgentCreate.createIndex(spec, )




class CompanyAgentRef(pydantic.BaseModel):
    id: str
    name: typing.Optional[str] = pydantic.Field(**{'max_length': 256})


    async def load(self):
        data = await Company.get(self.id)
        super().__init__(**data.dict())


class AgentCreate(framework.postgresmodel.BasePostgresModel):
    name: str
    version: typing.Optional[str] = pydantic.Field("", **{})
    host_name: typing.Optional[str] = pydantic.Field("", **{})
    ostype: typing.Optional['cybercns_enum.OSType']
    agent_type: typing.Optional['cybercns_enum.AgentType']
    ip: typing.Optional[ipaddress.IPv4Address]
    tags: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    lastscannedtime: typing.Optional[datetime.datetime]
    companyRef: typing.Optional['CompanyAgentRef']


    class Config:
        collection_name = 'test'



    async def loadRefs(self):

        await self.companyRef.load() if self.companyRef else ...



class Agent(framework.postgresmodel.PostgresModel):
    name: typing.Optional[str]
    version: typing.Optional[str] = pydantic.Field("", **{})
    host_name: typing.Optional[str] = pydantic.Field("", **{})
    ostype: typing.Optional['cybercns_enum.OSType']
    agent_type: typing.Optional['cybercns_enum.AgentType']
    ip: typing.Optional[ipaddress.IPv4Address]
    tags: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    lastscannedtime: typing.Optional[datetime.datetime]
    companyRef: typing.Optional['CompanyAgentRef']

    class Config:
        collection_name = 'test'



    async def loadRefs(self):
        await self.companyRef.load() if self.companyRef else ...



class AgentGetResp(pydantic.BaseModel):
    data: typing.List[Agent]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)



agent_router = fastapi.APIRouter(prefix='/agent')


@agent_router.post('/', response_model=Agent, tags=['Agent'])
async def create(inputObj: AgentCreate):

    await inputObj.loadRefs()

    return await inputObj.create()





@agent_router.put('/', response_model=Agent, tags=['Agent'])
async def update(inputObj: Agent):

    await inputObj.loadRefs()

    return await inputObj.update()


@agent_router.get('/{id}', response_model=Agent, tags=['Agent'])
async def get(id: str):
    return await Agent.get(id)


@agent_router.get('/', response_model=AgentGetResp, tags=['Agent'])
async def get_all(params = fastapi.Depends(framework.queryparams.QueryParams)):
    return await Agent.get_all(params)

import agentCommunicator
@agent_router.delete('/{id}', tags=['Agent'])
async def delete(id: str):
    # Generate Cascade delete in Agent for below:
    # Delete Asset
    await Asset.delete_bulk({'agentRef.id.keyword': id})
    # Delete AssetSnmpTable
    await AssetSnmpTable.delete_bulk({'agentRef.id.keyword': id})
    # Delete SslScanTimeseries
    await SslScanTimeseries.delete_bulk({'agentRef.id.keyword': id})
    # Delete AssetTimeStats
    await AssetTimeStats.delete_bulk({'agentRef.id.keyword': id})
    # Delete SmbSharePaths
    await SmbSharePaths.delete_bulk({'agentRef.id.keyword': id})
    # Delete AssetRunningProcess
    await AssetRunningProcess.delete_bulk({'agentRef.id.keyword': id})
    # Delete DiscoverySettings
    await DiscoverySettings.delete_bulk({'agentRef.id.keyword': id})
    # Delete SnmpV2Credentials
    await SnmpV2Credentials.delete_bulk({'agentRef.id.keyword': id})
    # Delete SnmpV3Credentials
    await SnmpV3Credentials.delete_bulk({'agentRef.id.keyword': id})
    # Delete AssetCredentials
    await AssetCredentials.delete_bulk({'agentRef.id.keyword': id})
    # Delete Ports
    await Ports.delete_bulk({'agentRef.id.keyword': id})
    # Delete Interfaces
    await Interfaces.delete_bulk({'agentRef.id.keyword': id})
    # Delete InstalledProgram
    await InstalledProgram.delete_bulk({'agentRef.id.keyword': id})
    # Delete Storage
    await Storage.delete_bulk({'agentRef.id.keyword': id})
    # Delete Vulnerability
    await Vulnerability.delete_bulk({'agentRef.id.keyword': id})
    # Delete VulnerabilityTimeseries
    await VulnerabilityTimeseries.delete_bulk({'agentRef.id.keyword': id})
    # Delete Compliance
    await Compliance.delete_bulk({'agentRef.id.keyword': id})
    # Delete ComplianceChecks
    await ComplianceChecks.delete_bulk({'agentRef.id.keyword': id})
    # Delete AssetFirewallPolicy
    await AssetFirewallPolicy.delete_bulk({'agentRef.id.keyword': id})
    # Delete AssetBestPractices
    await AssetBestPractices.delete_bulk({'agentRef.id.keyword': id})
    # Delete RemediationSuppression
    await RemediationSuppression.delete_bulk({'agentRef.id.keyword': id})
    # Delete Remediation
    await Remediation.delete_bulk({'agentRef.id.keyword': id})
    # Delete Jobs
    await Jobs.delete_bulk({'agentRef.id.keyword': id})
    # Delete AssetUsers
    await AssetUsers.delete_bulk({'agentRef.id.keyword': id})
    # Delete ApplicationBaseline
    await ApplicationBaseline.delete_bulk({'agentRef.id.keyword': id})
    # Delete RegistryMisConfiguration
    await RegistryMisConfiguration.delete_bulk({'agentRef.id.keyword': id})
    # Delete ADComputers
    await ADComputers.delete_bulk({'agentRef.id.keyword': id})
    # Delete ADUsers
    await ADUsers.delete_bulk({'agentRef.id.keyword': id})
    # Delete ADOu
    await ADOu.delete_bulk({'agentRef.id.keyword': id})
    # Delete ADGpo
    await ADGpo.delete_bulk({'agentRef.id.keyword': id})
    # Delete ADGroups
    await ADGroups.delete_bulk({'agentRef.id.keyword': id})
    # Delete FSMORoles
    await FSMORoles.delete_bulk({'agentRef.id.keyword': id})
    # Delete PasswordPolicy
    await PasswordPolicy.delete_bulk({'agentRef.id.keyword': id})
    await agentCommunicator.AgentCommunicator().uninstallAgent(Agent, id)
    resp = await Agent.delete(id)
    return resp

import agentCommunicator
class AgentscanParams(pydantic.BaseModel):
    scantype: 'cybercns_enum.ScanType'
    agent_id: str

@agent_router.post('/{id}/scan', tags=['Agent'])
async def Agentscan(id: str, data: AgentscanParams):
    try:
        agentdata = await Agent().get(data.agent_id)
        if agentdata.agent_type.value != 4:
            return await agentCommunicator.AgentCommunicator().startAgentScan(Jobs, Agent, data.scantype, data.agent_id, agentdata.companyRef.id)
        else:
            return await agentCommunicator.AgentCommunicator().startGlobalExternalScan(Jobs, Agent, data.scantype, data.agent_id, "")
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        return False, "No registered agent available for the given ID"
    #return await agentCommunicator.AgentCommunicator().startAgentScan(Jobs, Agent, data.scantype, data.agent_id, agentdata.companyRef.id)


class AgentgetworkParams(pydantic.BaseModel):
    agent_id: str

@agent_router.post('/{id}/getwork', tags=['Agent'])
async def Agentgetwork(id: str, data: AgentgetworkParams):
    return await agentCommunicator.AgentCommunicator().getWork(data.agent_id)

class AgentgetAgentStatusParams(pydantic.BaseModel):
    agent_id: str

@agent_router.post('/{id}/getAgentStatus', tags=['Agent'])
async def AgentStatus(id: str, data: AgentgetAgentStatusParams):
    return await agentCommunicator.AgentCommunicator().getAgentStatus(data.agent_id)


class AgentgetAgentLinkParams(pydantic.BaseModel):
    ostype: str

@agent_router.post('/{id}/getAgentLink', tags=['Agent'])
async def AgentgetAgentLink(id: str, data: AgentgetAgentLinkParams):
    if data.ostype.lower() == "windows":
        return True, "https://cybercnsagent.s3.amazonaws.com/cybercnsagent.exe"
    elif data.ostype.lower() == "linux":
        return True, "https://cybercnsagent.s3.amazonaws.com/cybercnsagent_linux"
    elif data.ostype.lower() in ["darwin", "mac"]:
        return True, "https://cybercnsagent.s3.amazonaws.com/cybercnsagent_darwin"
    elif data.ostype.lower() == "arm":
        return True, "https://cybercnsagent.s3.amazonaws.com/cybercnsagent_arm"
    return False, "Not Supported"


class AgentgetscanTemplatesParams(pydantic.BaseModel):
    template_type: str

@agent_router.post('/{id}/getscanTemplates', tags=['Agent'])
async def AgentgetscanTemplates(id: str, data: AgentgetscanTemplatesParams):
    return await agentCommunicator.AgentCommunicator().cybertemplates(data.template_type)


class AgentupdateAgentVersionParams(pydantic.BaseModel):
    agent_id: str
    agent_version: str

@agent_router.post('/{id}/updateAgentVersion', tags=['Agent'])
async def AgentupdateAgentVersion(id: str, data: AgentupdateAgentVersionParams):
    await Agent(**{"_id": data.agent_id, "version": data.agent_version}).update()
    return True, "Success"


class AgentgetScheduledActionsParams(pydantic.BaseModel):
    agent_id: str

@agent_router.post('/{id}/getScheduledActions', tags=['Agent'])
async def AgentgetScheduledActions(id: str, data: AgentgetScheduledActionsParams):
    return await agentCommunicator.AgentCommunicator().getScheduledActionsParams(Agent, Scheduler, data.agent_id)


class AgentuninstallAgentParams(pydantic.BaseModel):
    agent_id: str

@agent_router.post('/{id}/uninstallAgent', tags=['Agent'])
async def AgentuninstallAgent(id: str, data: AgentuninstallAgentParams):
    return await agentCommunicator.AgentCommunicator().uninstallAgent(Agent, data.agent_id)


@agent_router.post("/upload_file", tags=['Agent'])
async def upload_file(uploadfile: fastapi.UploadFile = fastapi.File(...)):
    return await agentCommunicator.AgentCommunicator().uploadagentlogs(uploadfile)


class SortOptionsCreate(framework.postgresmodel.BasePostgresModel):
    active: typing.Optional[str] = pydantic.Field("", **{})
    direction: typing.Optional[str] = pydantic.Field("", **{})


import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum


class TableInternalSettingsCreate(framework.postgresmodel.BasePostgresModel):
    gFilter: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    sortOptions: typing.Optional['SortOptionsCreate']
    pageSize: typing.Optional[int] = pydantic.Field(0, **{})


import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum


class TableSettingsCreate(framework.postgresmodel.BasePostgresModel):
    tableId: str
    columnRepr: typing.Optional[str] = pydantic.Field("", **{})
    refreshInterval: typing.Optional[int] = pydantic.Field(0, **{})
    userId: typing.Optional[str] = pydantic.Field("", **{})
    settings: typing.Optional['TableInternalSettingsCreate']

    class Config:
        collection_name = 'TableSettings'
        filterkey = ''


class TableSettings(framework.postgresmodel.PostgresModel):
    tableId: typing.Optional[str]
    columnRepr: typing.Optional[str] = pydantic.Field("", **{})
    refreshInterval: typing.Optional[int] = pydantic.Field(0, **{})
    userId: typing.Optional[str] = pydantic.Field("", **{})
    settings: typing.Optional['TableInternalSettingsCreate']

    class Config:
        collection_name = 'TableSettings'
        filterkey = ''

class TableSettingsCreateUpdateGetResp(pydantic.BaseModel):
    data: TableSettings
    status: bool = pydantic.Field(True)
    message: str = pydantic.Field("Success")


class TableSettingsGetResp(pydantic.BaseModel):
    data: typing.List[TableSettings]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)


tablesettings_router = fastapi.APIRouter(prefix='/tablesettings')


@tablesettings_router.post('/', response_model=TableSettingsCreateUpdateGetResp, tags=['TableSettings'])
async def create(inputObj: TableSettingsCreate):
    return await inputObj.create()


@tablesettings_router.put('/', response_model=TableSettingsCreateUpdateGetResp, tags=['TableSettings'])
async def update(inputObj: TableSettings):
    return await inputObj.update()


@tablesettings_router.get('/{id}', response_model=TableSettings, tags=['TableSettings'])
async def get(id: str):
    return await TableSettings.get(id)


@tablesettings_router.get('/', response_model=TableSettingsGetResp, tags=['TableSettings'])
async def get_all(params = fastapi.Depends(framework.queryparams.QueryParams)):
    try:
        return await TableSettings.get_all(params)
    except Exception as e:
        print('-- Exception --')
        print(e)
        return {"data":[], "count": 0, "total": 0}


@tablesettings_router.delete('/{id}', tags=['TableSettings'])
async def delete(id: str):
    return await TableSettings.delete(id)



# Aggrid Settings

import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum


class AggridSettingsCreate(framework.postgresmodel.BasePostgresModel):
    tableId: str
    columnRepr: typing.Optional[str] = pydantic.Field("", **{})
    refreshInterval: typing.Optional[int] = pydantic.Field(0, **{})
    userId: typing.Optional[str] = pydantic.Field("", **{})
    settings: typing.Optional[str] = pydantic.Field("", **{})
    reconId: str
    function: typing.Optional[str] = pydantic.Field("", **{})
    source: typing.Optional[str] = pydantic.Field("", **{})

    class Config:
        collection_name = 'aggridsettings'
        filterkey = ''


class AggridSettings(framework.postgresmodel.PostgresModel):
    tableId: typing.Optional[str]
    columnRepr: typing.Optional[str] = pydantic.Field("", **{})
    refreshInterval: typing.Optional[int] = pydantic.Field(0, **{})
    userId: typing.Optional[str] = pydantic.Field("", **{})
    settings: typing.Optional[str] = pydantic.Field("", **{})
    reconId: typing.Optional[str]
    function: typing.Optional[str] = pydantic.Field("", **{})
    source: typing.Optional[str] = pydantic.Field("", **{})

    class Config:
        collection_name = 'aggridsettings'
        filterkey = ''


class AggridSettingsGetResp(pydantic.BaseModel):
    data: typing.List[AggridSettings]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)


aggridsettings_router = fastapi.APIRouter(prefix='/aggridsettings')


@aggridsettings_router.post('/', response_model=AggridSettings, tags=['AggridSettings'])
async def create(inputObj: AggridSettingsCreate):
    return await inputObj.create()


@aggridsettings_router.put('/', response_model=AggridSettings, tags=['AggridSettings'])
async def update(inputObj: AggridSettings):
    return await inputObj.update()


@aggridsettings_router.get('/{id}', response_model=AggridSettings, tags=['AggridSettings'])
async def get(id: str):
    return await AggridSettings.get(id)


@aggridsettings_router.get('/', response_model=AggridSettingsGetResp, tags=['AggridSettings'])
async def get_all(params = fastapi.Depends(framework.queryparams.QueryParams)):
    try:
        return await AggridSettings.get_all(params)
    except Exception as e:
        return {"data":[], "count": 0, "total": 0}


@aggridsettings_router.delete('/{id}', tags=['AggridSettings'])
async def delete(id: str):
    return await AggridSettings.delete(id)





import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum





class EventRulesCreate(framework.postgresmodel.BasePostgresModel):
    ruleId: str
    eventId: typing.List[str]









import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum





class AlertRulesCreate(framework.postgresmodel.BasePostgresModel):
    sectionId: str
    rules: typing.List['EventRulesCreate']









import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum





class IntegrationRulesCreate(framework.postgresmodel.BasePostgresModel):
    integrationId: str
    integrationName: str
    board: typing.Optional[str] = pydantic.Field("", **{})
    type: typing.Optional[str] = pydantic.Field("", **{})
    subtype: typing.Optional[str] = pydantic.Field("", **{})
    item: typing.Optional[str] = pydantic.Field("", **{})
    status: typing.Optional[str] = pydantic.Field("", **{})
    status_close: typing.Optional[str] = pydantic.Field("", **{})
    priority: typing.Optional[str] = pydantic.Field("", **{})
    toEmail: typing.Optional[str] = pydantic.Field("", **{})
    fromuser: typing.Optional[str] = pydantic.Field("", **{})
    replyTo: typing.Optional[str] = pydantic.Field("", **{})
    isHtml: typing.Optional[bool] = pydantic.Field(False, )
    location: typing.Optional[str] = pydantic.Field("", **{})
    employee: typing.Optional[str] = pydantic.Field("", **{})
    queues: typing.Optional[str] = pydantic.Field("", **{})









import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import cybercns_enum

async def NotificationRulesIndex():
    spec = []
    spec.append(('companyRef', 1))
    await NotificationRulesCreate.createIndex(spec, )




class CompanyNotificationRulesRef(pydantic.BaseModel):
    id: str
    name: typing.Optional[str] = pydantic.Field(**{'max_length': 256})


    async def load(self):
        data = await Company.get(self.id)
        super().__init__(**data.dict())


class NotificationRulesCreate(framework.postgresmodel.BasePostgresModel):
    name: typing.Optional[str] = pydantic.Field(**{'max_length': 256})
    integrationRule: typing.List['IntegrationRulesCreate']
    alertRules: typing.List['AlertRulesCreate']
    companyRef: typing.Optional['CompanyNotificationRulesRef']


    class Config:
        collection_name = 'test'



    async def loadRefs(self):

        await self.companyRef.load() if self.companyRef else ...



class NotificationRules(framework.postgresmodel.PostgresModel):
    name: typing.Optional[str] = pydantic.Field(**{'max_length': 256})
    integrationRule: typing.Optional[typing.List['IntegrationRulesCreate']]
    alertRules: typing.Optional[typing.List['AlertRulesCreate']]
    companyRef: typing.Optional['CompanyNotificationRulesRef']

    class Config:
        collection_name = 'test'



    async def loadRefs(self):
        await self.companyRef.load() if self.companyRef else ...



class NotificationRulesGetResp(pydantic.BaseModel):
    data: typing.List[NotificationRules]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)



notificationrules_router = fastapi.APIRouter(prefix='/notificationrules')


@notificationrules_router.post('/', response_model=NotificationRules, tags=['NotificationRules'])
async def create(inputObj: NotificationRulesCreate):

    await inputObj.loadRefs()

    return await inputObj.create()





@notificationrules_router.put('/', response_model=NotificationRules, tags=['NotificationRules'])
async def update(inputObj: NotificationRules):

    await inputObj.loadRefs()

    return await inputObj.update()


@notificationrules_router.get('/{id}', response_model=NotificationRules, tags=['NotificationRules'])
async def get(id: str):
    return await NotificationRules.get(id)


@notificationrules_router.get('/', response_model=NotificationRulesGetResp, tags=['NotificationRules'])
async def get_all(params = fastapi.Depends(framework.queryparams.QueryParams)):
    return await NotificationRules.get_all(params)


@notificationrules_router.delete('/{id}', tags=['NotificationRules'])
async def delete(id: str):
    return await NotificationRules.delete(id)



