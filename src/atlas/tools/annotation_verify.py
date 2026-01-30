"""Annotation Verification Tool — Check for overlapping or missing labels.

MZX-signed tool for verifying annotation quality in datasets.
Detects overlapping bounding boxes and missing/empty labels.
"""

from __future__ import annotations

from typing import Any

from atlas.agents.atlas_agent import register_tool
from atlas.core.config import get_config
from atlas.core.mzx_protocol import mzx_signed


def _compute_iou(box_a: list[float], box_b: list[float]) -> float:
    """Compute Intersection over Union between two bounding boxes.

    Each box is [x_min, y_min, x_max, y_max].
    """
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])

    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    if intersection == 0:
        return 0.0

    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    union = area_a + area_b - intersection

    return intersection / union if union > 0 else 0.0


def _box_area(box: list[float]) -> float:
    """Compute the area of a bounding box [x_min, y_min, x_max, y_max]."""
    return max(0, box[2] - box[0]) * max(0, box[3] - box[1])


@register_tool(
    "verify_annotations",
    description="Check for overlapping or missing labels in annotation data",
    is_async=False,
)
@mzx_signed
def verify_annotations(annotations: str | list[dict[str, Any]]) -> dict[str, Any]:
    """Verify annotation quality: overlapping boxes, missing labels, tiny regions.

    Args:
        annotations: Either a JSON string or a list of annotation dicts.
            Each annotation should have:
            - "bbox": [x_min, y_min, x_max, y_max]
            - "label": str (class label)
            Optional:
            - "id": str/int identifier

    Returns:
        Dict with verification results, issues, and summary.
    """
    import json

    cfg = get_config()
    tool_cfg = cfg.tools.get("verify_annotations")
    iou_threshold = tool_cfg.overlap_iou_threshold if tool_cfg else 0.5
    min_area = tool_cfg.min_area if tool_cfg else 10

    # Parse if string
    if isinstance(annotations, str):
        try:
            annotations = json.loads(annotations)
        except json.JSONDecodeError:
            return {
                "error": "Invalid JSON input",
                "summary": "Cannot verify: invalid annotation format",
            }

    if not isinstance(annotations, list):
        return {
            "error": "Annotations must be a list of dicts",
            "summary": "Cannot verify: unexpected input type",
        }

    total = len(annotations)
    issues: list[dict[str, Any]] = []

    # Check for missing labels
    for i, ann in enumerate(annotations):
        ann_id = ann.get("id", i)
        label = ann.get("label", "")
        bbox = ann.get("bbox")

        if not label or not label.strip():
            issues.append({
                "type": "missing_label",
                "annotation_id": ann_id,
                "detail": "Annotation has no label",
            })

        if bbox is None:
            issues.append({
                "type": "missing_bbox",
                "annotation_id": ann_id,
                "detail": "Annotation has no bounding box",
            })
            continue

        if len(bbox) != 4:
            issues.append({
                "type": "invalid_bbox",
                "annotation_id": ann_id,
                "detail": f"Bounding box has {len(bbox)} values (expected 4)",
            })
            continue

        area = _box_area(bbox)
        if area < min_area:
            issues.append({
                "type": "tiny_region",
                "annotation_id": ann_id,
                "detail": f"Bounding box area={area:.1f} < min_area={min_area}",
            })

    # Check for overlapping boxes
    valid_anns = [
        (i, ann)
        for i, ann in enumerate(annotations)
        if ann.get("bbox") and len(ann.get("bbox", [])) == 4
    ]

    overlaps: list[dict[str, Any]] = []
    for idx_a in range(len(valid_anns)):
        for idx_b in range(idx_a + 1, len(valid_anns)):
            i, ann_a = valid_anns[idx_a]
            j, ann_b = valid_anns[idx_b]
            iou = _compute_iou(ann_a["bbox"], ann_b["bbox"])
            if iou >= iou_threshold:
                overlaps.append({
                    "type": "overlap",
                    "annotation_ids": [ann_a.get("id", i), ann_b.get("id", j)],
                    "iou": round(iou, 3),
                    "detail": f"IoU={iou:.3f} >= threshold={iou_threshold}",
                })

    all_issues = issues + overlaps
    quality = "PASS" if not all_issues else "FAIL"

    return {
        "quality": quality,
        "total_annotations": total,
        "missing_labels": len([i for i in issues if i["type"] == "missing_label"]),
        "missing_bboxes": len([i for i in issues if i["type"] == "missing_bbox"]),
        "tiny_regions": len([i for i in issues if i["type"] == "tiny_region"]),
        "overlapping_pairs": len(overlaps),
        "issues": all_issues,
        "iou_threshold": iou_threshold,
        "min_area": min_area,
        "summary": (
            f"Annotations: {quality}. {len(all_issues)} issue(s) across {total} annotations."
            if all_issues
            else f"Annotations: PASS. All {total} annotations are valid."
        ),
    }
