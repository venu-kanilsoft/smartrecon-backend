Model ReconExecution {
    
    Action=> uploadinputdata {
        reconId str
    }
    Action=> runrecons {
        stmtdate str
        reconids list str
    }
    Action=> runrecon {
        stmtdate str
        reconId str
    }
    Action=> rollback {
        reconId str
    }
}