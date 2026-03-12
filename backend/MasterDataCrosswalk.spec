Model MasterDataCrosswalk {
    fileName str
    displayName str
    loadType str
    delimiter optional str
    createdBy str
    updatedBy optional str

    Action=> getMasterDataCrosswalkData {
        crosswalkId str
    }

    Action=> uploadMasterDataCrosswalk {
        
    }

    Config=> {
        collection_name=masterdata_crosswalk
    }
}