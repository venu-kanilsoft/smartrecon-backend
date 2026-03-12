Model MatchQuery internal {
    s1colname str
    s2colname str
    s1colcondition str
}
Model Recons {
    reconName str
    reconProcess str
    reconId str
    sources optional list str
    displayColumns optional list str
    currentStmtDate optional str
    prevStmtDate optional str
    Action=> getSummaryColumns {
    }
    Action=> get_mail_settings {
        reconId str
    }
    Action=> getReconSourceColumns {
        reconId str
    }
    Action=> get_similar_matches {
        reconId str
        match_query list MatchQuery
        source str
        destination str 
        records optional str
    }
    Action=> operationData {
        reconId str
        records str
        amountcol str
    }
    Action=> operationAllData {
        reconId str
        sources str
        stmtdate optional str
    }
    Action=> importRecon {
    }
    Action=> downloadReport {
        reconId str
        filename str
        stmtdate optional str
    }
    Action=> searchString {
        reconId str
        search_string str
        stmtdate optional str
    }
    Action=> exportXlsx {
        reconId str
        reconName str
        records str
        operation str
        stmtdate optional str
    }
    Action=> exportCsv {
        reconId str
        reconName str
        records str
        operation str
        stmtdate optional str
    }
    Action=> getExecutionDates {
        reconId str
    }
    Action=> getSummary {
        reconId str
        stmtdate optional str
    }
    Action=> getGlSummary {
        reconId str
        stmtdate optional str
    }
    Action=> getGlWiseSummary {
        reconId str
        glnumber str
        stmtdate optional str
    }
    Action=> getReports {
        reconId str
        stmtdate optional str
    }
    Action=> getReconData {
        reconId str
        operation str
        sourceName str
        stmtdate optional str
    }
    Action=> getGlReconData {
        reconId str
        glnumber str
        operation str
        sourceName str
        stmtdate optional str
    }
    Action=> getReconAllData {
        reconId str
        operation str
        sourceName str
        stmtdate optional str
    }
    Action=> getGlReconAllData {
        reconId str
        operation str
        glnumber str
        stmtdate optional str
    }
    Action=> force_match_records {
        reconId str
        records str
        comments optional str
    }
    Action=> authorize_force_match_records {
        reconId str
        records str
        comments optional str
    }
    Action=> reject_force_match_records {
        reconId str
        records str
        comments optional str
    }
    Action=> rollback_matched_records {
        reconId str
        records str
        comments optional str
    }
    Action=> authorize_rollback_records {
        reconId str
        records str
        comments optional str
    }
    Action=> reject_rollback_records {
        reconId str
        records str
        comments optional str
    }

    Action=> updateReconRemarksFromFile {
        reconId str
    }
    Action=> processRecon {
        reconId str
    }
    Action=> generateDisplayColumns {
        reconId str
    }
    Action=> deleteData {
        reconId str
    }
    Action=> getProcessRecons {
        reconProcess str
    }
    Action=> cloneSelectedRecon {
        reconId str
    }
    Action=> saveRecon {

    }
    Action=> getDisplayColumns {
        reconId str
    }
    Action=> updateData {
        reconId str
        records str
        operations str
        stmtdate optional str
    }
}
