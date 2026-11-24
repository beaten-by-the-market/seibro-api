from unittest.mock import Mock

import pandas as pd

from seibro_api import get_shareholder_meetings


def test_record_date_windows_omit_non_meetings_and_query_each_meeting_date_once():
    client = Mock()
    client.get_issuco_custno.return_value = {"issuco_custno": "12"}
    client.get_rights_record_dates.side_effect = [
        pd.DataFrame([
            {"RGT_STD_DT": "20221231", "RGT_RACD": "001", "RGT_RACD_NM": "정기총회"},
            {"RGT_STD_DT": "20221231", "RGT_RACD": "002", "RGT_RACD_NM": "임시총회"},
            {"RGT_STD_DT": "20230228", "RGT_RACD": "009", "RGT_RACD_NM": "기타"},
        ]),
        pd.DataFrame([
            {"RGT_STD_DT": "20231231", "RGT_RACD": "001", "RGT_RACD_NM": "정기총회"},
        ]),
    ]
    client.get_meeting_details.return_value = pd.DataFrame([{"ISSUIN_NO": "1"}])
    client.get_meeting_agendas.return_value = pd.DataFrame([{"AGENDA_NO": "1"}])

    result = get_shareholder_meetings("005930", "2020-12-31", "20231231", client=client)

    assert [call.args for call in client.get_rights_record_dates.call_args_list] == [
        ("12", "20201231", "20231230"), ("12", "20231231", "20231231"),
    ]
    assert [call.args for call in client.get_meeting_details.call_args_list] == [
        ("12", "20221231"), ("12", "20231231"),
    ]
    assert client.get_meeting_agendas.call_args_list == client.get_meeting_details.call_args_list
    assert len(result["record_dates"]) == 3
    assert len(result["meetings"]) == len(result["agendas"]) == 2
