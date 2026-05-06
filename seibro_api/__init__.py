from .client import SeibroClient
from .corp_loader import load_corps
from .stock_bond import get_stock_bonds, get_dart_cb_events
from .stock_issue import get_stock_issue_details
from .dart_report import get_sub_pis, get_cb_from_report, get_bw_from_report, get_eb_from_report, get_bonds_from_report
from .display import display_bond_summary

__all__ = [
    "SeibroClient", "load_corps",
    "get_stock_bonds", "get_dart_cb_events",
    "get_stock_issue_details",
    "get_schedule_reason_details",
    "get_bonus_issue_details",
    "get_sub_pis", "get_cb_from_report", "get_bw_from_report", "get_eb_from_report",
    "get_bonds_from_report",
]


def __getattr__(name):
    if name == "get_schedule_reason_details":
        from .schedule_reason import get_schedule_reason_details

        return get_schedule_reason_details
    if name == "get_bonus_issue_details":
        from .schedule_reason import get_bonus_issue_details

        return get_bonus_issue_details
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
