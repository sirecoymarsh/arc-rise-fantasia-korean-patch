#!/usr/bin/env python3
"""Apply the pinned batch 0003–0004 ARF system-table boundary audit."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


BASE_TOOL = Path(__file__).with_name("apply_boundary_audit.py")
spec = importlib.util.spec_from_file_location("arf_apply_boundary_base", BASE_TOOL)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {BASE_TOOL}")
tool = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tool
spec.loader.exec_module(tool)

tool.AUDIT_PATH = (
    tool.ROOT / "work/translation/boundary_audit/batches_0003_0004.json"
)
tool.EXPECTED_AUDIT_SHA256 = (
    "8500248960597E9A7A656F14FD07010A923C0B60544B1D1478E8B497900BDB5C"
)
tool.APPLICATION_PATH = (
    tool.ROOT / "work/translation/boundary_audit/application_report_0003_0004.json"
)
tool.BATCHES = ("batch_0003", "batch_0004")
tool.EXPECTED_AUDITED_UNITS = 80
tool.TRANSLATION_OVERRIDES = {}


if __name__ == "__main__":
    raise SystemExit(tool.main())
