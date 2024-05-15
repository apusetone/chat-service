from enum import Enum, IntEnum


class CacheType(IntEnum):
    THROTTLING = 0
    TWO_FA = 1
    ACCESS_TOKEN = 2
    PUBSUB = 3
    CACHE = 4


class TokenType(Enum):
    ACCESS_TOKEN = "access_token"
    REFRESH_TOKEN = "refresh_token"


class NotificationType(IntEnum):
    DISABLED = 0
    MOBILE_PUSH = 1
    EMAIL = 2


class ChatType(IntEnum):
    DIRECT = 0
    GROUP = 1


class PlatformType(IntEnum):
    UNKNOWN = 0
    IOS = 1
    ANDROID = 2


class AWSServiceType(Enum):
    S3 = "s3"
    SNS = "sns"
    SES = "ses"
