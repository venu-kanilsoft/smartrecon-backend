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
import FeedFile_enum



class sftpDictCreate(framework.postgresmodel.BasePostgresModel):
    host: typing.Optional[str] = pydantic.Field("", **{})
    port: typing.Optional[str] = pydantic.Field("", **{})
    userName: typing.Optional[str] = pydantic.Field("", **{})
    password: typing.Optional[str] = pydantic.Field("", **{})
    filePattern: typing.Optional[str] = pydantic.Field("", **{})
    remotePath: typing.Optional[str] = pydantic.Field("", **{})
    tdate: typing.Optional[str] = pydantic.Field("", **{})
    dateFolderPattern: typing.Optional[str] = pydantic.Field("", **{})
    sourceName: typing.Optional[str] = pydantic.Field("", **{})
    sourceType: typing.Optional[str] = pydantic.Field("", **{})
    pemkey: typing.Optional[str] = pydantic.Field("", **{})
    tmonth: typing.Optional[str] = pydantic.Field("", **{})
    remoteProcessedPath: typing.Optional[str] = pydantic.Field("", **{})
    moveInputToProcess: typing.Optional[bool] = pydantic.Field(False, )
    dateFoldertdate: typing.Optional[str] = pydantic.Field("", **{})
    dateFoldertmonth: typing.Optional[str] = pydantic.Field("", **{})

    
    





class mountPointDictCreate(framework.postgresmodel.BasePostgresModel):
    mountPointPath: typing.Optional[str] = pydantic.Field("", **{})
    filePattern: typing.Optional[str] = pydantic.Field("", **{})
    dateFolderPattern: typing.Optional[str] = pydantic.Field("", **{})
    tdate: typing.Optional[str] = pydantic.Field("", **{})
    sourceName: typing.Optional[str] = pydantic.Field("", **{})
    sourceType: typing.Optional[str] = pydantic.Field("", **{})
    tmonth: typing.Optional[str] = pydantic.Field("", **{})
    moveInputToProcess: typing.Optional[bool] = pydantic.Field(False, )

    
    





class moveToProcessDictCreate(framework.postgresmodel.BasePostgresModel):
    processFilesystem: typing.Optional[str] = pydantic.Field("", **{})
    processPassword: typing.Optional[str] = pydantic.Field("", **{})
    processPort: typing.Optional[str] = pydantic.Field("", **{})
    processRemoteProcessPath: typing.Optional[str] = pydantic.Field("", **{})
    processUsername: typing.Optional[str] = pydantic.Field("", **{})
    processfilepat: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    processhost: typing.Optional[str] = pydantic.Field("", **{})
    dateFolderPattern: typing.Optional[str] = pydantic.Field("", **{})
    processSourceType: typing.Optional[str] = pydantic.Field("", **{})
    pemkey: typing.Optional[str] = pydantic.Field("", **{})

    
    





class FeedFileCreate(framework.postgresmodel.BasePostgresModel):
    id: typing.Optional[str] = pydantic.Field("", **{})
    reconName: str
    reconId: str
    reconProcess: str
    emailId: str
    sftp: typing.Optional[typing.List[sftpDictCreate]]
    mountPoint: typing.Optional[typing.List[mountPointDictCreate]]
    moveToProcess: typing.Optional[typing.List[moveToProcessDictCreate]]

    class Config:
        collection_name = 'feed_file'
    
    

class FeedFile(framework.postgresmodel.PostgresModel):
    id: typing.Optional[str] = pydantic.Field("", **{})
    reconName: typing.Optional[str]
    reconId: typing.Optional[str]
    reconProcess: typing.Optional[str]
    emailId: typing.Optional[str]
    sftp: typing.Optional[typing.List[sftpDictCreate]]
    mountPoint: typing.Optional[typing.List[mountPointDictCreate]]
    moveToProcess: typing.Optional[typing.List[moveToProcessDictCreate]]
    
    class Config:
        collection_name = 'feed_file'
    

    

    
class FeedFileCreateUpdateGetResp(pydantic.BaseModel):
    data: FeedFile
    status: bool = pydantic.Field(True)
    message: str = pydantic.Field("Success")
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)

class FeedFileGetResp(pydantic.BaseModel):
    data: typing.List[FeedFile]
    status: bool = pydantic.Field(True)
    message: str = pydantic.Field("Success")
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)
class getSourcesParams(pydantic.BaseModel):
    recon_id: str
    
    
class feedStatusMailParams(pydantic.BaseModel):
    reconId: str
    reconName: str
    reconProcess: str
    stmtDate: typing.Optional[str] = pydantic.Field("", **{})
    
    
class feed_status_schedulerParams(pydantic.BaseModel):
    reconList: typing.List[str]
    stmtdate: typing.Optional[str] = pydantic.Field("", **{})
    
    
class getFeedFileStatusParams(pydantic.BaseModel):
    reconId: str
    reconName: str
    reconProcess: str
    stmtDate: typing.Optional[str] = pydantic.Field("", **{})
    
    

class monitorFeedPathParams(pydantic.BaseModel):
    reconids: typing.List[str]
    stmtdate: typing.Optional[str] = pydantic.Field("", **{})



    
class getInputFileDetailsParams(pydantic.BaseModel):
    reconId: str
    reconName: str
    reconProcess: str
    stmtDate: typing.Optional[str] = pydantic.Field("", **{})
    
    
class downloadInpufileParams(pydantic.BaseModel):
    reconId: str
    sourceName: str
    filename: str
    stmtDate: typing.Optional[str] = pydantic.Field("", **{})
