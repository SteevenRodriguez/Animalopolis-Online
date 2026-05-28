import pytest

from app.services.whatsapp_normalizer import (
    InvalidWhatsAppNumber,
    normalize_whatsapp,
)


class TestWhatsAppNormalizer:
    def test_normalizes_ecuador_national_format(self):
        assert normalize_whatsapp("0991234567", default_region="EC") == "+593991234567"

    def test_normalizes_international_format(self):
        assert normalize_whatsapp("+593 99 123 4567") == "+593991234567"

    def test_accepts_spaces_and_dashes(self):
        assert normalize_whatsapp("+593-99-123-4567") == "+593991234567"

    def test_rejects_empty(self):
        with pytest.raises(InvalidWhatsAppNumber):
            normalize_whatsapp("")

    def test_rejects_none(self):
        with pytest.raises(InvalidWhatsAppNumber):
            normalize_whatsapp(None)  # type: ignore[arg-type]

    def test_rejects_garbage(self):
        with pytest.raises(InvalidWhatsAppNumber):
            normalize_whatsapp("not-a-phone")

    def test_rejects_too_short(self):
        with pytest.raises(InvalidWhatsAppNumber):
            normalize_whatsapp("123")
