#!/usr/bin/env python3
"""Apply the pinned batch 0008 ARF system-table boundary audit."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


BASE_TOOL = Path(__file__).with_name("apply_boundary_audit.py")
spec = importlib.util.spec_from_file_location("arf_apply_boundary_base_0008", BASE_TOOL)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {BASE_TOOL}")
tool = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tool
spec.loader.exec_module(tool)

tool.AUDIT_PATH = tool.ROOT / "work/translation/boundary_audit/batch_0008.json"
tool.EXPECTED_AUDIT_SHA256 = (
    "19CEF06A3A04E3E74F6023D3C0D1528D7A6F916B7FB36C0C3BD6F7E1B4C7B511"
)
tool.APPLICATION_PATH = (
    tool.ROOT / "work/translation/boundary_audit/application_report_0008.json"
)
tool.BATCHES = ("batch_0008",)
tool.EXPECTED_AUDITED_UNITS = 34
tool.TRANSLATION_OVERRIDES = {}


if __name__ == "__main__":
    raise SystemExit(tool.main())
