Model sourceColumnsDetails internal {
    sourceName optional str
    Columns optional list str
}

Model ForceMatchCond {
    reconId str
    sourceColumns optional list sourceColumnsDetails
    isMatched optional bool
    isUnMatched optional bool
}