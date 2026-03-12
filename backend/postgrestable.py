import framework.settings
from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy import Column, String, BigInteger, Integer, DateTime, Boolean, Float
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy import *
from sqlalchemy.orm import *

base = declarative_base()

dbName = framework.settings.dbName

class Recons(base):
    __tablename__ = dbName + '_recons'

    _id = Column(String, primary_key=True)
    # id = Column(String, nullable=False)
    reconName = Column(String, nullable=True)
    reconProcess = Column(String, nullable=True)
    reconId = Column(String, primary_key=True, nullable=True)
    sources = Column(JSONB, nullable=True)
    displayColumns = Column(JSONB, nullable=True)
    currentStmtDate = Column(String, nullable=True)
    prevStmtDate = Column(String, nullable=True)
    _type_ = Column(String, nullable=False)
    created = Column(BigInteger)
    updated = Column(BigInteger)

class ReconExecDetailsLog(base):
    __tablename__ = dbName + '_recon_exec_details_log'

    _id = Column(String, primary_key=True)
    statementDate = Column(DateTime, nullable=False)
    jobStatus = Column(String, nullable=True)
    errorMsg = Column(String, nullable=False)
    reconName = Column(String, nullable=False)
    reconProcess = Column(String, nullable=False)
    reconId = Column(String, primary_key=True, nullable=False)
    reconExecutionId = Column(String, nullable=False)
    stmtDate = Column(BigInteger, nullable=False)
    executionDateTime = Column(String, nullable=False)
    executedBy = Column(String, nullable=False)
    rollbackedBy = Column(String, nullable=True)
    cycleName = Column(String, nullable=False)
    _type_ = Column(String, nullable=False)
    created = Column(BigInteger)
    updated = Column(BigInteger)

class ColumnDataTypes(base):
    __tablename__ = dbName + '_column_data_types'

    _id = Column(String, primary_key=True)
    reconId = Column(String, primary_key=True, nullable=False)
    source = Column(String, nullable=False)
    dtypes = Column(JSONB, nullable=True)
    _type_ = Column(String, nullable=False)
    created = Column(BigInteger)
    updated = Column(BigInteger)

class CustomReport(base):
    __tablename__ = dbName + '_custom_reports'

    _id = Column(String, primary_key=True)
    reconName = Column(String, nullable=False)
    statementDate = Column(String, nullable=False)
    reconType =  Column(String, nullable=False)
    reportName = Column(String, nullable=False)
    details = Column(JSONB, nullable=True)
    reconId = Column(String, primary_key=True, nullable=False)
    _type_ = Column(String, nullable=False)
    created = Column(BigInteger)
    updated = Column(BigInteger)

class FeedFile(base):
    __tablename__ = dbName + '_feed_file'

    _id = Column(String, primary_key=True)
    reconName = Column(String, nullable=False)
    reconId = Column(String, primary_key=True, nullable=False)
    reconProcess = Column(String, nullable=False)
    emailId = Column(String, nullable=True)
    sftp = Column(JSONB, nullable=True)
    mountPoint = Column(JSONB, nullable=True)
    moveToProcess = Column(JSONB, nullable=True)
    _type_ = Column(String, nullable=False)
    created = Column(BigInteger)
    updated = Column(BigInteger)

class Flows(base):
    __tablename__ = dbName + '_flows'

    _id = Column(String, primary_key=True)
    reconId = Column(String, primary_key=True, nullable=False)
    connections = Column(JSONB, nullable=True)
    nodes = Column(JSONB, nullable=True)
    _type_ = Column(String, nullable=False)
    created = Column(BigInteger)
    updated = Column(BigInteger)

class GlBalance(base):
    __tablename__ = dbName + '_gl_balance'

    _id = Column(String, primary_key=True)
    AccountNumber = Column(String, nullable=True)
    AccountName = Column(String, nullable=True)
    reconId = Column(String, primary_key=True, nullable=False)
    reconName = Column(String, nullable=True)
    reconProcess = Column(String, nullable=True)
    sourceName = Column(String, nullable=True)
    stmtDate = Column(String, nullable=True)
    CLOSING_BAL = Column(String, nullable=True, default=0)
    OPENING_BAL = Column(String, nullable=True, default=0)
    ExecutionId = Column(String, nullable=True)
    Currency = Column(String, nullable=True)
    _type_ = Column(String, nullable=False)
    created = Column(BigInteger)
    updated = Column(BigInteger)

class Glmapping(base):
    __tablename__ = dbName + '_gl_mapping'

    _id = Column(String, primary_key=True)
    reconName = Column(String, nullable=False)
    reconProcess = Column(String, nullable=False)
    reconId = Column(String, primary_key=True, nullable=False)
    glNumber = Column(String, nullable=True)
    glName = Column(String, nullable=True)
    _type_ = Column(String, nullable=False)
    created = Column(BigInteger)
    updated = Column(BigInteger)

class MatchRuleReference(base):
    __tablename__ = dbName + '_match_rule_reference'

    _id = Column(String, primary_key=True)
    reconId = Column(String, primary_key=True, nullable=False)
    Rules = Column(JSONB, nullable=True)
    _type_ = Column(String, nullable=False)
    created = Column(BigInteger)
    updated = Column(BigInteger)

class MatchRuleSumColumns(base):
    __tablename__ = dbName + '_match_rule_sum_columns'

    _id = Column(String, primary_key=True)
    reconId = Column(String, primary_key=True, nullable=False)
    sumColumns = Column(JSONB, nullable=True)
    _type_ = Column(String, nullable=False)
    created = Column(BigInteger)
    updated = Column(BigInteger)

class ReconMetaInfo(base):
    __tablename__ = dbName + '_recon_meta_info'

    _id = Column(String, primary_key=True)
    reconName = Column(String, nullable=False)
    reconProcess = Column(String, nullable=False)
    reconId = Column(String, primary_key=True, nullable=False)
    reportDetails = Column(JSONB, nullable=True)
    statementDate = Column(DateTime, nullable=True)
    stmtdate = Column(BigInteger, nullable=True)
    reconExecutionId = Column(BigInteger, nullable=True)
    cycleWise = Column(String, nullable=True)
    incData = Column(JSONB, nullable=True)
    _type_ = Column(String, nullable=False)
    created = Column(BigInteger)
    updated = Column(BigInteger)

class ReconNotificationRule(base):
    __tablename__ = dbName + '_reconnotificationrule'

    _id = Column(String, primary_key=True)
    reconId = Column(String, primary_key=True, nullable=False)
    reconName = Column(String, nullable=False)
    autoTrigger = Column(Boolean, default=False)
    deltadateSelected = Column(String, nullable=True)
    subrecon = Column(String, nullable=True)
    levels = Column(JSONB, nullable=True)
    reports = Column(JSONB, nullable=True)
    scheduler = Column(JSONB, nullable=True)
    schedulerEnabled = Column(Boolean, default=False)
    unit = Column(String, nullable=True)
    isActive = Column(Boolean, default=False)
    templateName = Column(String, nullable=True)
    _type_ = Column(String, nullable=False)
    created = Column(BigInteger)
    updated = Column(BigInteger)

class ReconSummary(base):
    __tablename__ = dbName + '_recon_summary'

    _id = Column(String, primary_key=True)
    reconName = Column(String, nullable=False)
    statementDate = Column(String, nullable=True)
    reconType = Column(String, nullable=True)
    reportName = Column(String, nullable=True)
    details = Column(JSONB, nullable=True)
    reconId = Column(String, primary_key=True, nullable=False)
    reconExecutionId = Column(String, nullable=True)
    totalInput = Column(BigInteger, nullable=False)
    totalMatched = Column(BigInteger, nullable=False)
    totalUnmatched = Column(BigInteger, nullable=False)
    totalMatchedAmount = Column(Float, nullable=False)
    totalUnmatchedAmount = Column(Float, nullable=False)
    _type_ = Column(String, nullable=False)
    created = Column(BigInteger)
    updated = Column(BigInteger)

class SourceData(base):
    __tablename__ = dbName + '_source_data'

    _id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    loadType = Column(String, nullable=False)
    skipRow = Column(BigInteger, nullable=True)
    skipFooter = Column(BigInteger, nullable=True)
    parseIndex = Column(JSONB, nullable=True)
    file_id = Column(String, nullable=True)
    fileName = Column(String, nullable=True)
    delimiter = Column(String, nullable=True)
    headerkey = Column(String, nullable=True)
    footerKey = Column(String, nullable=True)
    filetype = Column(String, nullable=True)
    typeoftransaction = Column(String, nullable=True)
    merge = Column(String, nullable=True)
    database = Column(String, nullable=True)
    _type_ = Column(String, nullable=False)
    created = Column(BigInteger)
    updated = Column(BigInteger)

class SourceReference(base):
    __tablename__ = dbName + '_source_reference'

    _id = Column(String, primary_key=True)
    delimiter = Column(String, nullable=True)
    structureid = Column(String, nullable=True)
    loadType = Column(String, nullable=False)
    startdata = Column(String, nullable=True)
    enddata = Column(String, nullable=True)
    typeoftransaction = Column(String, nullable=True)
    headerkey = Column(String, nullable=True)
    footerkey = Column(String, nullable=True)
    merge = Column(String, nullable=True)
    sheetno = Column(BigInteger, nullable=True)
    filetype = Column(String, nullable=True)
    skiprows = Column(String, nullable=True)
    skipfooter = Column(String, nullable=True)
    structureFileName = Column(String, nullable=True)
    filePattern = Column(String, nullable=True)
    fileExtension = Column(String, nullable=True)
    postFilters = Column(JSONB, nullable=True)
    filters = Column(JSONB, nullable=True)
    derivedColumns = Column(JSONB, nullable=True)
    source = Column(String, nullable=True)
    struct = Column(String, nullable=True)
    fileName = Column(String, nullable=True)
    position = Column(BigInteger, nullable=True)
    sourceId = Column(String, nullable=True)
    reconId = Column(String, primary_key=True, nullable=False)
    feedDetails = Column(JSONB, nullable=True)
    secondStructure = Column(Boolean, default=False)
    folderName = Column(String, nullable=True)
    matchCriteria = Column(JSONB, nullable=True)
    masterMergeData = Column(JSONB, nullable=True)
    enrichColumnsData = Column(JSONB, nullable=True)
    master_id = Column(String, nullable=True)
    sourceType = Column(String, nullable=True)
    filterMergeData = Column(JSONB, nullable=True)
    matchingColumns = Column(JSONB, nullable=True)
    raiseError = Column(Boolean, default=False)
    _type_ = Column(String, nullable=False)
    created = Column(BigInteger)
    updated = Column(BigInteger)

class SystemAudit(base):
    __tablename__ = dbName + '_systemaudit'

    _id = Column(String, primary_key=True)
    email = Column(String, nullable=True)
    reconId = Column(String, primary_key=True, nullable=False)
    reconName = Column(String, primary_key=False)
    type = Column(String, nullable=True)
    actionStatus = Column(Boolean, default=False)
    reason = Column(String, nullable=True)
    system_idx = Column(String, nullable=True)
    comment = Column(String, nullable=True)
    remarksupdatedby = Column(String, nullable=True)
    remarksupdatedate = Column(DateTime, nullable=True)
    sourceName = Column(String, nullable=True)
    msg = Column(String, nullable=True)
    _type_ = Column(String, nullable=False)
    created = Column(BigInteger)
    updated = Column(BigInteger)

class TableSettings(base):
    __tablename__ = dbName + '_TableSettings'

    _id = Column(String, primary_key=True)
    columnRepr = Column(String, nullable=True)
    refreshInterval = Column(BigInteger, nullable=True)
    settings = Column(JSONB, nullable=True)
    tableId = Column(String, nullable=True)
    userId = Column(String, primary_key=True, nullable=False)
    _type_ = Column(String, nullable=False)
    created = Column(BigInteger)
    updated = Column(BigInteger)

class ReconIntegrationsMap(base):
    __tablename__ = dbName + '_integrations'

    _id = Column(String, primary_key=True)
    integrationName = Column(String, nullable=False)
    credentialId = Column(String, nullable=False)
    credentialName = Column(String, nullable=False)
    sourceReconName = Column(String, nullable=False)
    reconId = Column(String, primary_key=True, nullable=False)
    _type_ = Column(String, nullable=False)
    created = Column(BigInteger)
    updated = Column(BigInteger)

class SequenceGenerator(base):
    __tablename__ = dbName + '_sequence_generator'

    _id = Column(String, primary_key=True)
    sequence = Column(BigInteger, nullable=False)
    _type_ = Column(String, nullable=False)
    created = Column(BigInteger)
    updated = Column(BigInteger)

class Scheduler(base):
    __tablename__ = dbName + '_scheduler'

    _id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    uniqueid = Column(String, nullable=False)
    reconId = Column(ARRAY(String), nullable=True)
    stmtdate = Column(String, nullable=True)
    settings = Column(JSONB, nullable=True)
    scheduler = Column(String, nullable=True)
    isGlobal = Column(Boolean, default=False)
    isActive = Column(Boolean, default=False)
    email = Column(ARRAY(String), nullable=True)
    _type_ = Column(String, nullable=False)
    created = Column(BigInteger)
    updated = Column(BigInteger)

class ForceMatchCond(base):
    __tablename__ = dbName + '_forcematchcond'

    _id = Column(String, primary_key=True)
    reconId = Column(String, nullable=False)
    sourceColumns = Column(JSONB, nullable=True)
    isMatched = Column(Boolean, default=False)
    isUnMatched = Column(Boolean, default=False)
    _type_ = Column(String, nullable=False)
    created = Column(BigInteger)
    updated = Column(BigInteger)

class AggridSettings(base):
    __tablename__ = dbName + '_aggridsettings'

    _id = Column(String, primary_key=True)
    tableId = Column(String, nullable=False)
    columnRepr = Column(String, nullable=True)
    refreshInterval = Column(BigInteger, nullable=True)
    userId = Column(String, nullable=True)
    settings = Column(String, nullable=True)
    reconId = Column(String, nullable=True)
    function = Column(String, nullable=True)
    source = Column(String, nullable=True)
    _type_ = Column(String, nullable=False)
    created = Column(BigInteger)
    updated = Column(BigInteger)
