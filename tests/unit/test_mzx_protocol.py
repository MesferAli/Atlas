"""Unit tests for the MZX Identity Protocol."""

import pytest

from atlas.core.mzx_protocol import (
    MZXAgentResponse,
    MZXBaseModel,
    MZXSignature,
    generate_mzx_id,
    mzx_signed,
)


class TestGenerateMzxId:
    """Tests for MZX ID generation."""

    def test_format(self):
        mzx_id = generate_mzx_id()
        parts = mzx_id.split("-")
        assert parts[0] == "MZX"
        assert parts[1] == "ATLAS"
        assert len(parts[2]) == 8  # YYYYMMDD
        assert len(parts[3]) == 12  # short uuid

    def test_custom_product(self):
        mzx_id = generate_mzx_id(product="WAFER")
        assert mzx_id.startswith("MZX-WAFER-")

    def test_uniqueness(self):
        ids = {generate_mzx_id() for _ in range(100)}
        assert len(ids) == 100


class TestMZXSignature:
    """Tests for MZXSignature model."""

    def test_default_creation(self):
        sig = MZXSignature()
        assert sig.mzx_id.startswith("MZX-ATLAS-")
        assert sig.product == "ATLAS"
        assert sig.version == "1.0.0"
        assert sig.timestamp is not None

    def test_custom_id(self):
        sig = MZXSignature(mzx_id="MZX-TEST-20260130-abc123def456")
        assert sig.mzx_id == "MZX-TEST-20260130-abc123def456"


class TestMZXBaseModel:
    """Tests for MZXBaseModel."""

    def test_auto_signature(self):
        model = MZXBaseModel()
        assert model.mzx_auth is not None
        assert model.mzx_auth.mzx_id.startswith("MZX-")

    def test_serialization(self):
        model = MZXBaseModel()
        data = model.model_dump()
        assert "mzx_auth" in data
        assert "mzx_id" in data["mzx_auth"]


class TestMZXAgentResponse:
    """Tests for MZXAgentResponse."""

    def test_success_response(self):
        resp = MZXAgentResponse(
            agent_name="Atlas",
            action="test_action",
            result={"key": "value"},
        )
        assert resp.success is True
        assert resp.agent_name == "Atlas"
        assert resp.mzx_auth.mzx_id.startswith("MZX-")

    def test_error_response(self):
        resp = MZXAgentResponse(
            agent_name="Atlas",
            action="failed_action",
            success=False,
            error="Something went wrong",
        )
        assert resp.success is False
        assert resp.error == "Something went wrong"


class TestMzxSigned:
    """Tests for the @mzx_signed decorator."""

    def test_sync_dict_return(self):
        @mzx_signed
        def my_func() -> dict:
            return {"result": "ok"}

        result = my_func()
        assert "mzx_id" in result
        assert result["mzx_id"].startswith("MZX-")
        assert result["result"] == "ok"

    @pytest.mark.asyncio
    async def test_async_dict_return(self):
        @mzx_signed
        async def my_func() -> dict:
            return {"result": "async_ok"}

        result = await my_func()
        assert "mzx_id" in result
        assert result["result"] == "async_ok"

    def test_sync_non_dict_return(self):
        @mzx_signed
        def my_func() -> str:
            return "hello"

        result = my_func()
        assert isinstance(result, MZXAgentResponse)
        assert result.result == {"value": "hello"}
