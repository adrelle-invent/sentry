import enum


class ServiceEnvironment(enum.StrEnum):
    development = "development"
    staging = "staging"
    production = "production"


class ServiceStatus(enum.StrEnum):
    active = "active"
    inactive = "inactive"

class EventLevel(enum.StrEnum):
    debug = "debug"
    info = "info"
    warn = "warn"
    error = "error"
    fatal = "fatal"