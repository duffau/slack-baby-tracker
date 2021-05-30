import re
import csv
import itertools
from datetime import datetime, date, time, timedelta
import dateparser as dp
import zlib
from copy import copy, deepcopy
import pickle


FIRST_MESSAGE_DATE = "2021-05-19"
USERNAMES = ["ph", "duffau"]
FEED_PREFIX_PATTERNS = [r"Amme:\s*", r"Amme v:\s*", r"F:\s*", r"N:\s*"] 
SLEEP_PREFIX_PATTERNS = [r"Sov:\s*", r"S:\s*", r"Lagt i lift:\s*e"]
SKIP_EDIT = False


def split_messages(txt, usernames):
    split_pattern = r"\n\n" + "(" + "|".join([f"{name}  \\d{{2}}:\\d{{2}}" for name in usernames])  + ")"
    print("split_pattern:", split_pattern)
    splits =  re.split(split_pattern, txt)
    if splits[0] == "":
        splits.pop(0)
    return [s1+s2 for s1,s2 in zip(splits[0::2], splits[1::2])]

def infer_timestamps(messages, start_date, usernames):
    timestamps = []
    current_date = date.fromisoformat(start_date)
    prev_timestamp = datetime(1,1,1,0,0,0,0)
    for i, msg in enumerate(messages):
        clock = extract_clock(msg, usernames)
        if clock >= prev_timestamp.time():
            timestamp = datetime.combine(current_date, clock)
        else:
            current_date += timedelta(days=1)
            timestamp = datetime.combine(current_date, clock)
        timestamps.append(timestamp)
        prev_timestamp = timestamp
    return timestamps


def extract_clock(message_text, usernames):
    clock_matches = re.search(f"({'|'.join(usernames)})  (\\d{{2}}:\\d{{2}})", message_text)
    clock = clock_matches.group(2)
    clock = time.fromisoformat(clock)
    return clock

def extract_feed_recordings(message_text):
    prefix_patterns = FEED_PREFIX_PATTERNS
    hour_minute_sep_patterns = [r":", r"\."]
    hour_minute_patterns = [r"\d{1,2}", r"\?"]
    clock_patterns = itertools.product(hour_minute_patterns, hour_minute_sep_patterns, hour_minute_patterns) 
    clock_patterns = ["".join([h,s,m]) for h,s,m in clock_patterns]
    clock_patterns += [r"\?", r"\d{4}"]
    sep_pattern = [r"-"]
    patterns = itertools.product(prefix_patterns, clock_patterns, sep_pattern, clock_patterns)
    patterns = ["".join([pre, clock1, sep, clock2]) for pre, clock1, sep, clock2 in patterns]
    pattern = "|".join(patterns)
    matches = re.findall(pattern, message_text)
    return matches


def extract_sleep_recordings(message_text):
    prefix_patterns = SLEEP_PREFIX_PATTERNS 
    hour_minute_sep_patterns = [r":", r"\."]
    hour_minute_patterns = [r"\d{1,2}", r"\?", r""]
    start_clock_patterns = itertools.product(hour_minute_patterns, hour_minute_sep_patterns, hour_minute_patterns) 
    start_clock_patterns = ["".join([h,s,m]) for h,s,m in start_clock_patterns]
    start_clock_patterns += [r"\?", r"\d{4}"]
    end_clock_patterns = [p for p in start_clock_patterns] + [r""]
    sep_pattern = [r"-", r"\s*", r""]
    patterns = itertools.product(prefix_patterns, start_clock_patterns, sep_pattern, end_clock_patterns)
    patterns = ["".join([pre, clock1, sep, clock2]) for pre, clock1, sep, clock2 in patterns]
    pattern = "|".join(patterns)
    matches = re.findall(pattern, message_text)
    return matches

def parse_feed_record(message_timestamp, feed_record_txt):
    created_at = message_timestamp
    from_time_time, to_time_time = feed_from_and_to_time(feed_record_txt)
    if from_time_time is not None:
        if (to_time_time is not None) and (from_time_time > to_time_time):
            from_time_date = created_at.date() - timedelta(days=1)
        else:
            from_time_date = created_at.date()
        from_time = datetime.combine(from_time_date, from_time_time)
    else:
        from_time = None

    if to_time_time is not None:
        to_time_date = created_at.date()
        to_time = datetime.combine(to_time_date, to_time_time)
    else:
        to_time = None
    return (from_time, to_time, created_at)

def parse_sleep_record(message_timestamp, sleep_record_txt):
    created_at = message_timestamp
    from_time_time, to_time_time = sleep_from_and_to_time(sleep_record_txt)
    if from_time_time is not None:
        if (to_time_time is not None) and (from_time_time > to_time_time):
            from_time_date = created_at.date() - timedelta(days=1)
        else:
            from_time_date = created_at.date()
        from_time = datetime.combine(from_time_date, from_time_time)
    else:
        from_time = None

    if to_time_time is not None:
        to_time_date = created_at.date()
        to_time = datetime.combine(to_time_date, to_time_time)
    else:
        to_time = None
    return (from_time, to_time, created_at)

def feed_from_and_to_time(feed_record_txt):
    return _from_and_to_time(feed_record_txt, FEED_PREFIX_PATTERNS)

def sleep_from_and_to_time(feed_record_txt):
    return _from_and_to_time(feed_record_txt, SLEEP_PREFIX_PATTERNS)

def _from_and_to_time(feed_record_txt, prefix_patterns):
    prefix_pattern = "|".join(prefix_patterns)
    feed_record_txt = re.sub(prefix_pattern, "", feed_record_txt)
    feed_record_txt = feed_record_txt.strip()
    sep_patterns = [r"-"]
    sep_pattern = "|".join(sep_patterns)
    splits = re.split(sep_pattern, feed_record_txt)

    if len(splits) == 2:
        from_time, to_time = splits
    elif len(splits) == 1:
        from_time = splits[0]
        to_time = None
    else:
        from_time = None
        to_time = None

    if from_time:
        from_time = parse_time(from_time)
    if to_time:
        to_time = parse_time(to_time)
    return from_time, to_time

def parse_time(date_string):
    patterns = ["%H:%M", "%H.%M", "%H%M"]
    timestamp = None
    for pattern in patterns:
        if timestamp is None:
            try:
                timestamp = datetime.strptime(date_string, pattern)
            except ValueError:
                timestamp = None
    return timestamp.time() if timestamp else None


def print_message(timestamp, msg, prefix="Current"):
    print(f"\n--- {prefix} Message: {timestamp.isoformat()}")
    print(msg)


def csv_format_duration_record(row):
    datetime_fmt = "%Y-%m-%d %H:%M"
    return [t.strftime(datetime_fmt) if t else "NULL" for t in row]

def prompt(record):
    print("Parsed record:", format_record(record))
    action = input("Ok ?(yes/drop/edit/skip) y/d/e/s:")
    if action in {"y", "yes"}:
        return record
    if action in {"d", "drop"}:
        return None
    if action in {"s", "skip"}:
        return "skip"
    if action in {"e", "edit"}:
        print("Edit:", format_record(record))
        new_record = []
        for i, ts in enumerate(record):
            do_keep = input(f"Keep timestamp {i} {format_timestamp(ts)} (y/n):")
            if do_keep == "y":
                new_record.append(ts)
                continue
            elif do_keep == "n":
                new_timestamp = input(f"Input timestamp 'Y-m-d HH:MM':")
                try:
                    new_timestamp = datetime.strptime(new_timestamp.strip(), '%Y-%m-%d %H:%M')
                    new_record.append(new_timestamp)
                except Exception as e:
                    print(repr(e))
                    new_record.append(ts)
        return new_record

def format_record(record):
    _record = [format_timestamp(t) for t in record]
    return " ".join(_record)

def format_timestamp(ts):
    return ts.strftime("%Y-%m-%d %H:%M") if ts else "NULL"


def _checksum(text: str) -> str:
    checksum = zlib.adler32(text.encode())
    return f"0x{checksum:08X}"

def main():
    with open("slack-messages.txt") as txt_file:
        txt = txt_file.read()

    messages = split_messages(txt, USERNAMES)
    timestamps = infer_timestamps(messages, FIRST_MESSAGE_DATE, USERNAMES)
    global feed_csv
    feed_csv = []
    global sleep_csv
    sleep_csv = []

    try:
        with open("feed_edits.pickle", "rb") as feed_edits_file:
            global feed_edits 
            feed_edits = pickle.load(feed_edits_file)
    except FileNotFoundError:
        feed_edits = {} 

    try:
        with open("sleep_edits.pickle", "rb") as sleep_edits_file:
            global sleep_edits
            sleep_edits = pickle.load(sleep_edits_file)
    except FileNotFoundError:
        sleep_edits = {} 

    for i, (msg, timestamp) in enumerate(zip(messages, timestamps)):

        feed_records_texts = extract_feed_recordings(msg)
        for feed_record_txt in feed_records_texts:
            feed_record = parse_feed_record(timestamp, feed_record_txt)
            if None in feed_record:
                edit_id = _checksum(msg + feed_record_txt)
                updated_feed_record = feed_edits.get(edit_id)
                if not SKIP_EDIT:
                    if not updated_feed_record:
                        print()
                        print("-"*15)
                        print("None in Feed record")
                        print_message(timestamp, messages[i-1] if i>0 else None, "Previous")
                        print_message(timestamp, msg, "Current")
                        print_message(timestamp, messages[i+1] if i+1<len(messages) else None, "Next")
                        updated_feed_record = prompt(feed_record)
                        if updated_feed_record != "skip":
                            feed_edits[edit_id] = deepcopy(updated_feed_record)
                            feed_record = updated_feed_record
                    else:
                        feed_record = updated_feed_record
            feed_csv.append(csv_format_duration_record(feed_record))

        sleep_records_texts = extract_sleep_recordings(msg)
        for sleep_records_txt in sleep_records_texts:
            sleep_record = parse_sleep_record(timestamp, sleep_records_txt)
            if None in sleep_record:
                edit_id = _checksum(msg+sleep_records_txt)
                updated_sleep_record = sleep_edits.get(edit_id)
                if not SKIP_EDIT:
                    if not updated_sleep_record:
                        print()
                        print("-"*15)
                        print("None in Sleep record")
                        print_message(timestamp, messages[i-1] if i>0 else None, "Previous")
                        print_message(timestamp, msg, "Current")
                        print_message(timestamp, messages[i+1] if i+1<len(messages) else None, "Next")
                        updated_sleep_record = prompt(sleep_record)
                        if updated_sleep_record != "skip":
                            sleep_edits[edit_id] = deepcopy(updated_sleep_record)
                            sleep_record = updated_sleep_record
                    else:
                        sleep_record = updated_sleep_record
            sleep_csv.append(csv_format_duration_record(sleep_record))

    print(f"Found {len(timestamps)} timstamps")
    print(f"Found {len(messages)} messages.")
    print(f"First timestamp: {timestamps[0]}")
    print(f"Last timestamp: {timestamps[-1]}")
    print(f"Found {len(feed_csv)} breastfeeding records")
    print(f"Found {len(sleep_csv)} sleep records")

if __name__ == "__main__":
    import sys
    cmd_args = sys.argv
    cmd_flags = [arg for arg in cmd_args if arg.startswith("--")] 
    try:
        if "--skip" in set(cmd_flags):
            SKIP_EDIT = True
        main()
    finally:
        with open("../feed_slack_records.csv", "w") as feed_csv_file:
            feed_csv_writer = csv.writer(feed_csv_file)
            feed_csv_writer.writerow(["from_time","to_time","created_at"])
            feed_csv_writer.writerows(feed_csv)

        with open("../sleep_slack_records.csv", "w") as sleep_csv_file:
            sleep_csv_writer = csv.writer(sleep_csv_file)
            sleep_csv_writer.writerow(["from_time","to_time","created_at"])
            sleep_csv_writer.writerows(sleep_csv)

        with open("feed_edits.pickle", "wb") as feed_edits_file:
            pickle.dump(feed_edits, feed_edits_file)

        with open("sleep_edits.pickle", "wb") as sleep_edits_file:
            pickle.dump(sleep_edits, sleep_edits_file)   
