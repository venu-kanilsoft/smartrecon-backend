Model saveMatchRuleQuery internal {
    reconId optional str
    sumColumns optional list str
}

Model getValuesObj internal {
    test optional str
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

Model ConnectorDict internal {
    name str
}

Model propertiesDict internal {
    reconProcess optional str
    reconName optional str
    sourceType optional str
    source optional str
    resultkey optional str
    sources optional list sourcesDict
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
    id optional str
}

Model rule internal {
    Id optional str
    title optional str
    flowSources optional list str
    matchDuplicateRecords optional bool
    nodes optional list nodesDict
}

Model MatchRuleReference {
    reconId str
    reconName str
    reconProcess str
    Rules list rule
    Action=> saveMatchRule {
        query saveMatchRuleQuery
    }
    Action=> getValues {
        obj optional getValuesObj
        ref optional str
        sep optional str
        default optional str
    }
    Action=> setValues {
        obj optional getValuesObj
        ref optional str
        sep optional str
    }
    Action=> downloadReports {
        reconName str
        reconId str 
    }
    Action=> getSelectedColumns {
        reconId str
    }
    Config=> {
        collection_name=match_rule_reference
    }
}
