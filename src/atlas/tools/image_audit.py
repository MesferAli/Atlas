"""Image Quality Audit Tool — Detect blur and luminance issues.

MZX-signed tool for auditing image quality in data pipelines.
Checks for blur (Laplacian variance) and luminance problems.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from atlas.agents.atlas_agent import register_tool
from atlas.core.config import get_config
from atlas.core.mzx_protocol import mzx_signed


def _compute_blur_score(image: np.ndarray) -> float:
    """Compute blur score using Laplacian variance.

    Higher values mean sharper images. A value below the threshold
    indicates a blurry image.
    """
    if image.ndim == 3:
        # Convert to grayscale using luminosity method
        gray = np.dot(image[..., :3], [0.2989, 0.5870, 0.1140]).astype(np.float64)
    else:
        gray = image.astype(np.float64)

    # Laplacian kernel
    kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float64)

    # Apply convolution (simplified — no scipy dependency)
    h, w = gray.shape
    if h < 3 or w < 3:
        return 0.0

    padded = np.pad(gray, 1, mode="reflect")
    laplacian = np.zeros_like(gray)
    for i in range(3):
        for j in range(3):
            laplacian += kernel[i, j] * padded[i : i + h, j : j + w]

    return float(np.var(laplacian))


def _compute_luminance(image: np.ndarray) -> dict[str, float]:
    """Compute mean and std luminance of an image."""
    if image.ndim == 3:
        gray = np.dot(image[..., :3], [0.2989, 0.5870, 0.1140])
    else:
        gray = image.astype(np.float64)

    return {
        "mean": float(np.mean(gray)),
        "std": float(np.std(gray)),
        "min": float(np.min(gray)),
        "max": float(np.max(gray)),
    }


@register_tool(
    "audit_image_quality",
    description="Detect blur and luminance issues in images",
    is_async=False,
)
@mzx_signed
def audit_image_quality(image_input: str | np.ndarray) -> dict[str, Any]:
    """Audit image quality for blur and luminance problems.

    Args:
        image_input: Either a file path (str) or a numpy array.

    Returns:
        Dict with blur_score, luminance stats, and issue flags.
    """
    cfg = get_config()
    tool_cfg = cfg.tools.get("audit_image_quality")
    blur_threshold = tool_cfg.blur_threshold if tool_cfg else 100.0
    lum_min = tool_cfg.luminance_min if tool_cfg else 30
    lum_max = tool_cfg.luminance_max if tool_cfg else 220

    if isinstance(image_input, str):
        try:
            from PIL import Image

            img = Image.open(image_input).convert("RGB")
            image = np.array(img)
        except ImportError:
            return {
                "error": "Pillow is required for file-based image audit",
                "summary": "Cannot audit: Pillow not installed",
            }
        except Exception as e:
            return {"error": str(e), "summary": f"Cannot open image: {e}"}
    else:
        image = image_input

    blur_score = _compute_blur_score(image)
    luminance = _compute_luminance(image)

    issues: list[str] = []
    if blur_score < blur_threshold:
        issues.append(f"Blurry image (score={blur_score:.1f}, threshold={blur_threshold})")
    if luminance["mean"] < lum_min:
        issues.append(f"Too dark (mean luminance={luminance['mean']:.1f})")
    if luminance["mean"] > lum_max:
        issues.append(f"Overexposed (mean luminance={luminance['mean']:.1f})")

    quality = "PASS" if not issues else "FAIL"

    return {
        "quality": quality,
        "blur_score": round(blur_score, 2),
        "blur_threshold": blur_threshold,
        "luminance": {k: round(v, 2) for k, v in luminance.items()},
        "issues": issues,
        "summary": f"Image quality: {quality}. {len(issues)} issue(s) found."
        if issues
        else "Image quality: PASS. No issues detected.",
    }
