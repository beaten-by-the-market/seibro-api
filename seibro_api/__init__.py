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
    "get_dividend_schedule_details",
    "get_face_value_split_details",
    "get_face_value_merge_details",
    "get_capital_reduction_details",
    "get_company_schedules",
    "get_cost_payment_schedules",
    "get_dividend_details",
    "get_issued_share_changes",
    "get_overseas_settlement_amounts",
    "get_overseas_holdings",
    "get_kofr_rates",
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
    if name == "get_dividend_schedule_details":
        from .schedule_reason import get_dividend_schedule_details

        return get_dividend_schedule_details
    if name == "get_face_value_split_details":
        from .schedule_reason import get_face_value_split_details

        return get_face_value_split_details
    if name == "get_face_value_merge_details":
        from .schedule_reason import get_face_value_merge_details

        return get_face_value_merge_details
    if name == "get_capital_reduction_details":
        from .schedule_reason import get_capital_reduction_details

        return get_capital_reduction_details
    if name == "get_company_schedules":
        from .schedule_reason import get_company_schedules

        return get_company_schedules
    if name == "get_cost_payment_schedules":
        from .schedule_reason import get_cost_payment_schedules

        return get_cost_payment_schedules
    if name == "get_dividend_details":
        from .dividend import get_dividend_details

        return get_dividend_details
    if name == "get_issued_share_changes":
        from .issued_share_change import get_issued_share_changes

        return get_issued_share_changes
    if name == "get_overseas_settlement_amounts":
        from .overseas_securities import get_overseas_settlement_amounts

        return get_overseas_settlement_amounts
    if name == "get_overseas_holdings":
        from .overseas_securities import get_overseas_holdings

        return get_overseas_holdings
    if name == "get_kofr_rates":
        from .kofr import get_kofr_rates

        return get_kofr_rates
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
