Model MasterDataCrosswalkAudit {
    fileName str
    displayName str
    remarks str
    comments str
    UserId str

    Config=> {
        collection_name=masterdata_crosswalk_audit
    }
}