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
import SystemAudit_enum



class SystemAuditCreate(framework.postgresmodel.BasePostgresModel):
    email: typing.Optional[str] = pydantic.Field("", **{})
    reconId: typing.Optional[str] = pydantic.Field("", **{})
    type: typing.Optional[str] = pydantic.Field("", **{})
    actionStatus: typing.Optional[bool] = pydantic.Field(False, )
    reason: typing.Optional[str] = pydantic.Field("", **{})
    system_idx: typing.Optional[str] = pydantic.Field("", **{})
    comment: typing.Optional[str] = pydantic.Field("", **{})
    remarksupdatedby: typing.Optional[str] = pydantic.Field("", **{})
    remarksupdatedate: typing.Optional[datetime.date]
    sourceName: typing.Optional[str] = pydantic.Field("", **{})
    msg: typing.Optional[str] = pydantic.Field("", **{})

    class Config:
        collection_name = 'systemaudit'
    
    

class SystemAudit(framework.postgresmodel.PostgresModel):
    email: typing.Optional[str] = pydantic.Field("", **{})
    reconId: typing.Optional[str] = pydantic.Field("", **{})
    type: typing.Optional[str] = pydantic.Field("", **{})
    actionStatus: typing.Optional[bool] = pydantic.Field(False, )
    reason: typing.Optional[str] = pydantic.Field("", **{})
    system_idx: typing.Optional[str] = pydantic.Field("", **{})
    comment: typing.Optional[str] = pydantic.Field("", **{})
    remarksupdatedby: typing.Optional[str] = pydantic.Field("", **{})
    remarksupdatedate: typing.Optional[datetime.date]
    sourceName: typing.Optional[str] = pydantic.Field("", **{})
    msg: typing.Optional[str] = pydantic.Field("", **{})
    
    class Config:
        collection_name = 'systemaudit'
    

    

    


class SystemAuditGetResp(pydantic.BaseModel):
    data: typing.List[SystemAudit]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)

