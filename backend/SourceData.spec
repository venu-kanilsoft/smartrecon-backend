Model SourceData {
    name str
    type str
    loadType str
    skipRow default=0 int
    skipFooter default=0 int
    parseIndex list default='' str
    
    file_id optional str
    fileName optional str
    delimiter optional str

    headerkey optional str
    footerKey optional str
    filetype optional str
    typeoftransaction optional str
    merge optional str

    Action=> deleteData {
        sourceId str
    }

    Config=> {
        collection_name=source_data
    }
}


