Model sublevel internal {
    ageingend optional int
    ageingstart optional int
    cc optional str
    escLevel optional str
    id optional int
    mailTo optional str
}

Model subreport internal {
    displayname optional str
    filename optional str
}

Model subscheduler internal {
    hours optional int
    minutes optional int
}

Model ReconNotificationRule {
    reconId str
    reconName str
    autoTrigger optional bool
    deltadateSelected str
    levels optional list sublevel
    reports optional list subreport
    scheduler optional subscheduler
    schedulerEnabled optional bool
    unit optional str
    Action=> notificationRule {
    }
    Action=> manualTrigger {
        reconId str
        reconName str
        stmtDate optional str
        subRecon optional str
    }
    Action=> listOfRecons {
        reconId str
    }
    Config=> {
        collection_name=reconnotificationrule
    }
}