# Tools for working with EMR event data

# Copyright (c) 2018 Aubrey Barnard.  This is free software released
# under the MIT License (https://choosealicense.com/licenses/mit/).


import csv
import datetime
import io
import itertools as itools
import json
import pathlib
import unittest

from barnapy import general
from barnapy import logging
from barnapy import parse
import esal


# Record format
fields = (
    'id',
    'lo',
    'hi',
    'tbl',
    'typ',
    'val',
    'jsn',
)
field_name2idx = {f: i for (i, f) in enumerate(fields)}


# Source tables
tables = (
    'bx', # biographic / demographic facts
    'dx', # diagnosis / condition events
    'mx', # measurement / lab / vitals events
    'ox', # observation events
    'px', # procedure events
    'rx', # prescription / drug events
    'vx', # visits
    'xx', # deaths
)


# Event records are literal CSV format delimited with pipes / bars
csv_format = dict(
    delimiter='|',
    quoting=csv.QUOTE_NONE,
    doublequote=False,
    escapechar=None,
    strict=False,
)


def records(lines, csv_format=csv_format, comment_char='#'):
    # Ignore comments and whitespace
    lines = filter(lambda s: s and not s.startswith(comment_char),
                   (line.strip() for line in lines))
    return csv.reader(lines, **csv_format)


def reconstruct_json(
        record, delimiter='|', field_name2idx=field_name2idx):
    if len(record) > len(field_name2idx):
        jsn_idx = field_name2idx['jsn']
        record[jsn_idx] = delimiter.join(record[jsn_idx:])
        del record[jsn_idx + 1:]
    return record


def parse_date(text, fmt='%Y-%m-%d'):
    return (datetime.datetime.strptime(text, fmt).date()
            if text
            else None)


def parse_record(record, json_constructor=json.loads):
    id, lo, hi, tbl, typ, val, jsn = record
    # Parse JSON if there is anything to parse and there is a
    # constructor
    if jsn:
        if json_constructor is not None:
            jsn = json_constructor(jsn)
    # Parse empty JSON as `None`
    else:
        jsn = None
    # Parse the remaining values and construct a new record
    return [
        int(id),
        parse_date(lo),
        parse_date(hi),
        tbl if tbl else None,
        parse.atom_err(typ, typ)[0] if typ else None,
        parse.atom_err(val, val)[0] if val else None,
        jsn,
    ]


def fact_from_record(record):
    _, _, _, tbl, typ, val, jsn = record
    return ((tbl, typ), (val, jsn))


def event_from_record(record):
    _, lo, hi, tbl, typ, val, jsn = record
    return esal.Event(esal.Interval(lo, hi), (tbl, typ), (val, jsn))


def read_records(
        file,
        csv_format=csv_format,
        comment_char='#',
        include_tables=set(tables),
        json_constructor=json.loads,
        record_parser=parse_record,
        include_record=None,
        record_transformer=None,
        field_name2idx=field_name2idx,
):
    # Open the file if it is a filename
    if isinstance(file, (str, pathlib.Path)):
        lines = open(file, 'rt')
    else:
        lines = file
    id_idx = field_name2idx['id']
    tbl_idx = field_name2idx['tbl']
    # Logger for tracking reading records
    logger = logging.getLogger(__name__)
    def tracker(count):
        logger.info('CSV records: {}', count)
    # Read the records
    for record in general.track_iterator(
            records(lines, csv_format, comment_char),
            tracker, track_every=100000,
            track_init=True, track_end=True):
        # Skip events from some tables
        if record[tbl_idx] not in include_tables:
            continue
        # Reconstruct JSON if needed
        if len(record) > len(field_name2idx):
            record = reconstruct_json(record, csv_format['delimiter'])
        # Parse record
        if record_parser is not None:
            record = record_parser(record, json_constructor)
        # Filter records if requested
        if not (include_record is None or include_record(record)):
            continue
        # Transform record
        if record_transformer is not None:
            record = record_transformer(record)
        yield record


def separate_fact_event_records(
        records,
        field_name2idx=field_name2idx,
):
    lo_idx = field_name2idx['lo']
    hi_idx = field_name2idx['hi']
    facts = []
    events = []
    for record in records:
        if record[lo_idx] is None and record[hi_idx] is None:
            facts.append(record)
        else:
            events.append(record)
    return facts, events


def event_sequences_from_records(
        records,
        fact_constructor=fact_from_record,
        event_constructor=event_from_record,
        field_name2idx=field_name2idx,
):
    id_idx = field_name2idx['id']
    # Logger for tracking reading records
    logger = logging.getLogger(__name__)
    def tracker(count):
        logger.info('Event records: {}', count)
    for rec_id, recs in itools.groupby(
            general.track_iterator(
                records,
                tracker, track_every=10000,
                track_init=True, track_end=True),
            key=lambda r: r[id_idx]):
        # Separate facts and events
        facts, events = separate_fact_event_records(recs)
        # Construct facts
        facts = (fact_constructor(f) for f in facts)
        # Construct events
        events = (event_constructor(e) for e in events)
        # Construct event sequence
        yield esal.EventSequence(events, facts, rec_id)


class EventDataTest(unittest.TestCase):

    def test_records(self):
        lines = [
            '   # various comments  \n',
            '  \t  \n',
            '\t# with various whitespace \t \n',
            '\t\r\v\n',
            'a|record\n',
            'an|other|record\n',
            '1|2|3|4|5\n',
            '\n',
            '# last one is empty\n',
            '||||\n',
        ]
        expected = [
            ['a', 'record'],
            ['an', 'other', 'record'],
            ['1', '2', '3', '4', '5'],
            ['', '', '', '', ''],
        ]
        actual = list(records(lines))
        self.assertEqual(expected, actual)

    def test_reconstruct_json(self):
        record = ['1', '1996-10-01', '1997-11-13', 'dx', '12345', '',
                  '"4 pipes: ', '', '', '', '!"']
        expected = ['1', '1996-10-01', '1997-11-13', 'dx', '12345', '',
                    '"4 pipes: ||||!"']
        actual = reconstruct_json(record)
        self.assertEqual(expected, actual)

    def test_parse_record(self):
        record = ['1', '1996-10-01', '1997-11-13', 'mx', '12345',
                  '100.0', '[1, 2, 3, 4, 5]']
        expected = [
            1, datetime.date(1996, 10, 1), datetime.date(1997, 11, 13),
            'mx', 12345, 100.0, [1, 2, 3, 4, 5]]
        actual = parse_record(record)
        self.assertEqual(expected, actual)

    def test_parse_record__leave_json(self):
        record = ['1', '1996-10-01', '1997-11-13', 'mx', '12345',
                  '100.0', '[1, 2, 3, 4, 5]']
        expected = [
            1, datetime.date(1996, 10, 1), datetime.date(1997, 11, 13),
            'mx', 12345, 100.0, '[1, 2, 3, 4, 5]']
        actual = parse_record(record, json_constructor=None)
        self.assertEqual(expected, actual)

    def test_parse_record__empty(self):
        record = ['0', '', '', '', '', '', '']
        expected = [0] + [None] * 6
        actual = parse_record(record)
        self.assertEqual(expected, actual)

    def test_read_records(self):
        text = '''
id|lo|hi|tbl|typ|val|jsn
1|||bx|dob|1932-11-29|
1|||bx|gndr|M|
1|||bx|race|8552|
1|||bx|record||
1|1991-11-15|1991-11-15|mx|3000330|4069590|
1|1991-11-15|1991-11-15|px|2108115||
1|1991-11-15|1991-11-15|vx|9202||
1|1996-06-01||dx|80180||
1|1997-07-01||dlux|486||
1|2009-07-04|2009-07-04|ox|4222303||{"a":1,"b":2,"3":"c"}
1|2009-07-30|2009-08-29|rx|19078559||
1|2009-08-12||xx|||"|||||"
'''
        expected = (
            # Interval, event type, value
            (1, None, None, 'bx', 'dob', '1932-11-29', None),
            (1, None, None, 'bx', 'gndr', 'M', None),
            (1, None, None, 'bx', 'race', 8552, None),
            (1, '1991-11-15', '1991-11-15', 'mx', 3000330, 4069590, None),
            (1, '1991-11-15', '1991-11-15', 'px', 2108115, None, None),
            (1, '1991-11-15', '1991-11-15', 'vx', 90210, None, None),
            (1, '1996-06-01', None, 'dx', 80180, None, None),
            (1, '2009-07-04', '2009-07-04', 'ox', 4222303, None, {'a': 1, 'b': 2, '3': 'c'}),
            (1, '2009-07-30', '2009-08-29', 'rx', 19078559, None, None),
            (1, '2009-08-12', None, 'xx', None, None, '|||||'),
        )
        expected = [[r[0], parse_date(r[1]), parse_date(r[2]), *r[3:]]
                    for r in expected]
        file = io.StringIO(text)
        actual = list(read_records(
            file,
            include_record=lambda r: not (
                r[field_name2idx['tbl']] == 'bx' and
                r[field_name2idx['typ']] == 'record'),
            record_transformer=lambda r: [
                *r[:4], (r[4] if r[4] != 9202 else 90210), *r[5:]],
        ))
        self.maxDiff = None
        self.assertEqual(expected, actual)
