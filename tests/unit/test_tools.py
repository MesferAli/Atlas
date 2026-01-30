"""Unit tests for Atlas tools — image audit and annotation verification."""

import json

import numpy as np
import pytest

from atlas.tools.image_audit import audit_image_quality
from atlas.tools.annotation_verify import verify_annotations


class TestAuditImageQuality:
    """Tests for the image quality audit tool."""

    def test_sharp_image(self):
        """A noisy image should have high blur score (PASS)."""
        rng = np.random.RandomState(42)
        image = rng.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        result = audit_image_quality(image)
        assert result["quality"] == "PASS"
        assert result["blur_score"] > 0

    def test_blurry_image(self):
        """A uniform image should have low blur score (FAIL)."""
        image = np.full((100, 100, 3), 128, dtype=np.uint8)
        result = audit_image_quality(image)
        assert result["quality"] == "FAIL"
        assert any("Blurry" in i for i in result["issues"])

    def test_dark_image(self):
        """An all-black image should flag as too dark."""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        result = audit_image_quality(image)
        assert any("dark" in i.lower() for i in result["issues"])

    def test_overexposed_image(self):
        """An all-white image should flag as overexposed."""
        image = np.full((100, 100, 3), 255, dtype=np.uint8)
        result = audit_image_quality(image)
        assert any("overexposed" in i.lower() or "Overexposed" in i for i in result["issues"])

    def test_mzx_signed(self):
        """Result should contain MZX signature."""
        image = np.full((50, 50, 3), 128, dtype=np.uint8)
        result = audit_image_quality(image)
        assert "mzx_id" in result
        assert result["mzx_id"].startswith("MZX-")

    def test_grayscale_input(self):
        """Should handle grayscale (2D) arrays."""
        rng = np.random.RandomState(42)
        image = rng.randint(0, 256, (100, 100), dtype=np.uint8)
        result = audit_image_quality(image)
        assert "blur_score" in result


class TestVerifyAnnotations:
    """Tests for the annotation verification tool."""

    def test_valid_annotations(self):
        annotations = [
            {"id": 1, "label": "car", "bbox": [10, 10, 50, 50]},
            {"id": 2, "label": "tree", "bbox": [100, 100, 150, 150]},
        ]
        result = verify_annotations(annotations)
        assert result["quality"] == "PASS"
        assert result["total_annotations"] == 2

    def test_missing_label(self):
        annotations = [
            {"id": 1, "label": "", "bbox": [10, 10, 50, 50]},
        ]
        result = verify_annotations(annotations)
        assert result["quality"] == "FAIL"
        assert result["missing_labels"] == 1

    def test_missing_bbox(self):
        annotations = [
            {"id": 1, "label": "car"},
        ]
        result = verify_annotations(annotations)
        assert result["quality"] == "FAIL"
        assert result["missing_bboxes"] == 1

    def test_overlapping_boxes(self):
        annotations = [
            {"id": 1, "label": "car", "bbox": [10, 10, 50, 50]},
            {"id": 2, "label": "truck", "bbox": [10, 10, 50, 50]},  # exact overlap
        ]
        result = verify_annotations(annotations)
        assert result["quality"] == "FAIL"
        assert result["overlapping_pairs"] == 1

    def test_tiny_region(self):
        annotations = [
            {"id": 1, "label": "dot", "bbox": [10, 10, 11, 11]},  # area = 1
        ]
        result = verify_annotations(annotations)
        assert result["quality"] == "FAIL"
        assert result["tiny_regions"] == 1

    def test_json_string_input(self):
        data = json.dumps([
            {"id": 1, "label": "car", "bbox": [10, 10, 100, 100]},
        ])
        result = verify_annotations(data)
        assert result["quality"] == "PASS"

    def test_invalid_json(self):
        result = verify_annotations("not json")
        assert "error" in result

    def test_mzx_signed(self):
        result = verify_annotations([
            {"id": 1, "label": "car", "bbox": [10, 10, 50, 50]},
        ])
        assert "mzx_id" in result
        assert result["mzx_id"].startswith("MZX-")

    def test_no_overlap_non_intersecting(self):
        annotations = [
            {"id": 1, "label": "a", "bbox": [0, 0, 10, 10]},
            {"id": 2, "label": "b", "bbox": [50, 50, 60, 60]},
        ]
        result = verify_annotations(annotations)
        assert result["overlapping_pairs"] == 0
