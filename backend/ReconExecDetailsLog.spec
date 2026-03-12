Model rollbackReconQuery internal {
    statementDate optional str
    reconName optional str
}

Model ReconExecDetailsLog {
    statementDate datetime
    jobStatus str
    errorMsg str
    reconName str
    reconProcess str
    reconId str
    reconExecutionId str
    stmtDate int
    executionDateTime str
    executedBy str
    rollbackedBy str
    Action=> getLatestExeDetails {
        reconId str
    }
    Action=> getMaxReconExecutionDoc {
        recon_names list str
    }
    Action=> rollbackRecon {
        query rollbackReconQuery
    }
    Action=> get_latest_execution_details {
    }
    Config=> {
        collection_name=recon_exec_details_log
    }
}
