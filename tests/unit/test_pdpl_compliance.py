"""PDPL (Personal Data Protection Law) compliance tests.

Tests PII detection for Saudi-specific patterns (Saudi IDs, phone numbers,
emails) and validates masking behavior for Arabic/English content.
"""

import re

# ---------------------------------------------------------------------------
# Inline PII detector – mirrors Atlas/middleware_core.py ComplianceEngine
# so tests don't depend on the legacy middleware import chain (psycopg2 etc.)
# ---------------------------------------------------------------------------

PII_PATTERNS: dict[str, str] = {
    "SAUDI_ID": r"\b[12]\d{9}\b",
    "PHONE_SA": r"\b05\d{8}\b",
    "EMAIL": r"[^@]+@[^@]+\.[^@]+",
}


def check_pii(text: str) -> dict:
    """Detect and mask PII in text (standalone, no external deps)."""
    detected: list[str] = []
    masked_text = text

    for p_type, regex in PII_PATTERNS.items():
        matches = re.findall(regex, text)
        if matches:
            detected.append(p_type)
            for m in matches:
                if p_type == "PHONE_SA":
                    masked_text = masked_text.replace(m, "******" + m[-4:])
                elif p_type == "SAUDI_ID":
                    masked_text = masked_text.replace(m, "##########")
                elif p_type == "EMAIL":
                    parts = m.split("@")
                    masked_text = masked_text.replace(
                        m, parts[0][:2] + "***@" + parts[1]
                    )

    return {
        "has_pii": len(detected) > 0,
        "detected_types": detected,
        "masked_content": masked_text,
    }


# ---------------------------------------------------------------------------
# Saudi ID detection
# ---------------------------------------------------------------------------


class TestSaudiIDDetection:
    def test_detects_saudi_id_starting_with_1(self) -> None:
        result = check_pii("الهوية 1234567890")
        assert result["has_pii"] is True
        assert "SAUDI_ID" in result["detected_types"]

    def test_detects_saudi_id_starting_with_2(self) -> None:
        result = check_pii("Iqama number: 2098765432")
        assert "SAUDI_ID" in result["detected_types"]

    def test_masks_saudi_id(self) -> None:
        result = check_pii("ID: 1234567890")
        assert "1234567890" not in result["masked_content"]
        assert "##########" in result["masked_content"]

    def test_rejects_short_number(self) -> None:
        result = check_pii("رقم 12345")
        assert "SAUDI_ID" not in result.get("detected_types", [])

    def test_rejects_starting_with_other_digit(self) -> None:
        result = check_pii("Code: 3456789012")
        assert "SAUDI_ID" not in result.get("detected_types", [])


# ---------------------------------------------------------------------------
# Saudi phone number detection
# ---------------------------------------------------------------------------


class TestPhoneDetection:
    def test_detects_saudi_mobile(self) -> None:
        result = check_pii("الجوال 0512345678")
        assert "PHONE_SA" in result["detected_types"]

    def test_masks_phone_keeps_last_4(self) -> None:
        result = check_pii("Call 0551234567")
        assert "******4567" in result["masked_content"]

    def test_rejects_non_05_prefix(self) -> None:
        result = check_pii("رقم 0112345678")
        assert "PHONE_SA" not in result.get("detected_types", [])


# ---------------------------------------------------------------------------
# Email detection
# ---------------------------------------------------------------------------


class TestEmailDetection:
    def test_detects_email(self) -> None:
        result = check_pii("بريد ahmed@company.sa")
        assert "EMAIL" in result["detected_types"]

    def test_masks_email(self) -> None:
        result = check_pii("ahmed@company.sa is the contact")
        assert "ah***@company.sa" in result["masked_content"]


# ---------------------------------------------------------------------------
# Combined / edge cases
# ---------------------------------------------------------------------------


class TestCombinedPII:
    def test_detects_multiple_pii_types(self) -> None:
        text = "اسمي أحمد، هويتي 1234567890، جوالي 0512345678، إيميلي ahmed@test.sa"
        result = check_pii(text)
        assert result["has_pii"] is True
        assert set(result["detected_types"]) == {"SAUDI_ID", "PHONE_SA", "EMAIL"}

    def test_no_pii_clean_text(self) -> None:
        result = check_pii("مرحبا، كيف حالك؟")
        assert result["has_pii"] is False
        assert result["detected_types"] == []
        assert result["masked_content"] == "مرحبا، كيف حالك؟"

    def test_arabic_surrounding_text_preserved(self) -> None:
        result = check_pii("الموظف رقم 1234567890 في الرياض")
        assert result["masked_content"] == "الموظف رقم ########## في الرياض"

    def test_multiple_ids_all_masked(self) -> None:
        text = "IDs: 1111111111 and 2222222222"
        result = check_pii(text)
        assert result["masked_content"].count("##########") == 2


# ---------------------------------------------------------------------------
# Audit log sanitization
# ---------------------------------------------------------------------------


class TestAuditSanitization:
    """Verify that the audit logger redacts sensitive keys."""

    def test_sensitive_keys_redacted(self) -> None:
        from atlas.api.security.audit import get_audit_logger

        logger = get_audit_logger()
        details = {
            "password": "secret123",
            "token": "jwt-abc",
            "username": "ahmed",
        }
        sanitized = logger._sanitize_details(details)
        assert sanitized["password"] == "[REDACTED]"
        assert sanitized["token"] == "[REDACTED]"
        assert sanitized["username"] == "ahmed"
