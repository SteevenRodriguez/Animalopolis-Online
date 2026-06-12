import enum


class Rol(str, enum.Enum):
    admin = "admin"
    staff = "staff"
    consulta = "consulta"


class Sede(str, enum.Enum):
    urdesa = "urdesa"
    ciudad_celeste = "ciudad_celeste"


class EstadoEnvio(str, enum.Enum):
    pendiente = "pendiente"
    enviado = "enviado"
    fallido = "fallido"


class TipoConsulta(str, enum.Enum):
    primera_consulta = "primera_consulta"
    control = "control"
    vacunacion = "vacunacion"
    desparasitacion = "desparasitacion"
    emergencia = "emergencia"
    cirugia = "cirugia"
    otro = "otro"


class TipoExamen(str, enum.Enum):
    sangre = "sangre"
    orina = "orina"
    heces = "heces"
    radiografia = "radiografia"
    ecografia = "ecografia"
    citologia = "citologia"
    otro = "otro"
