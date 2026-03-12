Model GlBalance {
    AccountNumber str
    AccountName str
    reconId str
    reconName str
    reconProcess str
    sourceName str
    stmtDate str
    CLOSING_BAL str
    OPENING_BAL str
    ExecutionId str
    Action=> getGlBalance {
        recon_id str
        accnum str
        stmtdate optional str
    }
    Config=> {
        collection_name=gl_balance
    }
}