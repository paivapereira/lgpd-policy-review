"""Phase 0 anchors — Detector output contract (detector.md §3.1, §3.2).

strip-opinion / keep-provenance (DD-D1): DetectorFinding has exactly the 5
fields, NO rule_severity / rule_message. Provenance is per-envelope, not
per-finding (DD-D3).
"""
from __future__ import annotations

from subagents.detector.models import (
    DetectorFinding,
    DetectorOutput,
    ScanMetadata,
    ScanProvenance,
)


def test_detector_finding_exactly_five_fields_no_opinion() -> None:
    schema = DetectorFinding.model_json_schema()
    props = set(schema["properties"])
    assert props == {"file", "line", "rule_id", "snippet", "surrounding_context"}
    assert "rule_severity" not in props  # opinion stripped (DD-D1)
    assert "rule_message" not in props
    assert schema.get("additionalProperties") is False


def test_detector_output_provenance_is_per_envelope() -> None:
    schema = DetectorOutput.model_json_schema()
    assert set(schema["properties"]) == {"findings", "provenance"}
    assert schema["properties"]["findings"]["type"] == "array"
    # provenance is NOT a per-finding field
    assert "provenance" not in DetectorFinding.model_json_schema()["properties"]


def test_scan_provenance_three_keys() -> None:
    sp = ScanProvenance.model_json_schema()
    assert set(sp["properties"]) == {"rules_version", "semgrep_version", "scan_metadata"}


def test_detector_output_accepts_empty_findings() -> None:
    out = DetectorOutput(
        findings=[],
        provenance=ScanProvenance(
            rules_version="2026.04.1",
            semgrep_version="1.163.0",
            scan_metadata=ScanMetadata(
                base_ref="a" * 40,
                head_ref="b" * 40,
                files_scanned=0,
                elapsed_seconds=0.0,
            ),
        ),
    )
    assert out.findings == []
    assert out.provenance.scan_metadata.files_scanned == 0
