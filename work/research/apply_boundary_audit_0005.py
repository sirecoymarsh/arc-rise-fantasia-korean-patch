#!/usr/bin/env python3
"""Apply the pinned batch 0005 ARF system-table boundary audit."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


BASE_TOOL = Path(__file__).with_name("apply_boundary_audit.py")
spec = importlib.util.spec_from_file_location("arf_apply_boundary_base_0005", BASE_TOOL)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {BASE_TOOL}")
tool = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tool
spec.loader.exec_module(tool)

tool.AUDIT_PATH = tool.ROOT / "work/translation/boundary_audit/batch_0005.json"
tool.EXPECTED_AUDIT_SHA256 = (
    "4776B6BB8042A707C9A2E3ADDEE08520396BF52B54E88ED0D72989936BA7339E"
)
tool.APPLICATION_PATH = (
    tool.ROOT / "work/translation/boundary_audit/application_report_0005.json"
)
tool.BATCHES = ("batch_0005",)
tool.EXPECTED_AUDITED_UNITS = 28
tool.TRANSLATION_OVERRIDES = {}


if __name__ == "__main__":
    raise SystemExit(tool.main())
