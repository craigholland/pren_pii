# File: pii/common/utils/date_parser.py

from datetime import datetime, date
from dateutil import parser
from typing import Any, Optional, Union
from zoneinfo import ZoneInfo
from google.protobuf.timestamp_pb2 import Timestamp
from google.type.date_pb2 import Date as GoogleDate
from google.type.datetime_pb2 import DateTime as GoogleDateTime


class DateParseError(ValueError):
    """Raised when date parsing fails or input is unsupported."""


class DateParser:
    """Normalize various date/time inputs to UTC-aware datetime and expose common formats."""

    def __init__(self, date_input: Any):
        """
        Initialize parser with input and immediately parse to a UTC-aware datetime.

        :param date_input: Supported types:
            - None
            - int (Unix timestamp, seconds since epoch)
            - str (parsed by dateutil.parser)
            - datetime.date / datetime.datetime
            - google.protobuf.timestamp_pb2.Timestamp
            - google.type.Date, GoogleDateTime
            - dict (to reconstruct any of the above protos)
        """
        self._datetime: Optional[datetime] = self._parse_input(date_input)

    @staticmethod
    def _parse_input(date_input: Any) -> Optional[datetime]:
        """
        Parse supported inputs into a UTC-aware datetime.

        :raises DateParseError: on unsupported types or parse failures.
        """
        if date_input is None:
            return None

        try:
            # 1) Unix timestamp
            if isinstance(date_input, int):
                return datetime.fromtimestamp(date_input, tz=ZoneInfo("UTC"))

            # 2) ISO-ish string
            if isinstance(date_input, str):
                dt = parser.parse(date_input)
                if dt.tzinfo:
                    return dt.astimezone(ZoneInfo("UTC"))
                return dt.replace(tzinfo=ZoneInfo("UTC"))

            # 3) dict for proto types
            if isinstance(date_input, dict):
                # Distinguish Timestamp vs. Date/DateTime by keys
                if {"seconds", "nanos"} <= date_input.keys():
                    return DateParser._from_timestamp(Timestamp(**date_input))
                if {"year", "month", "day"} <= date_input.keys():
                    if {"hours", "minutes"}.intersection(date_input):
                        return DateParser._from_google_datetime(GoogleDateTime(**date_input))
                    return DateParser._from_google_date(GoogleDate(**date_input))
                raise DateParseError(f"Unsupported dict keys for date: {sorted(date_input.keys())}")

            # 4) Protobuf Timestamp
            if isinstance(date_input, Timestamp):
                return DateParser._from_timestamp(date_input)

            # 5) google.type.DateTime / Date
            if isinstance(date_input, GoogleDateTime):
                return DateParser._from_google_datetime(date_input)
            if isinstance(date_input, GoogleDate):
                return DateParser._from_google_date(date_input)

            # 6) native datetime
            if isinstance(date_input, datetime):
                if date_input.tzinfo:
                    return date_input.astimezone(ZoneInfo("UTC"))
                return date_input.replace(tzinfo=ZoneInfo("UTC"))

            # 7) native date
            if isinstance(date_input, date):
                dt = datetime.combine(date_input, datetime.min.time())
                return dt.replace(tzinfo=ZoneInfo("UTC"))

        except (parser.ParserError, ValueError, TypeError) as exc:
            raise DateParseError(f"Failed to parse {date_input!r}: {exc}") from exc

        raise DateParseError(f"Unsupported date format: {type(date_input)}")

    @staticmethod
    def _from_timestamp(ts: Timestamp) -> datetime:
        """Convert protobuf Timestamp to UTC-aware datetime."""
        return ts.ToDatetime(tzinfo=ZoneInfo("UTC"))

    @staticmethod
    def _from_google_date(gd: GoogleDate) -> datetime:
        """Convert google.type.Date to UTC-aware datetime at midnight."""
        return datetime(gd.year, gd.month, gd.day, tzinfo=ZoneInfo("UTC"))

    @staticmethod
    def _from_google_datetime(gd: GoogleDateTime) -> datetime:
        """Convert google.type.DateTime to UTC-aware datetime."""
        return gd.ToDatetime(tzinfo=ZoneInfo("UTC"))

    @property
    def datetime(self) -> Optional[datetime]:
        """Get the UTC-aware datetime (or None)."""
        return self._datetime

    @property
    def datetime_naive(self) -> Optional[datetime]:
        """Get a naive (tzinfo-free) UTC datetime (or None)."""
        return self._datetime.replace(tzinfo=None) if self._datetime else None

    @property
    def date(self) -> Optional[date]:
        """Get the date part in UTC (or None)."""
        return self._datetime.date() if self._datetime else None

    @property
    def time(self):
        """Get the time part (including tzinfo) (or None)."""
        return self._datetime.timetz() if self._datetime else None

    @property
    def timestamp(self) -> Optional[float]:
        """Get the Unix timestamp in seconds (or None)."""
        return self._datetime.timestamp() if self._datetime else None

    @property
    def isoformat(self) -> Optional[str]:
        """Get the ISO 8601 string representation (or None)."""
        return self._datetime.isoformat() if self._datetime else None

    def format(self, fmt: str) -> Optional[str]:
        """Format the datetime with a custom strftime pattern (or None)."""
        return self._datetime.strftime(fmt) if self._datetime else None

    def to_proto_timestamp(self) -> Optional[Timestamp]:
        """Get a google.protobuf.Timestamp representation (or None)."""
        if not self._datetime:
            return None
        ts = Timestamp()
        ts.FromDatetime(self._datetime)
        return ts

    def to_proto_date(self) -> Optional[GoogleDate]:
        """Get a google.type.Date representation (or None)."""
        if not self._datetime:
            return None
        return GoogleDate(
            year=self._datetime.year,
            month=self._datetime.month,
            day=self._datetime.day,
        )
