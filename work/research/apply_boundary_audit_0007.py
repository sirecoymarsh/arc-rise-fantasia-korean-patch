#!/usr/bin/env python3
"""Apply the pinned batch 0007 ARF system-table boundary audit."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


BASE_TOOL = Path(__file__).with_name("apply_boundary_audit.py")
spec = importlib.util.spec_from_file_location("arf_apply_boundary_base_0007", BASE_TOOL)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {BASE_TOOL}")
tool = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tool
spec.loader.exec_module(tool)

tool.AUDIT_PATH = tool.ROOT / "work/translation/boundary_audit/batch_0007.json"
tool.EXPECTED_AUDIT_SHA256 = (
    "8A04559A15EFAC784BACDA52E2B68B3AE94B0C157BB956AD731D3D3DF502DD42"
)
tool.APPLICATION_PATH = (
    tool.ROOT / "work/translation/boundary_audit/application_report_0007.json"
)
tool.BATCHES = ("batch_0007",)
tool.EXPECTED_AUDITED_UNITS = 29
tool.TRANSLATION_OVERRIDES = {}


if __name__ == "__main__":
    raise SystemExit(tool.main())
