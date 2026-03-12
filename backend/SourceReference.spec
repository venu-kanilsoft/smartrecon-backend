Model downloadSourceQuery internal {
    source optional str
    struct optional str
    feedDetails optional str
}

Model sourceDet {
    source optional str
    match optional str
    condition optional str
}

Model condition internal {
    cond optional list sourceDet
    filters optional list str
}

Model loadSourceRefQuery internal {
    filter optional bool
    filename optional str
    reconId optional str
    source_id optional str
}
Model storeOrderOfSourceQuery internal {
    source optional str
    struct optional str
    reconName optional str
    position optional str
}

Model SourceRef internal {
    reconName optional str
    struct optional str
    source optional str
    feedId optional str
}

Model addSourceRefQuery internal {
    _id optional str
    sourceRef optional list SourceRef
}

Model keyColumns internal {
    dataFields optional str
    lookupFields optional str
}

Model EnrichColumnsData internal {
    source optional str
    enrichColumns optional list str
    keyColumns optional list keyColumns
}

Model MasterMerge internal {
    source optional str
    master optional str
}

Model MasterMergeData internal {
    source optional str
    merge optional list MasterMerge
    join optional list str
}

Model updateSourceDetailsQuery internal {
    source_id optional str
    reconId optional str
    enrichColumnsData optional list EnrichColumnsData
    filterMergeData optional str
    startdata optional str
    enddata optional str
    fileMergeData optional str
    headerColumns optional list str
    masterMergeData optional list MasterMergeData
    headerColumns optional list str
    _rowIndex optional int
}

Model skipRowsQuery internal {
    reconName optional str
    source optional str
    skiprows optional int
    skipfooter optional int
}

Model loadSampleFileQuery internal {
    sourceId optional str
    showOriginal optional str
}

Model saveFiltersQuery internal {
    reconId optional str
    source_id optional str
    filters optional list str
}

Model deleteSourceQuery internal {
    reconId optional str
    source_id optional str
}

Model checkFilePropertyExpressionDoc internal {
    type optional str
    filter_type optional str
    columnName optional str
    value optional str
    index optional str
}

Model checkFilePropertyExpressionData internal {
    reconName optional str
    source optional str
    filters optional str
    derivedColumns optional str
}

Model deriveConditionColumnsData internal {
    reconName optional str
    reconProcess optional str
    source optional str
    customDerivedColumns optional list str
}

Model deriveColumnsQuery internal {
    selectedText optional str
    completeValue optional str
    selectedColumn optional str
    filterModule optional str
    filterColumn optional str
    reconId optional str
    source_id optional str
    columnName optional str
    filters optional list str
    derivedColumns optional list str
    saveSourceDetails optional bool
    feedDetails optional list str
}

Model feedDetailsDict internal {
    fileColumn optional str
    dataType optional str
    required optional bool
    datePattern optional str
    position optional int
    UIDisplayName optional str
}

Model filData internal {
    key optional str
    val optional str
    columnName optional str
    conditionData optional str
    condition optional str
    filter optional str
}

Model mergeData internal {
    _filterIndexId optional int
    filterData optional list filData
}

Model SourceReference {
    id optional str
    delimiter optional str
    structureid optional str
    loadType str
    startdata optional str
    enddata optional str
    skiprows optional str
    skipfooter optional str
    structureFileName optional str
    typeoftransaction optional str
    headerkey optional str
    footerkey optional str
    merge optional str
    filetype optional str
    filePattern optional str
    fileExtension optional str
    postFilters optional list str
    filters optional list str
    derivedColumns optional list str
    source optional str
    struct optional str
    fileName optional str
    position optional int
    sourceId optional str
    reconId optional str
    feedDetails optional list feedDetailsDict
    secondStructure optional bool
    folderName optional str
    matchCriteria optional list condition
    master_id optional str
    sourceType optional str
    enrichColumnsData optional list enrichColumnsData
    filterMergeData optional list mergeData
    Action=> downloadSource {
        id str
        query downloadSourceQuery
    }
    Action=> loadSourceRef {
        query loadSourceRefQuery
    }
    Action=> getSourceForRecon {
        reconName str 
    }
    Action=> storeOrderOfSource {
        query list storeOrderOfSourceQuery
    }
    Action=> addSourceRef {
        query addSourceRefQuery
    }
    Action=> getColumns {
        source optional str
    }
    Action=> updateSourceDetails {
        query updateSourceDetailsQuery
    }
    Action=> skipRows {
        query skipRowsQuery
    }
    Action=> loadSampleFile {
        query loadSampleFileQuery
    }
    Action=> saveFilters {
        query saveFiltersQuery
    }
    Action=> deleteSource {
        query deleteSourceQuery
    }
    Action=> checkFilePropertyExpression {
        doc checkFilePropertyExpressionDoc
        data checkFilePropertyExpressionData
    }
    Action=> deriveConditionColumns {
        data deriveConditionColumnsData
    }
    Action=> deriveColumns {
        query deriveColumnsQuery
    }
    Config=> {
        collection_name=source_reference
    }
}
