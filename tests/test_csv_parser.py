from parsers.csv_log import parse_csv

def test_csv_extra_columns_are_preserved():
    assert parse_csv("a,b\n1,2,3")["col_2"] == "3"
