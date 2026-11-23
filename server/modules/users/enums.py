import enum


class UserRole(enum.StrEnum):
    owner = "owner"
    admin = "admin"
    member = "member"