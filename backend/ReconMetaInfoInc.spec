Model Inc internal {
    source optional str
    incrementLoader optional str
    disableCarryForward optional bool
}

Model ReconMetaInfoInc {
    reconName str
    reconId str
    incData optional list Inc
    Config=> {
        collection_name=recon_meta_info_inc
    }
}