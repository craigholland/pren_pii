# File: pii/common/tests/test_dateparser.py

import pytest
from datetime import datetime, date, timezone
from zoneinfo import ZoneInfo
from google.protobuf.timestamp_pb2 import Timestamp
from google.type.date_pb2 import Date as GoogleDate
from google.type.datetime_pb2 import DateTime as GoogleDateTime

from pii.common.utils.dateparser import DateParser, DateParseError


def test_parse_none():
    dp = DateParser(None)
    assert dp.datetime is None
    assert dp.date is None
    assert dp.timestamp is None


def test_parse_int_timestamp():
    # 2021-01-01T00:00:00Z
    ts = 1609459200
    dp = DateParser(ts)
    expected = datetime(2021, 1, 1, tzinfo=ZoneInfo("UTC"))
    assert dp.datetime == expected
    assert dp.timestamp == ts


def test_parse_iso_string_with_tz():
    dp = DateParser("2021-06-15T12:34:56+02:00")
    # Converted to UTC
    assert dp.datetime == datetime(2021, 6, 15, 10, 34, 56, tzinfo=ZoneInfo("UTC"))


def test_parse_iso_string_without_tz():
    dp = DateParser("2021-06-15 12:34:56")
    assert dp.datetime == datetime(2021, 6, 15, 12, 34, 56, tzinfo=ZoneInfo("UTC"))


def test_parse_datetime_aware_and_naive():
    aware = datetime(2022, 3, 10, 8, 0, 0, tzinfo=ZoneInfo("UTC"))
    dp_aware = DateParser(aware)
    assert dp_aware.datetime == aware

    naive = datetime(2022, 3, 10, 8, 0, 0)
    dp_naive = DateParser(naive)
    assert dp_naive.datetime == aware

    # datetime_naive strips tzinfo
    assert dp_aware.datetime_naive == datetime(2022, 3, 10, 8, 0, 0)


def test_parse_date():
    d = date(2020, 12, 31)
    dp = DateParser(d)
    assert dp.datetime == datetime(2020, 12, 31, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
    assert dp.date == d


def test_parse_proto_timestamp_and_dict():
    # Create a protobuf Timestamp
    ts_proto = Timestamp()
    ts_proto.FromDatetime(datetime(2019, 7, 4, 17, 0, 0, tzinfo=ZoneInfo("UTC")))
    dp1 = DateParser(ts_proto)
    assert dp1.datetime == datetime(2019, 7, 4, 17, 0, 0, tzinfo=ZoneInfo("UTC"))

    # As dict
    dp2 = DateParser({"seconds": ts_proto.seconds, "nanos": ts_proto.nanos})
    assert dp2.datetime == dp1.datetime


def test_parse_google_date_and_datetime_and_dict():
    gd = GoogleDate(year=2023, month=5, day=20)
    dp_date = DateParser(gd)
    assert dp_date.datetime == datetime(2023, 5, 20, 0, 0, 0, tzinfo=ZoneInfo("UTC"))

    gdt = GoogleDateTime(year=2023, month=5, day=20, hours=14, minutes=30, seconds=15, nanos=500_000_000)
    dp_dt = DateParser(gdt)
    assert dp_dt.datetime == datetime(2023, 5, 20, 14, 30, 15, 500_000, tzinfo=ZoneInfo("UTC"))

    # As dict for GoogleDate
    dp_date2 = DateParser({"year": 2023, "month": 5, "day": 20})
    assert dp_date2.datetime == dp_date.datetime

    # As dict for GoogleDateTime
    dp_dt2 = DateParser({
        "year": 2023, "month": 5, "day": 20,
        "hours": 14, "minutes": 30, "seconds": 15, "nanos": 500_000_000
    })
    assert dp_dt2.datetime == dp_dt.datetime


def test_output_properties_and_format():
    dp = DateParser("2022-10-05T09:15:00Z")
    # isoformat
    assert dp.isoformat == "2022-10-05T09:15:00+00:00"
    # custom format
    assert dp.format("%Y/%m/%d %H:%M") == "2022/10/05 09:15"
    # to_proto_timestamp
    ts = dp.to_proto_timestamp()
    assert isinstance(ts, Timestamp)
    assert ts.seconds == 1664961300
    # to_proto_date
    gd = dp.to_proto_date()
    assert isinstance(gd, GoogleDate)
    assert (gd.year, gd.month, gd.day) == (2022, 10, 5)


def test_time_property():
    dp = DateParser("2022-11-11T23:59:59Z")
    assert dp.time.hour == 23
    assert dp.time.minute == 59
    assert dp.time.second == 59


def test_unsupported_type_raises():
    with pytest.raises(DateParseError):
        DateParser([1, 2, 3])
