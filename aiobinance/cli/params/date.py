from datetime import datetime

import click


class Date(click.ParamType):
    name = "date"

    def __init__(self, formats=None):
        self.formats = formats or [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S%z",
        ]

    def get_metavar(self, param: click.Option):
        return "[{}]".format("|".join(self.formats))

    def _try_to_convert_date(self, value, format):
        try:
            dt = datetime.strptime(value, format)
            if dt.hour == dt.minute == dt.second == dt.microsecond == 0:
                dt = dt.date()  # no time was specified => assume nothing at this stage
            return dt
        except ValueError:
            return None

    def convert(self, value, param, ctx):
        for format in self.formats:
            date = self._try_to_convert_date(value, format)
            if date:
                return date

        self.fail(
            "invalid date format: {}. (choose from {})".format(
                value, ", ".join(self.formats)
            )
        )

    def __repr__(self):
        return "Date"
