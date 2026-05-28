"""Consentimiento obligatorio: el campo debe ser exactamente True en TODOS
los puntos de entrada (schema Pydantic, service y -en PG- el CHECK)."""
import pytest
from pydantic import ValidationError

from app.schemas.alta import AltaCreate


def _valid_payload(**overrides):
    base = {
        "sede": "urdesa",
        "nombre_mascota": "Firulais",
        "nombre_propietario": "Juan Perez",
        "whatsapp": "+593991234567",
        "fecha_atencion": "2026-05-28",
        "tipo_consulta": "control",
        "consentimiento": True,
    }
    base.update(overrides)
    return base


class TestConsentimientoAlta:
    def test_acepta_true(self):
        a = AltaCreate(**_valid_payload())
        assert a.consentimiento is True

    def test_rechaza_false(self):
        with pytest.raises(ValidationError):
            AltaCreate(**_valid_payload(consentimiento=False))

    def test_rechaza_ausente(self):
        payload = _valid_payload()
        payload.pop("consentimiento")
        with pytest.raises(ValidationError):
            AltaCreate(**payload)

    @pytest.mark.parametrize("falsy", [False, "false", "no", "0", 0, "off"])
    def test_rechaza_cualquier_forma_de_no_consentir(self, falsy):
        # Pydantic v2 hace coerción laxa ("true"/"yes" → True) y eso está bien
        # para formularios. Lo crítico: ningún valor que signifique "no consiente"
        # debe colarse como True.
        with pytest.raises(ValidationError):
            AltaCreate(**_valid_payload(consentimiento=falsy))
