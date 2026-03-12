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
import ReconSummary_enum



class ReconSummaryDetailsCreate(framework.postgresmodel.BasePostgresModel):
    Source: typing.Optional[str] = pydantic.Field("", **{})
    MatchedAmount: typing.Optional[float] = pydantic.Field(0.0, **{})
    MatchedCount: typing.Optional[int] = pydantic.Field(0, **{})
    UnMatchedAmount: typing.Optional[float] = pydantic.Field(0.0, **{})
    UnMatchedCount: typing.Optional[int] = pydantic.Field(0, **{})
    ReversalAmount: typing.Optional[float] = pydantic.Field(0.0, **{})
    ReversalCount: typing.Optional[int] = pydantic.Field(0, **{})
    CarryForwardMatchedAmount: typing.Optional[float] = pydantic.Field(0.0, **{})
    CarryForwardMatchedCount: typing.Optional[int] = pydantic.Field(0, **{})
    CarryForwardUnMatchedAmount: typing.Optional[float] = pydantic.Field(0.0, **{})
    CarryForwardUnMatchedCount: typing.Optional[int] = pydantic.Field(0, **{})
    ForceMatchedAmount: typing.Optional[float] = pydantic.Field(0.0, **{})
    ForceMatchedCount: typing.Optional[int] = pydantic.Field(0, **{})

    
    





class ReconSummaryCreate(framework.postgresmodel.BasePostgresModel):
    reconName: str
    statementDate: str
    reconType: str
    reportName: str
    details: typing.List[ReconSummaryDetailsCreate]
    reconId: str
    reconExecutionId: str
    totalInput: int
    totalMatched: int
    totalUnmatched: int
    totalMatchedAmount: float
    totalUnmatchedAmount: float

    class Config:
        collection_name = 'recon_summary'
    
    

class ReconSummary(framework.postgresmodel.PostgresModel):
    reconName: typing.Optional[str]
    statementDate: typing.Optional[str]
    reconType: typing.Optional[str]
    reportName: typing.Optional[str]
    details: typing.Optional[typing.List[ReconSummaryDetailsCreate]]
    reconId: typing.Optional[str]
    reconExecutionId: typing.Optional[str]
    totalInput: typing.Optional[int]
    totalMatched: typing.Optional[int]
    totalUnmatched: typing.Optional[int]
    totalMatchedAmount: typing.Optional[float]
    totalUnmatchedAmount: typing.Optional[float]
    
    class Config:
        collection_name = 'recon_summary'
    

    

    


class ReconSummaryGetResp(pydantic.BaseModel):
    data: typing.List[ReconSummary]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)

