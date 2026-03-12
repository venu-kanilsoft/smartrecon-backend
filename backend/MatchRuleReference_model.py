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
import MatchRuleReference_enum



class saveMatchRuleQueryCreate(framework.postgresmodel.BasePostgresModel):
    reconId: typing.Optional[str] = pydantic.Field("", **{})
    sumColumns: typing.Optional[typing.List[str]] = pydantic.Field([], **{})

    
    





class getValuesObjCreate(framework.postgresmodel.BasePostgresModel):
    test: typing.Optional[str] = pydantic.Field("", **{})

    
    





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

    
    





class ConnectorDictCreate(framework.postgresmodel.BasePostgresModel):
    name: str

    
    





class propertiesDictCreate(framework.postgresmodel.BasePostgresModel):
    reconProcess: typing.Optional[str] = pydantic.Field("", **{})
    reconName: typing.Optional[str] = pydantic.Field("", **{})
    sourceType: typing.Optional[str] = pydantic.Field("", **{})
    source: typing.Optional[str] = pydantic.Field("", **{})
    resultkey: typing.Optional[str] = pydantic.Field("", **{})
    sources: typing.Optional[typing.List[sourcesDictCreate]]

    
    





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
    id: typing.Optional[str] = pydantic.Field("", **{})

    
    





class ruleCreate(framework.postgresmodel.BasePostgresModel):
    Id: typing.Optional[str] = pydantic.Field("", **{})
    title: typing.Optional[str] = pydantic.Field("", **{})
    flowSources: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    matchDuplicateRecords: typing.Optional[bool] = pydantic.Field(False, )
    nodes: typing.Optional[typing.List[nodesDictCreate]]

    
    





class MatchRuleReferenceCreate(framework.postgresmodel.BasePostgresModel):
    id: typing.Optional[str]
    reconId: str
    reconName: str
    reconProcess: str
    Rules: typing.List[ruleCreate]

    class Config:
        collection_name = 'match_rule_reference'
    
    

class MatchRuleReference(framework.postgresmodel.PostgresModel):
    id: typing.Optional[str]
    reconId: typing.Optional[str]
    reconName: typing.Optional[str]
    reconProcess: typing.Optional[str]
    Rules: typing.Optional[typing.List[ruleCreate]]
    
    class Config:
        collection_name = 'match_rule_reference'
    

    

    


class MatchRuleReferenceGetResp(pydantic.BaseModel):
    data: typing.List[MatchRuleReference]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)
class saveMatchRuleParams(pydantic.BaseModel):
    query: saveMatchRuleQueryCreate
    
    
class getValuesParams(pydantic.BaseModel):
    obj: typing.Optional[getValuesObjCreate]
    ref: typing.Optional[str] = pydantic.Field("", **{})
    sep: typing.Optional[str] = pydantic.Field("", **{})
    default: typing.Optional[str] = pydantic.Field("", **{})
    
    
class setValuesParams(pydantic.BaseModel):
    obj: typing.Optional[getValuesObjCreate]
    ref: typing.Optional[str] = pydantic.Field("", **{})
    sep: typing.Optional[str] = pydantic.Field("", **{})
    
    
class downloadReportsParams(pydantic.BaseModel):
    reconName: str
    reconId: str
    
    
class getSelectedColumnsParams(pydantic.BaseModel):
    reconId: str
    
    

