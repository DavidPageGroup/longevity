"""Entry points for functionality"""

# Copyright (c) 2018-2019 Aubrey Barnard.
#
# This is free software released under the MIT License
# (https://choosealicense.com/licenses/mit/).


import csv
import datetime
import json
import math
import re
import sys

from cdmdata import events
from cdmdata import examples
from cdmdata import records


# Utilities


def print_records(csv_format, header, records, output=sys.stdout):
    csv_writer = csv.writer(output, **csv_format)
    csv_writer.writerow(f[0] for f in header)
    for rec in records:
        csv_writer.writerow(rec)


# Handling dates


seconds_per_day = 24 * 60 * 60

def td_to_days(timedelta):
    return timedelta.total_seconds() / seconds_per_day


seconds_per_year = seconds_per_day * 365.25

def td_to_years(timedelta):
    return timedelta.total_seconds() / seconds_per_year


_date_pattern = re.compile(
    r'\s*(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\s*')

def parse_date(text):
    # Do our own parsing because `datetime.datetime.strptime` is
    # painfully slow.  (There are lots of locale-related calls.)
    match = _date_pattern.fullmatch(text)
    if match is None:
        return None
    return datetime.date(
        int(match['year']), int(match['month']), int(match['day']))


name2time_parser = {
    'float': float,
    'date': parse_date,
}


# API entry points


def gen_examples_at_intervals(
        events_csv_filename,
        time_type_name,
        start_age_years=30,
        interval_length_days=365.25,
):
    # Set up math with times that are either floats or dates.  Use typed
    # constants à la Julia.
    time_zero = 0.0
    time_one = 1.0
    mk_days_flt = float
    mk_years_flt = float
    if time_type_name == 'date':
        start_age_years = datetime.timedelta(
            days=start_age_years * 365.25)
        interval_length_days = datetime.timedelta(
            days=interval_length_days)
        time_zero = datetime.timedelta(0)
        time_one = datetime.timedelta(1)
        mk_days_flt = td_to_days
        mk_years_flt = td_to_years
    # Derive needed values
    events_header = events.header(name2time_parser[time_type_name])
    # Read event records and construct an event sequence for each
    # patient.  Then yield an example for each interval
    for ev_seq in events.read_sequences(
            records.read_csv(
                events_csv_filename,
                events.csv_format,
                events_header,
                header_detector=True,
                parser=False,
            ),
            header=events_header,
            parse_record=records.mk_parser(events_header),
    ):
        # Get the patient's date of birth
        dob = ev_seq.fact(('bx', 'dob'))
        # Skip this patient if they don't have a DOB
        if dob is None:
            continue
        dob = parse_date(dob)
        # Upper bound
        max_when = ev_seq.span(finite=True).hi
        max_age = max_when - dob
        span_len = max_age - start_age_years
        # Skip this patient if they are too young
        if span_len < time_zero:
            continue
        # Loop to produce each interval and its example
        curr_age = start_age_years
        n_itvls = math.ceil(span_len / interval_length_days)
        for i in range(n_itvls):
            next_age = start_age_years + (i + 1) * interval_length_days
            lo = dob + curr_age
            hi = dob + next_age - time_one # Back off by one
            itvl_len = mk_days_flt(hi - lo)
            n_evs = len(ev_seq.events_overlapping(lo, hi))
            age_flt = mk_years_flt(curr_age)
            # TODO is there a reasonable label?
            lbl = f'{i + 1}/{n_itvls}'
            yield [ev_seq.id, lo, hi, lbl, None, None,
                   itvl_len, n_evs, age_flt]
            # Increment
            curr_age = next_age


# CLI entry points


def gen_ex_itvls(
        events_csv_filename,
        time_type_name,
        start_age_years=30,
        interval_length_days=365,
):
    print_records(
        examples.csv_format,
        examples.header(name2time_parser[time_type_name]),
        gen_examples_at_intervals(
            events_csv_filename,
            time_type_name,
            float(start_age_years),
            float(interval_length_days),
        ),
    )


# Main


def cli(function_name, *args):
    """
    Call the given function from this module with the given string
    arguments.
    """
    globals()[function_name](*args)


if __name__ == '__main__':
    cli(*sys.argv[1:])
