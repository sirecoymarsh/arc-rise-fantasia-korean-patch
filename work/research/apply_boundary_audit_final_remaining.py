#!/usr/bin/env python3
"""Apply the pinned final 418-unit ARF system-table boundary audit."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


BASE_TOOL = Path(__file__).with_name("apply_boundary_audit.py")
spec = importlib.util.spec_from_file_location(
    "arf_apply_boundary_base_final_remaining", BASE_TOOL
)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {BASE_TOOL}")
tool = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tool
spec.loader.exec_module(tool)

tool.AUDIT_PATH = (
    tool.ROOT / "work/translation/boundary_audit/final_remaining_system.json"
)
tool.EXPECTED_AUDIT_SHA256 = (
    "32BBCE13CFE1756FE0AF572228F75EFF946007CFB19CD0F9273E5BF18529A1A5"
)
tool.APPLICATION_PATH = (
    tool.ROOT
    / "work/translation/boundary_audit/application_report_final_remaining.json"
)
tool.BATCHES = (
    "batch_0009",
    "batch_0010",
    "batch_0012",
    "batch_0013",
    "batch_0014",
    "batch_0015",
    "batch_0016",
    "batch_0017",
    "batch_0018",
    "batch_0019",
    "batch_0020",
    "batch_0021",
    "batch_0022",
)
tool.EXPECTED_AUDITED_UNITS = 418
tool.TRANSLATION_OVERRIDES = {}


if __name__ == "__main__":
    raise SystemExit(tool.main())
