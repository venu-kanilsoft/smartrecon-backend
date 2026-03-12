Model sftpDict internal {
    host optional str
    port optional str
    userName optional str
    password optional str
    filePattern optional str
    remotePath optional str
    tdate optional str
    dateFolderPattern optional str
    sourceName optional str
    sourceType optional str
    pemkey optional str
    tmonth optional str
    remoteProcessedPath optional str
    moveInputToProcess optional bool
    dateFoldertdate optional str
    dateFoldertmonth optional str
}

Model mountPointDict internal {
    mountPointPath optional str
    filePattern optional str
    dateFolderPattern optional str
    tdate optional str
    sourceName optional str
    sourceType optional str
    tmonth optional str
    moveInputToProcess optional bool
}

Model moveToProcessDict internal {
    processFilesystem optional str
    processPassword optional str
    processPort optional str
    processRemoteProcessPath optional str
    processUsername optional str
    processfilepat optional list str
    processhost optional str
    dateFolderPattern optional str
    processSourceType optional str
    pemkey optional str
}

Model FeedFile {
    id optional str
    reconName str
    reconId str
    reconProcess str
    emailId str
    sftp optional list sftpDict
    mountPoint optional list mountPointDict
    moveToProcess optional list moveToProcessDict
    Action=> getSources {
        recon_id str
    }
    Action=> feedStatusMail {
        recon_id str
        reconName str
        reconProcess str
        stmtDate optional str
    }
    Action=> feed_status_scheduler {
        reconList list str
    }
    Action=> getFeedFileStatus {
        reconId str
        reconName str
        reconProcess str
        stmtDate optional str
    }
    Action=> getInputFileDetails {
        reconId str
        reconName str
        reconProcess str
        stmtDate optional str
    }
    Action=> downloadInpufile {
        reconId str
        sourceName str
        filename str
        stmtdate optional str
    }
    Config=> {
        collection_name=feed_file
    }
}
