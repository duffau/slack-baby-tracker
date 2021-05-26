from baby_tracker import slack


def test_table():
    rows = [
        ("Abc", 123, 3.14),
        ("Def", 123, 3.14),

    ]
    table_str = slack.table(rows, ["Name", "Numeric value", "Other numeric value"])
    print(table_str)