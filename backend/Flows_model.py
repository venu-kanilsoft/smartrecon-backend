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
import Flows_enum



class ConnectionCreate(framework.postgresmodel.BasePostgresModel):
    nodeID: int
    connectorIndex: int

    
    





class connectionsDictCreate(framework.postgresmodel.BasePostgresModel):
    dest: ConnectionCreate
    source: ConnectionCreate

    
    





class ConnectorDictCreate(framework.postgresmodel.BasePostgresModel):
    name: str

    
    





class sourceColumnsCreate(framework.postgresmodel.BasePostgresModel):
    sumColumns: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    debitCreditColumn: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    matchColumns: typing.Optional[typing.List[str]] = pydantic.Field([], **{})

    
    





class sourcesDictCreate(framework.postgresmodel.BasePostgresModel):
    source: typing.Optional[str] = pydantic.Field("", **{})
    sourceTag: typing.Optional[str] = pydantic.Field("", **{})
    dropDuplicates: typing.Optional[bool] = pydantic.Field(False, )
    ruleFilters: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    columns: typing.Optional[sourceColumnsCreate]

    
    





class propertiesDictCreate(framework.postgresmodel.BasePostgresModel):
    reconProcess: typing.Optional[str] = pydantic.Field("", **{})
    reconName: typing.Optional[str] = pydantic.Field("", **{})
    sourceType: typing.Optional[str] = pydantic.Field("", **{})
    filter: typing.Optional[str] = pydantic.Field("", **{})
    source: typing.Optional[str] = pydantic.Field("", **{})
    resultkey: typing.Optional[str] = pydantic.Field("", **{})
    sources: typing.Optional[typing.List[sourcesDictCreate]]
    matchColumn: typing.Optional[str] = pydantic.Field("", **{})
    processAllRecords: typing.Optional[bool] = pydantic.Field(False, )
    ruleName: typing.Optional[str] = pydantic.Field("", **{})
    isToleranceMatch: typing.Optional[bool] = pydantic.Field(False, )
    toleranceValue: typing.Optional[float] = pydantic.Field(0.0, **{})
    isBucketMatch: typing.Optional[bool] = pydantic.Field(False, )
    bucketside: typing.Optional[str] = pydantic.Field("", **{})
    matchDuplicateRecords: typing.Optional[bool] = pydantic.Field(False, )
    data: typing.Optional[str] = pydantic.Field("", **{})
    lookup: typing.Optional[str] = pydantic.Field("", **{})
    dataFields: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    lookupFields: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    includeCols: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    dataFieldsFilter: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    lookupFieldsFilter: typing.Optional[typing.List[str]] = pydantic.Field([], **{})

    
    





class nodesDictCreate(framework.postgresmodel.BasePostgresModel):
    outputConnectors: typing.Optional[typing.List[ConnectorDictCreate]]
    name: typing.Optional[str] = pydantic.Field("", **{})
    color: typing.Optional[str] = pydantic.Field("", **{})
    inputConnectors: typing.Optional[typing.List[ConnectorDictCreate]]
    properties: typing.Optional[propertiesDictCreate]
    className: typing.Optional[str] = pydantic.Field("", **{})
    width: typing.Optional[int] = pydantic.Field(0, **{})
    y: typing.Optional[int] = pydantic.Field(0, **{})
    x: typing.Optional[int] = pydantic.Field(0, **{})
    type: typing.Optional[str] = pydantic.Field("", **{})
    filter: typing.Optional[str] = pydantic.Field("", **{})
    id: typing.Optional[str] = pydantic.Field("", **{})

    
    





class FlowsCreate(framework.postgresmodel.BasePostgresModel):
    id: typing.Optional[str] = pydantic.Field("", **{})
    reconId: str
    connections: typing.List[connectionsDictCreate]
    nodes: typing.List[nodesDictCreate]

    class Config:
        collection_name = 'flows'
    
    

class Flows(framework.postgresmodel.PostgresModel):
    id: typing.Optional[str] = pydantic.Field("", **{})
    reconId: typing.Optional[str]
    connections: typing.Optional[typing.List[connectionsDictCreate]]
    nodes: typing.Optional[typing.List[nodesDictCreate]]
    
    class Config:
        collection_name = 'flows'
    

    

    


class FlowsGetResp(pydantic.BaseModel):
    data: typing.List[Flows]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)
class generateFlowParams(pydantic.BaseModel):
    
    
    pass
    

