Model dtypesDict internal {
    column optional str
    dtype optional str
}

Model ColumnDataTypes {
    id optional str
    reconId str
    source str
    dtypes list dtypesDict
    Action=> getColumnDataTypes {
        reconId str
        source str
    }
    Config=> {
        collection_name=column_data_types
    }
}