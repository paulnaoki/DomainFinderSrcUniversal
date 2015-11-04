class Ec2InstanceType:
    T1_Micro = "t1.micro"  # not working with linux ubuntu OS, due to nvm not supported
    T2_Micro = "t2.micro"
    T2_Small = "t2.small"  # option for small host
    T2_Med = "t2.medium"
    T2_Large = "t2.large"
    M4_Large = "m4.large"
    M4_X = "m4.xlarge"   # option for small crawler
    M4_2X = "m4.2xlarge"
    M4_4X = "m4.4xlarge"  # option for large crawler, 8 times of M4_X
    M4_10X = "m4.10xlarge"
    M3_Med = "m3.medium"
    M3_Large = "m3.large"
    M3_X = "m3.xlarge"
    M3_2X = "m3.2xlarge"
    C4_Large = "c4.large"
    C4_X = "c4.xlarge"
    C4_2X = "c4.2xlarge"
    C4_4X = "c4.4xlarge"
    C4_8X = "c4.8xlarge"
    C3_Large = "c3.large"
    C3_X = "c3.xlarge"
    C3_2X = "c3.2xlarge"
    C3_4X = "c3.4xlarge"
    C3_8X = "c3.8xlarge"
    G2_2X = "g2.2xlarge"
    G2_8X = "g2.8xlarge"
    R3_Large = "r3.large"  # option for large host (memory optimized)
    R3_X = "r3.xlarge"
    R3_2X = "r3.2xlarge"
    R3_4X = "r3.4xlarge"
    E3_8X = "r3.8xlarge"
    I2_X = "i2.xlarge"
    I2_2X = "i2.2xlarge"
    I2_4X = "i2.4xlarge"
    I2_8X = "i2.8xlarge"
    D2_X = "d2.xlarge"
    D2_2X = "d2.2xlarge"
    D2_4X = "d2.4xlarge"
    D2_8X = "d2.8xlarge"


class ImageId:
    Host_v1048 = "ami-6c826f5f"
    Crawler_v1047 = "ami-a256b691"


class SecureGroupId:
    CrawlOperation = "sg-03332e66"


class SshSecureKeyName:
    Default = "DeveloperKeyPair"


class Region:
    US_EAST_1 = "us-east-1"
    US_WEST_2 = "us-west-2"
    US_WEST_1 = "us-west-1"
    EU_WEST_1 = "eu-west-1"
    EU_CEN_1 = "eu-central-1"
    AP_SE_1 = "ap-southeast-1"
    AP_SE_2 = "ap-southeast-2"
    AP_NE_1 = "ap-northeast-1"
    SA_EAST_1 = "sa-east-1"


class Zone:
    # not open not
    US_West_1A = "us-west-1a"
    US_West_1C = "us-west-1c"

    # use this region
    US_West_2A = "us-west-2a"
    US_West_2B = "us-west-2b"
    US_West_2C = "us-west-2c"


class SubnetID:
    # not open not
    US_West_1A = "subnet-c92437ab"
    US_West_1C = "subnet-3b9bc67d"

    # use this region
    US_West_2A = "subnet-93071af1"
    US_West_2B = "subnet-b2625ec6"
    US_West_2C = "subnet-15a7f853"


class EndPoint:
    EC2 = "ec2.{0:s}.amazonaws.com"


class InstanceStatus:
    pass


class SpotInstanceState:
    """
    state for spot instance in response of DescribeSpotInstances
    http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-bid-status.html#spot-instance-bid-status-understand
    """
    Open = "open"
    Active = "active"
    Closed = "closed"
    Cancelled = "cancelled"
    Failed = "failed"


class SpotInstanceStatusCode:
    """
    status code for spot instance in response of DescribeSpotInstances
    comes with SpotInstanceState, serves as additional info
    """
    # Fulfilled-terminal
    CancelledButRunning = "request-canceled-and-instance-running"  # cancelled
    TerminationMarked = "marked-for-termination"  # closed
    TerminationByPrice = "instance-terminated-by-price"  # closed
    TerminationByUser = "instance-terminated-by-user"  # closed or cancelled
    TerminationNoCap = "instance-terminated-no-capacity"  # closed
    TerminationOverCap = "instance-terminated-capacity-oversubscribed"  # closed
    TerminationGroupConst = "instance-terminated-launch-group-constraint"  # closed

    # Pending evaluation
    PendingEval = "pending-evaluation"  # open
    BadParam = "bad-parameters"  # closed or failed

    # Holding # open
    CapNotAvailable = "capacity-not-available"
    CapOver = "capacity-oversubscribed"
    PriceLow = "price-too-low"
    NotScheduled = "not-scheduled-yet"
    LaunchGroupConst = "launch-group-constraint"
    AvailableZoneConst = "az-group-constraint"
    PlacementGroupConst = "placement-group-constraint"
    ConstNotFulfillable = "constraint-not-fulfillable"

    # Pending evaluation/fulfillment-terminal
    ScheduleExp = "schedule-expired"  # closed
    CancelBeforeFulfill = "canceled-before-fulfillment"  # cancelled
    SysError = "system-error"  # closed

    # Pending fulfillment
    PendingFulfill = "pending-fulfillment"  # open

    # Fulfilled
    FulFilled = "fulfilled"  # active


class InstanceState:
    """
    state for instance in response of DescribeInstances
    http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstanceState.html
    """
    Pending = "pending"
    Running = "running"
    ShutDown = "shutting-down"
    Terminated = "terminated"
    Stopping = "stopping"
    Stopped = "stopped"


class InstanceStatusCode:
    """
    status code for instance in response of DescribeInstances
    comes with InstanceState, serves as additional info
    """
    Pending = 0
    Running = 16
    ShutDown = 32
    Terminated = 48
    Stopping = 64
    Stopped = 80