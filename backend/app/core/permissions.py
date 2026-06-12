"""
Capability-based authorization. Roles map to a set of capabilities so adding
a new role does not require touching every endpoint.
"""
from enum import Enum

from app.models.enums import Rol


class Capability(str, Enum):
    ALTA_CREATE = "alta:create"
    ALTA_READ_OWN_SEDE = "alta:read_own_sede"
    ALTA_READ_ALL = "alta:read_all"
    ALTA_UPDATE = "alta:update"
    ALTA_MARK_SENT = "alta:mark_sent"

    EXAMEN_CREATE = "examen:create"
    EXAMEN_READ_OWN_SEDE = "examen:read_own_sede"
    EXAMEN_READ_ALL = "examen:read_all"
    EXAMEN_UPDATE = "examen:update"
    EXAMEN_DOWNLOAD = "examen:download"
    EXAMEN_MARK_SENT = "examen:mark_sent"

    PROPIETARIO_UPDATE = "propietario:update"
    MASCOTA_UPDATE = "mascota:update"

    USER_MANAGE = "user:manage"
    AUDIT_READ = "audit:read"


ROLE_CAPABILITIES: dict[str, set[Capability]] = {
    Rol.admin.value: {
        Capability.ALTA_CREATE,
        Capability.ALTA_READ_ALL,
        Capability.ALTA_UPDATE,
        Capability.ALTA_MARK_SENT,
        Capability.EXAMEN_CREATE,
        Capability.EXAMEN_READ_ALL,
        Capability.EXAMEN_UPDATE,
        Capability.EXAMEN_DOWNLOAD,
        Capability.EXAMEN_MARK_SENT,
        Capability.PROPIETARIO_UPDATE,
        Capability.MASCOTA_UPDATE,
        Capability.USER_MANAGE,
        Capability.AUDIT_READ,
    },
    Rol.staff.value: {
        Capability.ALTA_CREATE,
        Capability.ALTA_READ_OWN_SEDE,
        Capability.ALTA_UPDATE,
        Capability.EXAMEN_CREATE,
        Capability.EXAMEN_READ_OWN_SEDE,
        Capability.EXAMEN_UPDATE,
        Capability.EXAMEN_DOWNLOAD,
    },
    # Read-only profile. Sede-scoped like staff. Can download files but not
    # create, edit, or manage anything.
    Rol.consulta.value: {
        Capability.ALTA_READ_OWN_SEDE,
        Capability.EXAMEN_READ_OWN_SEDE,
        Capability.EXAMEN_DOWNLOAD,
    },
}


def has_capability(rol: str, cap: Capability) -> bool:
    return cap in ROLE_CAPABILITIES.get(rol, set())


def is_admin(rol: str) -> bool:
    return rol == Rol.admin.value
