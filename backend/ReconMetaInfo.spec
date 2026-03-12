Model ReportDetail internal {
    displayName optional str
    filename optional str
    source optional str
}

Model Inc internal {
    source optional str
    incrementLoader optional str
    disableCarryForward optional bool
}

Model ReconMetaInfo {
    reconName str
    reconProcess str
    reconId str
    reportDetails list ReportDetail
    Config=> {
        collection_name=recon_meta_info
    }
}

Model ReconMetaInfoInc {
    reconName str
    reconId str
    incData list Inc
    Config=> {
        collection_name=reconMetaInfo
    }
}
