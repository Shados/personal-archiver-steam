import datetime
from typing import Any, Tuple

import sqlalchemy
from sqlalchemy.types import DateTime, TypeDecorator

MessageRow = Tuple[int, int, int, str, str, datetime.datetime, str]
UserRow = Tuple[int, str]


# NOTE: I have no idea *why*, but sqlalchemy appears to convert
# `datetime.datetime` objects from their associated timezone into the local
# timezone prior to storing them in `timestamp without time zone` columns. The
# SQL spec doesn't say anything about how `timestamp without time zone` is
# meant to be interpreted wrt. "what timezone is it in then?", so doing this
# sort of implicit/automatic tz conversion on data going into such columns does
# *not* seem well-justified to me.
#
# As a workaround, we explicitly convert any incoming timezones to utc, then
# strip the tzinfo field, which prevents sqlalchemy from being able to do any
# sort of tz-aware conversion on them. Similarly, we read back UTC timezones.
#
# This code is based on an example from sqlalchemy's documentation.
class DateTimeUTC(TypeDecorator):
    impl = DateTime
    cache_ok = True

    def process_bind_param(
        self, value: datetime.datetime | None, dialect: sqlalchemy.engine.Dialect
    ) -> Any:
        if value is not None:
            if not value.tzinfo:
                raise TypeError("tzinfo is required")
            value = value.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        return value

    def process_result_value(
        self, value: Any | None, dialect: sqlalchemy.engine.Dialect
    ) -> datetime.datetime | None:
        if value is not None:
            value = value.replace(tzinfo=datetime.timezone.utc)
        return value
