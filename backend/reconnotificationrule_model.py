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
import reconnotificationrule_enum



class sublevelCreate(framework.postgresmodel.BasePostgresModel):
    ageingend: typing.Optional[int] = pydantic.Field(0, **{})
    ageingstart: typing.Optional[int] = pydantic.Field(0, **{})
    cc: typing.Optional[str] = pydantic.Field("", **{})
    escLevel: typing.Optional[str] = pydantic.Field("", **{})
    id: typing.Optional[int] = pydantic.Field(0, **{})
    mailTo: typing.Optional[str] = pydantic.Field("", **{})

    
    





class subreportCreate(framework.postgresmodel.BasePostgresModel):
    displayName: typing.Optional[str] = pydantic.Field("", **{})
    filename: typing.Optional[str] = pydantic.Field("", **{})

    
    





class subschedulerCreate(framework.postgresmodel.BasePostgresModel):
    hours: typing.Optional[int] = pydantic.Field(0, **{})
    minutes: typing.Optional[int] = pydantic.Field(0, **{})

    
    





class ReconNotificationRuleCreate(framework.postgresmodel.BasePostgresModel):
    reconId: str
    reconName: str
    autoTrigger: typing.Optional[bool] = pydantic.Field(False, )
    deltadateSelected: str
    subrecon: typing.Optional[str] = pydantic.Field("", **{})
    levels: typing.Optional[typing.List[sublevelCreate]]
    reports: typing.Optional[typing.List[subreportCreate]]
    scheduler: typing.Optional[subschedulerCreate]
    schedulerEnabled: typing.Optional[bool] = pydantic.Field(False, )
    unit: typing.Optional[str] = pydantic.Field("", **{})
    templateName: typing.Optional[str] = pydantic.Field("", **{})
    isActive: typing.Optional[bool] = pydantic.Field(False, )

    class Config:
        collection_name = 'reconnotificationrule'
    
    

class ReconNotificationRule(framework.postgresmodel.PostgresModel):
    reconId: typing.Optional[str]
    reconName: typing.Optional[str]
    autoTrigger: typing.Optional[bool] = pydantic.Field(False, )
    deltadateSelected: typing.Optional[str]
    subrecon: typing.Optional[str] = pydantic.Field("", **{})
    levels: typing.Optional[typing.List[sublevelCreate]]
    reports: typing.Optional[typing.List[subreportCreate]]
    scheduler: typing.Optional[subschedulerCreate]
    schedulerEnabled: typing.Optional[bool] = pydantic.Field(False, )
    unit: typing.Optional[str] = pydantic.Field("", **{})
    templateName: typing.Optional[str] = pydantic.Field("", **{})
    isActive: typing.Optional[bool] = pydantic.Field(False, )
    
    class Config:
        collection_name = 'reconnotificationrule'
    

    

    


class ReconNotificationRuleGetResp(pydantic.BaseModel):
    data: typing.List[ReconNotificationRule]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)
class notificationRuleParams(pydantic.BaseModel):
    
    
    pass
    
class manualTriggerParams(pydantic.BaseModel):
    reconId: str
    reconName: str
    stmtDate: typing.Optional[str] = pydantic.Field("", **{})
    subRecon: typing.Optional[str] = pydantic.Field("", **{})
    
    
class listOfReconsParams(pydantic.BaseModel):
    reconId: str
    
    

    
class listOfTemplatesParams(pydantic.BaseModel):
    reconId: str
    
  
