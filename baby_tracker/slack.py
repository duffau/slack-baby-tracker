from prettytable import PrettyTable, NONE


def table(rows, colnames):
    t = PrettyTable()
    t.border = False
    t.hrules = NONE
    t.vrules = NONE
    t.field_names = colnames
    for row in rows:
        t.add_row(row)
    table_str = f"```{t.get_string()}```"
    return table_str


def error_message(e: Exception):
    exception_desc = repr(e)
    return f':exclamation: Failed with error: "{exception_desc}"'


def response(mrk_down_message, response_type="in_channel"):
    return {"response_type": response_type, "text": mrk_down_message}
