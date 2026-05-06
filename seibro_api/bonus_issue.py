"""Backward-compatible entry point for bonus issue schedule details."""

from __future__ import annotations

from .schedule_reason import get_bonus_issue_details


if __name__ == "__main__":
    import sys

    code = sys.argv[1] if len(sys.argv) > 1 else "000100"
    start_arg = sys.argv[2] if len(sys.argv) > 2 else "20110101"
    end_arg = sys.argv[3] if len(sys.argv) > 3 else None
    df_result = get_bonus_issue_details(code, start_arg, end_arg)
    if not df_result.empty:
        print(df_result.to_string(index=False))
