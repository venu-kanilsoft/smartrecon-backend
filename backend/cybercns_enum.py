import enum


class CompanySource(enum.IntEnum):
    local = 1
    integration = 2


import enum


class OSType(enum.IntEnum):
    LinuxX86 = 1
    Windows = 2
    Darwin = 3
    LinuxArm = 4


import enum


class AgentType(enum.IntEnum):
    Probe = 1
    LightWeight = 2
    LightWeightInstalled = 3
    ExternalScanAgent = 4


import enum


class ScanType(enum.IntEnum):
    FullScan = 1
    AssetScan = 2
    VulnerabilityScan = 3
    ExternalScan = 4
    ActiveDirectoryScan = 5
    SnmpScan = 6
    LightWeightAgentScan = 7
    FirewallScan = 8


import enum


class JobStatus(enum.IntEnum):
    Initiated = 1
    Started = 2
    Running = 3
    Partial = 4
    Completed = 5
    Failed = 6


import enum


class CredType(enum.IntEnum):
    Windows = 1
    Linux = 2
    VMWare = 3
    Darwin = 4
    NetworkDevice = 5


import enum


class FirewallType(enum.IntEnum):
    SonicWall = 1


import enum


class ApplicationStatus(enum.IntEnum):
    Allowed = 1
    Denied = 2
    Mandatory = 3


