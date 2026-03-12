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
import ColumnDataTypes_enum



class dtypesDictCreate(framework.postgresmodel.BasePostgresModel):
    column: typing.Optional[str] = pydantic.Field("", **{})
    dtype: typing.Optional[str] = pydantic.Field("", **{})

    
    





class ColumnDataTypesCreate(framework.postgresmodel.BasePostgresModel):
    id: typing.Optional[str] = pydantic.Field("", **{})
    reconId: str
    source: str
    dtypes: typing.List[dtypesDictCreate]

    class Config:
        collection_name = 'column_data_types'
    
    

class ColumnDataTypes(framework.postgresmodel.PostgresModel):
    id: typing.Optional[str] = pydantic.Field("", **{})
    reconId: typing.Optional[str]
    source: typing.Optional[str]
    dtypes: typing.Optional[typing.List[dtypesDictCreate]]
    
    class Config:
        collection_name = 'column_data_types'
    

    

    


class ColumnDataTypesGetResp(pydantic.BaseModel):
    data: typing.List[ColumnDataTypes]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)
class getColumnDataTypesParams(pydantic.BaseModel):
    reconId: str
    source: str
    
    

