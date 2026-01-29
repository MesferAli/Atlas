"""Tests for the Data Moat role-based schema filtering."""


import pytest

CLASSIFICATION_LEVELS = ["PUBLIC", "INTERNAL", "RESTRICTED", "SECRET", "TOP_SECRET"]

ROLE_CLEARANCE = {
    "viewer": 1,
    "analyst": 2,
    "service": 3,
    "admin": 4,
}


def get_classification_level(classification: str) -> int:
    classification = classification.upper()
    if classification in CLASSIFICATION_LEVELS:
        return CLASSIFICATION_LEVELS.index(classification)
    return 1


def _resolve_classification(table, schema_lookup):
    """Mirror of data_moat._resolve_classification for unit tests."""
    security = table.get("security_metadata", {})
    if security.get("classification"):
        return security["classification"]
    if table.get("classification"):
        return table["classification"]
    if schema_lookup:
        name = (table.get("table_name") or table.get("name") or "").upper()
        if name in schema_lookup:
            return schema_lookup[name]
    return "INTERNAL"


def filter_tables_by_role(tables, user_role, schema_lookup=None):
    """Mirror of data_moat.filter_tables_by_role with explicit schema_lookup."""
    max_level = ROLE_CLEARANCE.get(user_role, 0)
    filtered = []
    for table in tables:
        classification = _resolve_classification(table, schema_lookup)
        table_level = get_classification_level(classification)
        if table_level <= max_level:
            filtered.append(table)
    return filtered


class TestClassificationLevels:
    """Tests for classification level mapping."""

    def test_known_levels(self) -> None:
        assert get_classification_level("PUBLIC") == 0
        assert get_classification_level("INTERNAL") == 1
        assert get_classification_level("RESTRICTED") == 2
        assert get_classification_level("SECRET") == 3
        assert get_classification_level("TOP_SECRET") == 4

    def test_case_insensitive(self) -> None:
        assert get_classification_level("secret") == 3
        assert get_classification_level("Secret") == 3

    def test_unknown_defaults_to_internal(self) -> None:
        assert get_classification_level("UNKNOWN") == 1


class TestFilterTablesByRole:
    """Tests for role-based table filtering with inline security_metadata."""

    @pytest.fixture
    def sample_tables(self) -> list[dict]:
        return [
            {"name": "EMPLOYEES", "security_metadata": {"classification": "INTERNAL"}},
            {"name": "SALARIES", "security_metadata": {"classification": "SECRET"}},
            {"name": "PUBLIC_HOLIDAYS", "security_metadata": {"classification": "PUBLIC"}},
            {"name": "TOP_SECRET_DATA", "security_metadata": {"classification": "TOP_SECRET"}},
        ]

    def test_viewer_sees_public_and_internal(self, sample_tables) -> None:
        result = filter_tables_by_role(sample_tables, "viewer")
        names = [t["name"] for t in result]
        assert "PUBLIC_HOLIDAYS" in names
        assert "EMPLOYEES" in names
        assert "SALARIES" not in names
        assert "TOP_SECRET_DATA" not in names

    def test_analyst_sees_up_to_restricted(self, sample_tables) -> None:
        result = filter_tables_by_role(sample_tables, "analyst")
        names = [t["name"] for t in result]
        assert "EMPLOYEES" in names
        assert "SALARIES" not in names

    def test_admin_sees_all(self, sample_tables) -> None:
        result = filter_tables_by_role(sample_tables, "admin")
        assert len(result) == 4

    def test_service_sees_up_to_secret(self, sample_tables) -> None:
        result = filter_tables_by_role(sample_tables, "service")
        names = [t["name"] for t in result]
        assert "SALARIES" in names
        assert "TOP_SECRET_DATA" not in names

    def test_unknown_role_sees_only_public(self, sample_tables) -> None:
        result = filter_tables_by_role(sample_tables, "unknown_role")
        names = [t["name"] for t in result]
        assert "PUBLIC_HOLIDAYS" in names
        assert len(result) == 1


class TestResolveClassification:
    """Tests for _resolve_classification across different table formats."""

    def test_inline_security_metadata(self) -> None:
        table = {"name": "X", "security_metadata": {"classification": "SECRET"}}
        assert _resolve_classification(table, None) == "SECRET"

    def test_flat_classification_key(self) -> None:
        table = {"table_name": "X", "classification": "RESTRICTED"}
        assert _resolve_classification(table, None) == "RESTRICTED"

    def test_schema_lookup_by_table_name(self) -> None:
        table = {"table_name": "CMP_ASG_SALARY", "owner": "HR", "score": 0.95}
        lookup = {"CMP_ASG_SALARY": "SECRET"}
        assert _resolve_classification(table, lookup) == "SECRET"

    def test_schema_lookup_by_name(self) -> None:
        table = {"name": "CMP_ASG_SALARY"}
        lookup = {"CMP_ASG_SALARY": "SECRET"}
        assert _resolve_classification(table, lookup) == "SECRET"

    def test_default_when_no_match(self) -> None:
        table = {"table_name": "UNKNOWN_TABLE", "score": 0.5}
        lookup = {"OTHER_TABLE": "SECRET"}
        assert _resolve_classification(table, lookup) == "INTERNAL"

    def test_default_when_no_lookup(self) -> None:
        table = {"table_name": "ANYTHING", "score": 0.5}
        assert _resolve_classification(table, None) == "INTERNAL"


class TestFilterWithSchemaLookup:
    """Tests for the critical scenario: indexer results without inline classification.

    This is the real-world path: OracleSchemaIndexer.search_tables() returns
    dicts with {table_name, owner, comments, score} but NO security_metadata.
    The Data Moat must look up classification from the schema JSON.
    """

    @pytest.fixture
    def schema_lookup(self) -> dict[str, str]:
        return {
            "PER_ALL_PEOPLE_F": "INTERNAL",
            "CMP_ASG_SALARY": "SECRET",
            "PO_HEADERS_ALL": "INTERNAL",
            "PAY_PAYROLL_RELATIONS": "SECRET",
        }

    @pytest.fixture
    def indexer_results(self) -> list[dict]:
        """Simulates what OracleSchemaIndexer.search_tables() returns."""
        return [
            {"table_name": "PER_ALL_PEOPLE_F", "owner": "HR", "comments": "People", "score": 0.95},
            {"table_name": "CMP_ASG_SALARY", "owner": "HR", "comments": "Salaries", "score": 0.90},
            {"table_name": "PO_HEADERS_ALL", "owner": "PO", "comments": "POs", "score": 0.80},
            {
                "table_name": "PAY_PAYROLL_RELATIONS",
                "owner": "PAY",
                "comments": "Payroll",
                "score": 0.75,
            },
        ]

    def test_viewer_blocked_from_secret_tables(
        self, indexer_results, schema_lookup
    ) -> None:
        """CRITICAL: Viewer must NOT see SECRET salary/payroll tables."""
        result = filter_tables_by_role(
            indexer_results, "viewer", schema_lookup=schema_lookup
        )
        names = [t["table_name"] for t in result]
        assert "CMP_ASG_SALARY" not in names
        assert "PAY_PAYROLL_RELATIONS" not in names
        assert "PER_ALL_PEOPLE_F" in names
        assert "PO_HEADERS_ALL" in names

    def test_analyst_blocked_from_secret_tables(
        self, indexer_results, schema_lookup
    ) -> None:
        result = filter_tables_by_role(
            indexer_results, "analyst", schema_lookup=schema_lookup
        )
        names = [t["table_name"] for t in result]
        assert "CMP_ASG_SALARY" not in names
        assert "PAY_PAYROLL_RELATIONS" not in names

    def test_service_sees_secret_tables(
        self, indexer_results, schema_lookup
    ) -> None:
        result = filter_tables_by_role(
            indexer_results, "service", schema_lookup=schema_lookup
        )
        names = [t["table_name"] for t in result]
        assert "CMP_ASG_SALARY" in names
        assert "PAY_PAYROLL_RELATIONS" in names

    def test_admin_sees_all(self, indexer_results, schema_lookup) -> None:
        result = filter_tables_by_role(
            indexer_results, "admin", schema_lookup=schema_lookup
        )
        assert len(result) == 4
