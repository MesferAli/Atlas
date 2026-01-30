"""Picsellia Connector — Secure client for fetching assets and datasets.

Provides an async interface to Picsellia's data management platform
for image datasets, annotations, and model versioning.
All interactions are MZX-signed for traceability.
"""

from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urljoin

from pydantic import BaseModel, Field

from atlas.core.mzx_protocol import MZXBaseModel, MZXSignature, generate_mzx_id


class PicselliaAsset(BaseModel):
    """Represents a single asset from Picsellia."""

    id: str
    filename: str
    url: str | None = None
    width: int | None = None
    height: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PicselliaDataset(BaseModel):
    """Represents a dataset from Picsellia."""

    id: str
    name: str
    version: str = "latest"
    asset_count: int = 0
    label_classes: list[str] = Field(default_factory=list)


class PicselliaResponse(MZXBaseModel):
    """MZX-signed response from the Picsellia connector."""

    action: str
    data: dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    error: str | None = None


class PicselliaConnector:
    """Secure async client for the Picsellia data management platform.

    Usage:
        connector = PicselliaConnector(api_key="...", base_url="...")
        datasets = await connector.list_datasets()
        assets = await connector.get_assets(dataset_id="...")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://app.picsellia.com/api",
        organization: str | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._organization = organization
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request to the Picsellia API.

        Uses urllib for minimal dependencies. In production, swap to httpx/aiohttp.
        """
        import json
        import urllib.request

        url = urljoin(self._base_url + "/", path.lstrip("/"))
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query}"

        data = json.dumps(json_body).encode() if json_body else None
        req = urllib.request.Request(url, data=data, headers=self._headers, method=method)

        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(
                None, lambda: urllib.request.urlopen(req, timeout=30)
            )
            body = response.read().decode()
            return json.loads(body) if body else {}
        except Exception as e:
            raise ConnectionError(f"Picsellia API request failed: {e}") from e

    async def list_datasets(self, limit: int = 20) -> PicselliaResponse:
        """List available datasets.

        Args:
            limit: Maximum number of datasets to return.

        Returns:
            PicselliaResponse with dataset list.
        """
        mzx_id = generate_mzx_id()
        try:
            result = await self._request("GET", "/datasets", params={"limit": limit})
            datasets = [
                PicselliaDataset(
                    id=d.get("id", ""),
                    name=d.get("name", ""),
                    version=d.get("version", "latest"),
                    asset_count=d.get("asset_count", 0),
                ).model_dump()
                for d in result.get("items", result.get("results", []))
            ]
            return PicselliaResponse(
                action="list_datasets",
                data={"datasets": datasets, "total": len(datasets)},
                mzx_auth=MZXSignature(mzx_id=mzx_id),
            )
        except Exception as e:
            return PicselliaResponse(
                action="list_datasets",
                success=False,
                error=str(e),
                mzx_auth=MZXSignature(mzx_id=mzx_id),
            )

    async def get_assets(
        self, dataset_id: str, limit: int = 50
    ) -> PicselliaResponse:
        """Fetch assets from a specific dataset.

        Args:
            dataset_id: The dataset identifier.
            limit: Maximum number of assets to return.

        Returns:
            PicselliaResponse with asset list.
        """
        mzx_id = generate_mzx_id()
        try:
            result = await self._request(
                "GET",
                f"/datasets/{dataset_id}/assets",
                params={"limit": limit},
            )
            assets = [
                PicselliaAsset(
                    id=a.get("id", ""),
                    filename=a.get("filename", ""),
                    url=a.get("url"),
                    width=a.get("width"),
                    height=a.get("height"),
                ).model_dump()
                for a in result.get("items", result.get("results", []))
            ]
            return PicselliaResponse(
                action="get_assets",
                data={"assets": assets, "total": len(assets), "dataset_id": dataset_id},
                mzx_auth=MZXSignature(mzx_id=mzx_id),
            )
        except Exception as e:
            return PicselliaResponse(
                action="get_assets",
                success=False,
                error=str(e),
                mzx_auth=MZXSignature(mzx_id=mzx_id),
            )

    async def get_annotations(self, dataset_id: str, asset_id: str) -> PicselliaResponse:
        """Fetch annotations for a specific asset.

        Args:
            dataset_id: The dataset identifier.
            asset_id: The asset identifier.

        Returns:
            PicselliaResponse with annotation data.
        """
        mzx_id = generate_mzx_id()
        try:
            result = await self._request(
                "GET",
                f"/datasets/{dataset_id}/assets/{asset_id}/annotations",
            )
            return PicselliaResponse(
                action="get_annotations",
                data={"annotations": result, "asset_id": asset_id},
                mzx_auth=MZXSignature(mzx_id=mzx_id),
            )
        except Exception as e:
            return PicselliaResponse(
                action="get_annotations",
                success=False,
                error=str(e),
                mzx_auth=MZXSignature(mzx_id=mzx_id),
            )
