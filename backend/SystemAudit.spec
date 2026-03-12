Model SystemAudit {
    email optional str
    type optional str
    actionStatus optional bool
    reason optional str
    system_idx optional str
    comment optional str
    remarksupdatedby optional str
    remarksupdatedate optional date
    sourceName optional str
    msg optional str
    Config=> {
        collection_name=systemaudit
    }
}