Model Connection internal {
    nodeID int
    connectorIndex int
}

Model connectionsDict internal {
    dest Connection
    source Connection
}

Model ConnectorDict internal {
    name str
}

Model sourceColumns internal {
    sumColumns optional list str
    debitCreditColumn optional list str
    matchColumns optional list str
}

Model sourcesDict internal {
    source optional str
    sourceTag optional str
    dropDuplicates optional bool
    ruleFilters optional list str
    columns optional sourceColumns
}

Model propertiesDict internal {
    reconProcess optional str
    reconName optional str
    sourceType optional str
    filter optional str
    source optional str
    resultkey optional str
    sources optional list sourcesDict
    matchColumn optional str
    processAllRecords optional bool
    ruleName optional str
    isToleranceMatch optional bool
    toleranceValue optional float
    isBucketMatch optional bool
    bucketside optional str
    matchDuplicateRecords optional bool
    data optional str
    lookup optional str
    dataFields optional list str
    lookupFields optional list str
    includeCols optional list str
}

Model nodesDict internal {
    outputConnectors optional list ConnectorDict
    name optional str
    color optional str
    inputConnectors optional list ConnectorDict
    properties optional propertiesDict
    className optional str
    width optional int
    y optional int
    x optional int
    type optional str
    filter optional str
    id optional str
}

Model Flows {
    id optional str
    reconId str
    connections list connectionsDict
    nodes list nodesDict
    Action=> generateFlow {

    }
    
    Config=> {
        collection_name=flows
    }
}
