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
import SourceReference_enum



class downloadSourceQueryCreate(framework.postgresmodel.BasePostgresModel):
    source: typing.Optional[str] = pydantic.Field("", **{})
    struct: typing.Optional[str] = pydantic.Field("", **{})
    feedDetails: typing.Optional[str] = pydantic.Field("", **{})

    
    





class loadSourceRefQueryCreate(framework.postgresmodel.BasePostgresModel):
    filter: typing.Optional[bool] = pydantic.Field(False, )
    filename: typing.Optional[str] = pydantic.Field("", **{})
    reconId: typing.Optional[str] = pydantic.Field("", **{})
    source_id: typing.Optional[str] = pydantic.Field("", **{})

    
    





class storeOrderOfSourceQueryCreate(framework.postgresmodel.BasePostgresModel):
    source: typing.Optional[str] = pydantic.Field("", **{})
    struct: typing.Optional[str] = pydantic.Field("", **{})
    reconName: typing.Optional[str] = pydantic.Field("", **{})
    position: typing.Optional[str] = pydantic.Field("", **{})

    
    





class SourceRefCreate(framework.postgresmodel.BasePostgresModel):
    reconName: typing.Optional[str] = pydantic.Field("", **{})
    struct: typing.Optional[str] = pydantic.Field("", **{})
    source: typing.Optional[str] = pydantic.Field("", **{})
    feedId: typing.Optional[str] = pydantic.Field("", **{})

    
    





class addSourceRefQueryCreate(framework.postgresmodel.BasePostgresModel):
    _id: typing.Optional[str] = pydantic.Field("", **{})
    sourceRef: typing.Optional[typing.List[SourceRefCreate]]

    
    



class keyColumnsCreate(framework.postgresmodel.BasePostgresModel):
    dataFields: typing.Optional[str] = pydantic.Field("", **{})
    lookupFields: typing.Optional[str] = pydantic.Field("", **{})



class EnrichColumnsDataCreate(framework.postgresmodel.BasePostgresModel):
    source: typing.Optional[str] = pydantic.Field("", **{})
    enrichColumns: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    keyColumns: typing.Optional[typing.List[keyColumnsCreate]]

    
    


class MasterMergeCreate(framework.postgresmodel.BasePostgresModel):
    source: typing.Optional[str] = pydantic.Field("", **{})
    master: typing.Optional[str] = pydantic.Field("", **{})






class MasterMergeDataCreate(framework.postgresmodel.BasePostgresModel):
    source: typing.Optional[str] = pydantic.Field("", **{})
    merge: typing.Optional[typing.List[MasterMergeCreate]]
    join: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    masterFilter: typing.Optional[typing.List[str]] = pydantic.Field([], **{})

    
    





class updateSourceDetailsQueryCreate(framework.postgresmodel.BasePostgresModel):
    source_id: typing.Optional[str] = pydantic.Field("", **{})
    reconId: typing.Optional[str] = pydantic.Field("", **{})
    enrichColumnsData: typing.Optional[typing.List[EnrichColumnsDataCreate]]
    filterMergeData: typing.Optional[str] = pydantic.Field("", **{})
    startdata: typing.Optional[str] = pydantic.Field("", **{})
    enddata: typing.Optional[str] = pydantic.Field("", **{})
    fileMergeData: typing.Optional[str] = pydantic.Field("", **{})
    headerColumns: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    masterMergeData: typing.Optional[typing.List[MasterMergeDataCreate]]
    headerColumns: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    _rowIndex: typing.Optional[int] = pydantic.Field(0, **{})

    
    





class skipRowsQueryCreate(framework.postgresmodel.BasePostgresModel):
    reconName: typing.Optional[str] = pydantic.Field("", **{})
    source: typing.Optional[str] = pydantic.Field("", **{})
    skiprows: typing.Optional[int] = pydantic.Field(0, **{})
    skipfooter: typing.Optional[int] = pydantic.Field(0, **{})

    
    





class loadSampleFileQueryCreate(framework.postgresmodel.BasePostgresModel):
    sourceId: typing.Optional[str] = pydantic.Field("", **{})
    showOriginal: typing.Optional[str] = pydantic.Field("", **{})

    
    





class saveFiltersQueryCreate(framework.postgresmodel.BasePostgresModel):
    reconId: typing.Optional[str] = pydantic.Field("", **{})
    source_id: typing.Optional[str] = pydantic.Field("", **{})
    filters: typing.Optional[typing.List[str]] = pydantic.Field([], **{})

    
    





class deleteSourceQueryCreate(framework.postgresmodel.BasePostgresModel):
    reconId: typing.Optional[str] = pydantic.Field("", **{})
    source_id: typing.Optional[str] = pydantic.Field("", **{})

    
    





class checkFilePropertyExpressionDocCreate(framework.postgresmodel.BasePostgresModel):
    type: typing.Optional[str] = pydantic.Field("", **{})
    filter_type: typing.Optional[str] = pydantic.Field("", **{})
    columnName: typing.Optional[str] = pydantic.Field("", **{})
    value: typing.Optional[str] = pydantic.Field("", **{})
    index: typing.Optional[str] = pydantic.Field("", **{})

    
    





class checkFilePropertyExpressionDataCreate(framework.postgresmodel.BasePostgresModel):
    reconName: typing.Optional[str] = pydantic.Field("", **{})
    source: typing.Optional[str] = pydantic.Field("", **{})
    filters: typing.Optional[str] = pydantic.Field("", **{})
    derivedColumns: typing.Optional[str] = pydantic.Field("", **{})

    
    





class deriveConditionColumnsDataCreate(framework.postgresmodel.BasePostgresModel):
    reconName: typing.Optional[str] = pydantic.Field("", **{})
    reconProcess: typing.Optional[str] = pydantic.Field("", **{})
    source: typing.Optional[str] = pydantic.Field("", **{})
    customDerivedColumns: typing.Optional[typing.List[str]] = pydantic.Field([], **{})

    
    





class deriveColumnsQueryCreate(framework.postgresmodel.BasePostgresModel):
    selectedText: typing.Optional[str] = pydantic.Field("", **{})
    completeValue: typing.Optional[str] = pydantic.Field("", **{})
    selectedColumn: typing.Optional[str] = pydantic.Field("", **{})
    filterModule: typing.Optional[str] = pydantic.Field("", **{})
    filterColumn: typing.Optional[str] = pydantic.Field("", **{})
    reconId: typing.Optional[str] = pydantic.Field("", **{})
    source_id: typing.Optional[str] = pydantic.Field("", **{})
    columnName: typing.Optional[str] = pydantic.Field("", **{})
    filters: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    derivedColumns: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    saveSourceDetails: typing.Optional[bool] = pydantic.Field(False, )
    feedDetails: typing.Optional[typing.List[str]] = pydantic.Field([], **{})

    
    





class feedDetailsDictCreate(framework.postgresmodel.BasePostgresModel):
    fileColumn: typing.Optional[str] = pydantic.Field("", **{})
    dataType: typing.Optional[str] = pydantic.Field("", **{})
    required: typing.Optional[bool] = pydantic.Field(False, )
    datePattern: typing.Optional[str] = pydantic.Field("", **{})
    position: typing.Optional[int] = pydantic.Field(0, **{})
    UIDisplayName: typing.Optional[str] = pydantic.Field("", **{})

    
    


class sourceDetCreate(framework.postgresmodel.BasePostgresModel):
    source: typing.Optional[str] = pydantic.Field("", **{})
    match: typing.Optional[str] = pydantic.Field("", **{})
    condition: typing.Optional[str] = pydantic.Field("", **{})


class conditionCreate(framework.postgresmodel.BasePostgresModel):
    cond: typing.Optional[typing.List[sourceDetCreate]]
    filters: typing.Optional[typing.List[str]] = pydantic.Field([], **{})

class filDataCreate(framework.postgresmodel.BasePostgresModel):
    key: typing.Optional[str] = pydantic.Field("", **{})
    val: typing.Optional[str] = pydantic.Field("", **{})
    columnName: typing.Optional[str] = pydantic.Field("", **{})
    conditionData: typing.Optional[str] = pydantic.Field("", **{})
    condition: typing.Optional[str] = pydantic.Field("", **{})
    filter: typing.Optional[str] = pydantic.Field("", **{})

class mergeDataCreate(framework.postgresmodel.BasePostgresModel):
    _filterIndexId: typing.Optional[int] = pydantic.Field(0, **{})
    filterData: typing.Optional[typing.List[filDataCreate]]


class SourceReferenceCreate(framework.postgresmodel.BasePostgresModel):
    id: typing.Optional[str] = pydantic.Field("", **{})
    delimiter: typing.Optional[str] = pydantic.Field("", **{})
    structureid: typing.Optional[str] = pydantic.Field("", **{})
    loadType: str
    startdata: typing.Optional[str] = pydantic.Field("", **{})
    enddata: typing.Optional[str] = pydantic.Field("", **{})
    typeoftransaction: typing.Optional[str] = pydantic.Field("", **{})
    headerkey: typing.Optional[str] = pydantic.Field("", **{})
    footerkey: typing.Optional[str] = pydantic.Field("", **{})
    merge: typing.Optional[str] = pydantic.Field("", **{})
    sheetno: typing.Optional[int] = pydantic.Field(0, **{})
    filetype: typing.Optional[str] = pydantic.Field("", **{})
    skiprows: typing.Optional[str] = pydantic.Field("", **{})
    skipfooter: typing.Optional[str] = pydantic.Field("", **{})
    structureFileName: typing.Optional[str] = pydantic.Field("", **{})
    filePattern: typing.Optional[str] = pydantic.Field("", **{})
    fileExtension: typing.Optional[str] = pydantic.Field("", **{})
    postFilters: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    filters: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    derivedColumns: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    source: typing.Optional[str] = pydantic.Field("", **{})
    struct: typing.Optional[str] = pydantic.Field("", **{})
    fileName: typing.Optional[str] = pydantic.Field("", **{})
    position: typing.Optional[int] = pydantic.Field(0, **{})
    sourceId: typing.Optional[str] = pydantic.Field("", **{})
    reconId: typing.Optional[str] = pydantic.Field("", **{})
    feedDetails: typing.Optional[typing.List[feedDetailsDictCreate]]
    secondStructure: typing.Optional[bool] = pydantic.Field(False, )
    folderName: typing.Optional[str] = pydantic.Field("", **{})
    matchCriteria: typing.Optional[typing.List[conditionCreate]]
    masterMergeData: typing.Optional[typing.List[MasterMergeDataCreate]]
    enrichColumnsData: typing.Optional[typing.List[EnrichColumnsDataCreate]]
    master_id: typing.Optional[str] = pydantic.Field("", **{})
    sourceType: typing.Optional[str] = pydantic.Field("", **{})
    filterMergeData: typing.Optional[typing.List[mergeDataCreate]]
    matchingColumns: typing.Optional[typing.List[str]]
    raiseError: typing.Optional[bool] = pydantic.Field(False, )

    class Config:
        collection_name = 'source_reference'
    
    

class SourceReference(framework.postgresmodel.PostgresModel):
    id: typing.Optional[str] = pydantic.Field("", **{})
    delimiter: typing.Optional[str] = pydantic.Field("", **{})
    structureid: typing.Optional[str] = pydantic.Field("", **{})
    loadType: typing.Optional[str]
    startdata: typing.Optional[str] = pydantic.Field("", **{})
    enddata: typing.Optional[str] = pydantic.Field("", **{})
    typeoftransaction: typing.Optional[str] = pydantic.Field("", **{})
    headerkey: typing.Optional[str] = pydantic.Field("", **{})
    footerkey: typing.Optional[str] = pydantic.Field("", **{})
    merge: typing.Optional[str] = pydantic.Field("", **{})
    sheetno: typing.Optional[int] = pydantic.Field(0, **{})
    filetype: typing.Optional[str] = pydantic.Field("", **{})
    skiprows: typing.Optional[str] = pydantic.Field("", **{})
    skipfooter: typing.Optional[str] = pydantic.Field("", **{})
    structureFileName: typing.Optional[str] = pydantic.Field("", **{})
    filePattern: typing.Optional[str] = pydantic.Field("", **{})
    fileExtension: typing.Optional[str] = pydantic.Field("", **{})
    postFilters: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    filters: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    derivedColumns: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    source: typing.Optional[str] = pydantic.Field("", **{})
    struct: typing.Optional[str] = pydantic.Field("", **{})
    fileName: typing.Optional[str] = pydantic.Field("", **{})
    position: typing.Optional[int] = pydantic.Field(0, **{})
    sourceId: typing.Optional[str] = pydantic.Field("", **{})
    reconId: typing.Optional[str] = pydantic.Field("", **{})
    feedDetails: typing.Optional[typing.List[feedDetailsDictCreate]]
    secondStructure: typing.Optional[bool] = pydantic.Field(False, )
    folderName: typing.Optional[str] = pydantic.Field("", **{})
    matchCriteria: typing.Optional[typing.List[conditionCreate]]
    masterMergeData: typing.Optional[typing.List[MasterMergeDataCreate]]
    enrichColumnsData: typing.Optional[typing.List[EnrichColumnsDataCreate]]
    master_id: typing.Optional[str] = pydantic.Field("", **{})
    sourceType: typing.Optional[str] = pydantic.Field("", **{})
    filterMergeData: typing.Optional[typing.List[mergeDataCreate]]
    matchingColumns: typing.Optional[typing.List[str]]
    raiseError: typing.Optional[bool] = pydantic.Field(False, )
    
    class Config:
        collection_name = 'source_reference'
    

    

    


class SourceReferenceGetResp(pydantic.BaseModel):
    data: typing.List[SourceReference]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)
class downloadSourceParams(pydantic.BaseModel):
    id: str
    query: downloadSourceQueryCreate
    
    
class loadSourceRefParams(pydantic.BaseModel):
    query: loadSourceRefQueryCreate
    
    
class getSourceForReconParams(pydantic.BaseModel):
    reconName: str
    
    
class storeOrderOfSourceParams(pydantic.BaseModel):
    query: typing.List[storeOrderOfSourceQueryCreate]
    
    
class addSourceRefParams(pydantic.BaseModel):
    query: addSourceRefQueryCreate
    
    
class getColumnsParams(pydantic.BaseModel):
    source: typing.Optional[str] = pydantic.Field("", **{})
    
    
class updateSourceDetailsParams(pydantic.BaseModel):
    query: updateSourceDetailsQueryCreate
    
    
class skipRowsParams(pydantic.BaseModel):
    query: skipRowsQueryCreate
    
    
class loadSampleFileParams(pydantic.BaseModel):
    query: loadSampleFileQueryCreate
    
    
class saveFiltersParams(pydantic.BaseModel):
    query: saveFiltersQueryCreate
    
    
class deleteSourceParams(pydantic.BaseModel):
    query: deleteSourceQueryCreate
    
    
class checkFilePropertyExpressionParams(pydantic.BaseModel):
    doc: checkFilePropertyExpressionDocCreate
    data: checkFilePropertyExpressionDataCreate
    
    
class deriveConditionColumnsParams(pydantic.BaseModel):
    data: deriveConditionColumnsDataCreate
    
    
class deriveColumnsParams(pydantic.BaseModel):
    query: deriveColumnsQueryCreate
    
    

