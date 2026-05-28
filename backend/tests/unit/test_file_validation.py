import pytest

from app.services.file_validation import FileValidationError, validate_file

ALLOWED = ["application/pdf", "image/jpeg", "image/png", "image/webp"]


def _pdf(extra: bytes = b"") -> bytes:
    return b"%PDF-1.4\n%mock content\n" + extra


def _png(extra: bytes = b"") -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"IHDR" * 4 + extra


def _jpeg(extra: bytes = b"") -> bytes:
    return b"\xff\xd8\xff\xe0\x00\x10JFIF" + extra


def _webp(extra: bytes = b"") -> bytes:
    return b"RIFF\x24\x00\x00\x00WEBP" + extra


class TestValidFiles:
    def test_pdf(self):
        assert validate_file(
            data=_pdf(), declared_mime="application/pdf",
            allowed_mimes=ALLOWED, max_size=1_000_000
        ) == "application/pdf"

    def test_png(self):
        assert validate_file(
            data=_png(), declared_mime="image/png",
            allowed_mimes=ALLOWED, max_size=1_000_000
        ) == "image/png"

    def test_jpeg(self):
        assert validate_file(
            data=_jpeg(), declared_mime="image/jpeg",
            allowed_mimes=ALLOWED, max_size=1_000_000
        ) == "image/jpeg"

    def test_webp(self):
        assert validate_file(
            data=_webp(), declared_mime="image/webp",
            allowed_mimes=ALLOWED, max_size=1_000_000
        ) == "image/webp"

    def test_mime_with_charset_param(self):
        # Browsers may send "application/pdf; charset=binary"
        assert validate_file(
            data=_pdf(), declared_mime="application/pdf; charset=binary",
            allowed_mimes=ALLOWED, max_size=1_000_000
        ) == "application/pdf"


class TestRejections:
    def test_empty(self):
        with pytest.raises(FileValidationError):
            validate_file(data=b"", declared_mime="application/pdf",
                         allowed_mimes=ALLOWED, max_size=1_000_000)

    def test_oversize(self):
        with pytest.raises(FileValidationError, match="tamaño"):
            validate_file(data=_pdf(b"x" * 1000), declared_mime="application/pdf",
                         allowed_mimes=ALLOWED, max_size=500)

    def test_disallowed_mime(self):
        with pytest.raises(FileValidationError, match="no permitido"):
            validate_file(data=b"MZ\x90\x00", declared_mime="application/x-msdownload",
                         allowed_mimes=ALLOWED, max_size=1_000_000)

    def test_mime_magic_mismatch_pdf_with_png_mime(self):
        # Real PDF bytes but caller declares image/png — must be rejected.
        with pytest.raises(FileValidationError, match="no coincide"):
            validate_file(data=_pdf(), declared_mime="image/png",
                         allowed_mimes=ALLOWED, max_size=1_000_000)

    def test_executable_disguised_as_pdf(self):
        # Windows EXE bytes (MZ header) declared as application/pdf — magic check catches it.
        with pytest.raises(FileValidationError, match="no coincide"):
            validate_file(data=b"MZ\x90\x00\x03\x00\x00\x00", declared_mime="application/pdf",
                         allowed_mimes=ALLOWED, max_size=1_000_000)

    def test_riff_without_webp_marker(self):
        # RIFF container but not WEBP (e.g. AVI or WAV).
        avi = b"RIFF\x24\x00\x00\x00AVI "
        with pytest.raises(FileValidationError, match="WEBP"):
            validate_file(data=avi, declared_mime="image/webp",
                         allowed_mimes=ALLOWED, max_size=1_000_000)
