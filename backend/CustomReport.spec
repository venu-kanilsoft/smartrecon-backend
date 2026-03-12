Model CustomReportDetails internal {
    Source optional str
    StatementDate optional str
    ExecutionDateTime optional str
    STATEMENT_DATE optional str
    MatchedAmount optional float
    MatchedCount optional int
    UnMatchedAmount optional float
    UnMatchedCount optional int
    ReversalAmount optional float
    ReversalCount optional int
    CarryForwardMatchedAmount optional float
    CarryForwardMatchedCount optional int
    CarryForwardUnMatchedAmount optional float
    CarryForwardUnMatchedCount optional int
    ForceMatchedAmount optional float
    ForceMatchedCount optional int
    ClosingBalance optional float
}

Model CustomReport {
    reconName str
    statementDate str
    reconType str
    reportName str
    details list CustomReportDetails
    reconId str
    Action=> loadReport {
        reconId str
    }
    Action=> getDailySettlementRpt {
        statementDate str
    }
    Action=> generateReport {
        records: str
        groupBy: optional str
        sheetWise: optional bool
    }
    Config=> {
        collection_name=custom_reports
    }
}
