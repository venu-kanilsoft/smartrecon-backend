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
import ForceMatchCond_enum



class sourceColumnsDetailsCreate(framework.postgresmodel.BasePostgresModel):
    sourceName: typing.Optional[str] = pydantic.Field("", **{})
    Columns: typing.Optional[typing.List[str]] = pydantic.Field([], **{})

    
    





class ForceMatchCondCreate(framework.postgresmodel.BasePostgresModel):
    reconId: str
    sourceColumns: typing.Optional[typing.List[sourceColumnsDetailsCreate]]
    isMatched: typing.Optional[bool] = pydantic.Field(False, )
    isUnMatched: typing.Optional[bool] = pydantic.Field(False, )

    class Config:
        collection_name = 'forcematchcond'
    
    

class ForceMatchCond(framework.postgresmodel.PostgresModel):
    reconId: typing.Optional[str]
    sourceColumns: typing.Optional[typing.List[sourceColumnsDetailsCreate]]
    isMatched: typing.Optional[bool] = pydantic.Field(False, )
    isUnMatched: typing.Optional[bool] = pydantic.Field(False, )
    
    class Config:
        collection_name = 'forcematchcond'
    

    

    


class ForceMatchCondGetResp(pydantic.BaseModel):
    data: typing.List[ForceMatchCond]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)

