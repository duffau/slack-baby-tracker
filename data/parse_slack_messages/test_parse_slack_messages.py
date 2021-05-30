from pytest_cases import parametrize_with_cases

import data.parse_slack_messages as psm
from datetime import datetime


def test_split_messages():
    txt = '''

ph  16:29
Amme: 13:?-14:45

ph  16:48
Sov: 14:45-16:45

duffau  19:41
Amme start: 19:40
'''
    
    messages = psm.split_messages(txt, psm.USERNAMES)
    for msg in messages:
        print("Meesage:")
        print(msg)
    assert len(messages) == 3
    assert messages[0].startswith("ph  16:29")
    assert messages[1].startswith("ph  16:48")
    assert messages[2].startswith("duffau  19:41")

def test_infer_timestamps_same_day():
    messages = [
        "ph  16:48\nSov: 14:45-16:45",
        "duffau  19:41\nAmme start: 19:40"
    ]
    timestamps = psm.infer_timestamps(messages, 
    psm.FIRST_MESSAGE_DATE, psm.USERNAMES)
    expected_timestamps = [datetime(2021, 5, 19, 16, 48), datetime(2021, 5, 19, 19, 41)]
    assert timestamps == expected_timestamps

def test_infer_timestamps_overnight():
    messages = [
        "ph  22:01\nHello",
        "ph  23:48\nSov: 23:45-02:45",
        "duffau  02:54\nAmme start: 02:51",
        "ph  03:04\nAWhat ever"
    ]
    timestamps = psm.infer_timestamps(messages, 
    psm.FIRST_MESSAGE_DATE, psm.USERNAMES)
    expected_timestamps = [
        datetime(2021, 5, 19, 22, 1), 
        datetime(2021, 5, 19, 23, 48), 
        datetime(2021, 5, 20, 2, 54),
        datetime(2021, 5, 20, 3, 4)
    ]
    print(timestamps)
    assert timestamps == expected_timestamps



class MessageTextFeedRecords:
    def case_single_feed_record_dot_sep(self):
        message_text = """
        Jiberish: 21.53-22.20
        Amme: 21.53-22.20
        Some other Jiberish: 21.53-22.20
        """
        expected_records = ["Amme: 21.53-22.20"] 
        return message_text, expected_records

    def case_single_feed_record_dot_sep_no_space(self):
        message_text = """
        Jiberish: 21.53-22.20
        F:21.53-22.20
        Some other Jiberish: 21.53-22.20
        """
        expected_records = ["F:21.53-22.20"] 
        return message_text, expected_records

    def case_single_feed_record_colon_sep(self):
        message_text = """
        Jiberish: 21.53-22:20
        Amme: 21:53-22:20
        Some other Jiberish: 21:53-22:20
        """
        expected_records = ["Amme: 21:53-22:20"] 
        return message_text, expected_records

    def case_multiple_feed_records_dot_sep(self):
        message_text = """
        Jiberish: 21.53-22.20
        Amme: 21.53-22.20
        Some other Jiberish: 21.53-22.20
        F: 2.53-3.45
        N: 2:53-3:45
        """
        expected_records = ["Amme: 21.53-22.20", "F: 2.53-3.45", "N: 2:53-3:45"] 
        return message_text, expected_records

    def case_feed_records_question_mark_time(self):
        message_text = """
N: 22:.19/?
22:56
N: 22.32-?
22:56
N: 22:48-2254
22:59
S: 22:59
"""
        expected_records = ["N: 22.32-?", "N: 22:48-2254"] 
        return message_text, expected_records


@parametrize_with_cases("message_text,expected_records", cases=MessageTextFeedRecords)
def test_find_feed_recordings(message_text, expected_records):
    record_strings = psm.extract_feed_recordings(message_text)
    for s in record_strings:
        print(s)
    assert record_strings == expected_records

class MessageTextSleepRecords:
    def case_single_simple_sleep_record_1(self):
        message_text = "Sov: 05:17-06:34"
        expected_records = ["Sov: 05:17-06:34"] 
        return message_text, expected_records

    def case_single_simple_sleep_record_2(self):
        message_text = "S: 05:17-06:34"
        expected_records = ["S: 05:17-06:34"] 
        return message_text, expected_records

    def case_single_sleep_record_no_end_time(self):
        message_text = "Sov: 05:17"
        expected_records = ["Sov: 05:17"] 
        return message_text, expected_records

@parametrize_with_cases("message_text,expected_records", cases=MessageTextSleepRecords)
def test_find_sleep_recordings(message_text, expected_records):
    record_strings = psm.extract_sleep_recordings(message_text)
    for s in record_strings:
        print(s)
    assert record_strings == expected_records
