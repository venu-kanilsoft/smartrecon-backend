Model ReconSummaryDetails internal {
    Source optional str
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
}

Model ReconSummary {
    reconName str
    statementDate str
    reconType str
    reportName str
    details list ReconSummaryDetails
    reconId str
    reconExecutionId str
    totalInput int
    totalMatched int
    totalUnmatched int
    totalMatchedAmount float
    totalUnmatchedAmount float
    Config=> {
        collection_name=recon_summary
    }
}
