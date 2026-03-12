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
import SourceData_enum



class SourceDataCreate(framework.postgresmodel.BasePostgresModel):
    id: typing.Optional[str]
    name: str
    type: str
    loadType: str
    skipRow: int = pydantic.Field(0, **{})
    skipFooter: int = pydantic.Field(0, **{})
    parseIndex: typing.List[str] = pydantic.Field("", **{})
    file_id: typing.Optional[str] = pydantic.Field("", **{})
    fileName: typing.Optional[str] = pydantic.Field("", **{})
    delimiter: typing.Optional[str] = pydantic.Field("", **{})
    headerkey: typing.Optional[str] = pydantic.Field("", **{})
    footerKey: typing.Optional[str] = pydantic.Field("", **{})
    filetype: typing.Optional[str] = pydantic.Field("", **{})
    typeoftransaction: typing.Optional[str] = pydantic.Field("", **{})
    merge: typing.Optional[str] = pydantic.Field("", **{})
    database: typing.Optional[str] = pydantic.Field("", **{})

    class Config:
        collection_name = 'source_data'
    
    

class SourceData(framework.postgresmodel.PostgresModel):
    id: typing.Optional[str]
    name: typing.Optional[str]
    type: typing.Optional[str]
    loadType: typing.Optional[str]
    skipRow: typing.Optional[int] = pydantic.Field(0, **{})
    skipFooter: typing.Optional[int] = pydantic.Field(0, **{})
    parseIndex: typing.Optional[typing.List[str]] = pydantic.Field("", **{})
    file_id: typing.Optional[str] = pydantic.Field("", **{})
    fileName: typing.Optional[str] = pydantic.Field("", **{})
    delimiter: typing.Optional[str] = pydantic.Field("", **{})
    headerkey: typing.Optional[str] = pydantic.Field("", **{})
    footerKey: typing.Optional[str] = pydantic.Field("", **{})
    filetype: typing.Optional[str] = pydantic.Field("", **{})
    typeoftransaction: typing.Optional[str] = pydantic.Field("", **{})
    merge: typing.Optional[str] = pydantic.Field("", **{})
    database: typing.Optional[str] = pydantic.Field("", **{})
    
    class Config:
        collection_name = 'source_data'
    

    

    


class SourceDataGetResp(pydantic.BaseModel):
    data: typing.List[SourceData]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)
class deleteDataParams(pydantic.BaseModel):
    sourceId: str
    
    

