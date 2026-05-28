import phonenumbers


class InvalidWhatsAppNumber(ValueError):
    pass


def normalize_whatsapp(raw: str, default_region: str = "EC") -> str:
    """
    Normalize a phone number to E.164 (e.g. '+593991234567').

    Accepts either international format ('+593 99 123 4567') or a national
    number assumed to be from `default_region` (Ecuador by default).
    Raises InvalidWhatsAppNumber if the number is missing, malformed,
    or fails phonenumbers validation.
    """
    if raw is None or not str(raw).strip():
        raise InvalidWhatsAppNumber("WhatsApp vacío")
    try:
        parsed = phonenumbers.parse(str(raw).strip(), default_region)
    except phonenumbers.NumberParseException as e:
        raise InvalidWhatsAppNumber(f"No se pudo parsear: {e}") from e
    if not phonenumbers.is_valid_number(parsed):
        raise InvalidWhatsAppNumber("Número de WhatsApp inválido")
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
