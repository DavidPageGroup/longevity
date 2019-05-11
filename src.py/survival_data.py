"""Transform EMR event data into survival analysis data"""

# Copyright (c) 2018-2019 Aubrey Barnard.
#
# This is free software released under the MIT License
# (https://choosealicense.com/licenses/mit/).


import datetime
import io
import pathlib
import pprint
import sys
import unittest

from barnapy import general
from barnapy import logging
import esal

# "Install" related modules by updating import path
this_dir = pathlib.Path(__file__).absolute().parent
sys.path.append(str(this_dir))

import event_data


# Suggested (but optional) functionality


def json_get(json_dict, name, default=None):
    val = json_dict.get(name)
    if val is None or val == '':
        return default
    return val


def include_record(record):
    tbl = record[event_data.field_name2idx['tbl']]
    # Drop original person records
    if tbl == 'bx':
        typ = record[event_data.field_name2idx['typ']]
        if typ == 'record':
            return False
    # Ignore medication mentions (drug type concept ID 38000178)
    elif tbl == 'rx':
        jsn = record[event_data.field_name2idx['jsn']]
        attrs = jsn if isinstance(jsn, dict) else {}
        if json_get(attrs, 'drug_type_concept_id') == 38000178:
            return False
    return True


def infer_drug_days_supply(
        days_supply=None,
        refills=None,
        quantity=None,
        default_rx_days=30,
):
    """
    Return the number of days this medication is "active".

    The number of days this medication is active is determined by the
    value of `days_supply` if it exists, and otherwise by a combination
    of the other fields so as to estimate the number of days in the
    prescription.  When the number of days is missing, the quantity is
    assumed to be 1 / day.  When the quantity is missing, each refill is
    assumed to "contain" `default_rx_days`.
    """
    # The total number of fills is `refills + 1`
    if isinstance(refills, int):
        refills += 1
    # Ignore `None` for all fields
    if days_supply is not None:
        if refills:
            return days_supply * refills
        else:
            return days_supply
    elif quantity is not None:
        if refills:
            return quantity * refills
        else:
            return quantity
    elif refills:
        return default_rx_days * refills
    else:
        return default_rx_days


def set_drug_interval(
        record,
        min_days=30,
        washout=0,
        infer_drug_days_supply=infer_drug_days_supply,
        days_supply_key='days_supply',
        refills_key='refills',
        quantity_key='quantity',
):
    # Access fields
    lo_idx = event_data.field_name2idx['lo']
    hi_idx = event_data.field_name2idx['hi']
    jsn_idx = event_data.field_name2idx['jsn']
    lo = record[lo_idx]
    hi = record[hi_idx]
    jsn = record[jsn_idx]
    # Extra attributes must be a dictionary
    attrs = jsn if isinstance(jsn, dict) else {}
    # Guess at the days supply based on the extra attributes
    days = infer_drug_days_supply(
        days_supply=json_get(attrs, days_supply_key),
        refills=json_get(attrs, refills_key),
        quantity=json_get(attrs, quantity_key),
        default_rx_days=min_days,
    )
    # Compute interval
    days = max(days, min_days) + washout
    days = datetime.timedelta(days=days)
    # Only increase the interval
    if lo and hi:
        if hi - lo < days:
            hi = lo + days
    elif lo:
        hi = lo + days
    # Update the record in place
    record[hi_idx] = hi
    # Return the updated record
    return record


def transform_record(record):
    tbl_idx = event_data.field_name2idx['tbl']
    tbl = record[tbl_idx]
    if tbl == 'rx':
        return set_drug_interval(record)
    else:
        return record


def limit_to_ages(ev_seq, min_age=None, max_age=None):
    # Exit early if there is nothing to do
    if min_age is None and max_age is None:
        return ev_seq
    # Get DOB (ignore JSON)
    dob = ev_seq.fact(('bx', 'dob'))
    if dob is None:
        # No DOB.  What can one do except return the original?
        return ev_seq
    dob, jsn = dob
    dob = event_data.parse_date(dob)
    # Calculate bounds
    min_date = (
        dob + datetime.timedelta(days=(min_age * 365))
        if min_age is not None
        else None)
    max_date = (
        dob + datetime.timedelta(days=(max_age * 365))
        if max_age is not None
        else None)
    bounds = esal.Interval(
        min_date if min_date is not None else datetime.date.min,
        max_date if max_date is not None else datetime.date.max,
    )
    # Limit events to bounds
    evs = []
    for ev in ev_seq.events():
        when = ev.when
        if when.issubset(bounds):
            evs.append(ev)
        elif when.intersects(bounds):
            evs.append(esal.Event(
                when.intersection(bounds), ev.type, ev.value))
    # Add events to define study period
    if min_date is not None:
        evs.insert(0, esal.Event(esal.Interval(min_date),
                                 ('study', 'lo'), ()))
    if max_date is not None:
        evs.append(esal.Event(esal.Interval(max_date),
                              ('study', 'hi'), ()))
    return ev_seq.copy(events=evs)


# Feature vectors


def mk_fact_feature(fact_key):
    def get_fact_value(ev_seq):
        val = ev_seq.fact(fact_key)
        if val is None:
            return None
        else:
            val, jsn = val
            return val
    return get_fact_value


def mk_has_event_feature(event_key):
    def has_event(ev_seq):
        return int(ev_seq.has_type(event_key))
    return has_event


def mk_event_count_feature(event_key):
    def get_event_count(ev_seq):
        return ev_seq.n_events_of_type(event_key)
    return get_event_count


def mk_feature_vector_function(*funcs):
    def feature_vector_function(ev_seq):
        return [f(ev_seq) for f in funcs]
    return feature_vector_function


def age_at_first_event(ev_seq):
    # Exit early if the sequence is empty
    if len(ev_seq) == 0:
        return None
    # Get earliest date
    min_date = ev_seq[0].when.lo
    # Get DOB (ignore JSON)
    dob = ev_seq.fact(('bx', 'dob'))
    if dob is None:
        # No DOB.  What can one do except return `None`?
        return None
    dob, jsn = dob
    dob = event_data.parse_date(dob)
    return round((min_date - dob).days / 365, 1)


# Necessary functionality


def parse_event_type(text, delimiter='|', tbl_type=str, typ_type=int):
    tbl, typ = text.split(delimiter, 2)
    tbl = tbl_type(tbl) if tbl else None
    typ = typ_type(typ) if typ else None
    return (tbl, typ)


def read_event_types(file, comment_char='#', parser=parse_event_type):
    # Try to open the file unless it is already a stream
    if not isinstance(file, io.IOBase):
        file = open(file, 'rt')
    with file as lines:
        for line in lines:
            line = line.strip()
            if not line or line.startswith(comment_char):
                continue
            yield parse_event_type(line)


def build_exposure_outcome_event_type_map(
        exposure_types,
        outcome_types,
        exposure_event_type='exp',
        outcome_event_type='out',
):
    event_type2type = {t: exposure_event_type for t in exposure_types}
    event_type2type.update(
        (t, outcome_event_type) for t in outcome_types)
    return event_type2type


def map_event_types(events, type2type, replace=False):
    for ev in events:
        # Encode this event if it matches
        if ev.type in type2type:
            yield esal.Event(ev.when, type2type[ev.type], ev.value)
            # Yield the original if requested
            if not replace:
                yield ev
        # Otherwise leave the event alone
        else:
            yield ev


def make_eras(event_sequence, event_types, max_gap=0):
    union_aggregator = esal.mk_union_aggregator(
        min_len=datetime.timedelta(0), max_gap=max_gap)
    return event_sequence.aggregate_events(
        union_aggregator, types=event_types)


def survivalize(
        ev_seq,
        event_type_map,
        study_period_definer=None,
        replace_mapped_events=False,
        era_max_gap=0,
):
    # Encode exposures and outcomes
    events = map_event_types(
        ev_seq.events(), event_type_map, replace_mapped_events)
    ev_seq = ev_seq.copy(events=events)
    # Make exposures and outcomes into eras
    ev_seq = make_eras(
        ev_seq, set(event_type_map.values()), era_max_gap)
    # Limit sequence to study period.  Do this after making eras to
    # avoid missing eras that would otherwise overlap the bounds of the
    # study period.
    if study_period_definer is not None:
        ev_seq = study_period_definer(ev_seq)
    return ev_seq


def events_to_sequences(
        in_file,
        event_type_map,
        csv_format=event_data.csv_format,
        comment_char='#',
        include_tables=event_data.tables,
        include_record=include_record,
        record_transformer=transform_record,
        fact_constructor=event_data.fact_from_record,
        event_constructor=event_data.event_from_record,
        study_period_definer=None,
        replace_mapped_events=False,
        era_max_gap=0,
):
    # Read, parse, and filter event records.  This includes
    # interpreting drug records.
    records = event_data.read_records(
        in_file,
        csv_format=csv_format,
        comment_char=comment_char,
        include_tables=set(include_tables),
        include_record=include_record,
        record_transformer=record_transformer,
    )
    # Gather event records into event sequences
    ev_seqs = event_data.event_sequences_from_records(
        records, fact_constructor, event_constructor)
    # Make event sequences suitable for survival analysis
    for ev_seq in ev_seqs:
        yield survivalize(
            ev_seq,
            event_type_map,
            study_period_definer,
            replace_mapped_events,
            era_max_gap,
        )


def days_between(lo, hi):
    return round((hi - lo).total_seconds() / 86400)


# Survival data fields
fields = (
    'id', # example ID
    'dates', # interval of survival time
    'lo', # survival time lo (relative to reference)
    'hi', # survival time hi (relative to reference)
    'len', # interval length
    'exp', # exposed?
    'out', # outcome?
    'fv', # feature vector of covariates (if any)
)
field_name2idx = {f: i for (i, f) in enumerate(fields)}


def build_example(
        event_sequence,
        ref_lo,
        when_lo,
        when_hi,
        exposure_event_type,
        outcome_event_type,
        state,
        feature_vector_function=None,
):
    # Build a feature vector of covariates if such a feature vector
    # function is specified
    itvl = esal.Interval(when_lo, when_hi)
    subseq = event_sequence.subsequence(
        event_sequence.events_overlapping(
            itvl.lo, itvl.hi, itvl.is_lo_open, itvl.is_hi_open))
    fv = (feature_vector_function(subseq)
          if feature_vector_function is not None
          else None)
    return [
        event_sequence.id,
        esal.Interval(when_lo, when_hi),
        days_between(ref_lo, when_lo),
        days_between(ref_lo, when_hi),
        days_between(when_lo, when_hi),
        state[exposure_event_type],
        state[outcome_event_type],
        fv,
    ]


def examples_from_transitions(
        event_sequence,
        exposure_event_type='exp',
        outcome_event_type='out',
        feature_vector_function=None,
):
    # Exit early if empty sequence
    if len(event_sequence) == 0:
        return
    # Find the time bounds of the event sequence
    if isinstance(event_sequence[0].when, esal.Interval):
        es_lo = event_sequence[0].when.lo
        es_hi = max(e.when.hi for e in event_sequence)
    else:
        es_lo = event_sequence[0].when
        es_hi = event_sequence[-1].when

    # The time periods of interest are those where the exposure and
    # outcome event indicators remain constant.  Thus, all the time
    # periods are defined by transitions of the exposure and outcome
    # events.  This means all the state changes can be tracked by
    # iterating over when events start and end.

    # Iterate through exposure and outcome states to generate examples
    before = es_lo
    state = {exposure_event_type: 0, outcome_event_type: 0}
    for tx in event_sequence.transitions(
            exposure_event_type, outcome_event_type):
        now, starts, stops, points = tx
        # Yield an example if this is the end of a time period
        if now > before:
            yield build_example(
                event_sequence, es_lo, before, now,
                exposure_event_type, outcome_event_type,
                state, feature_vector_function)

        # Update the state with this transition

        # Treat stops as happening just before now
        for event in stops:
            state[event.type] = 0
        # Yield an additional example if there are point events
        if points:
            # Treat point events as starting now
            for event in points:
                state[event.type] = 1
            # Yield example for point
            yield build_example(
                event_sequence, es_lo, now, now,
                exposure_event_type, outcome_event_type,
                state, feature_vector_function)
            # Treat point events as ending now
            for event in points:
                state[event.type] = 0
        # Treat starts as happening directly after now
        for event in starts:
            state[event.type] = 1
        # Update `before`
        before = now
    if es_hi > before:
        yield build_example(
            event_sequence, es_lo, before, es_hi,
            exposure_event_type, outcome_event_type,
            state, feature_vector_function)


def examples_to_survival_examples(
        examples, field_name2idx=field_name2idx):
    out_idx = field_name2idx['out']
    # Iterate over examples from transitions.  Stop when there is an
    # outcome.
    prev_ex = None
    for curr_ex in examples:
        # If the current example has the outcome, transfer it to the
        # previous example, so that an outcomes "ends" an example.
        # Yield the example and stop generating examples.
        if curr_ex[out_idx] == 1:
            if prev_ex is None:
                prev_ex = curr_ex
            else:
                prev_ex[out_idx] = 1
            # Jump to yielding the last example
            break
        # Yield the previous example now that we know the current
        # example doesn't have the outcome
        if prev_ex is not None:
            yield prev_ex
        # Increment
        prev_ex = curr_ex
    # Yield the last example (if there were any examples at all)
    if prev_ex is not None:
        yield prev_ex


def event_sequence_to_survival_data_examples(
        event_sequence,
        exposure_event_type='exp',
        outcome_event_type='out',
        feature_vector_function=None,
        field_name2idx=field_name2idx,
):
    # Generate general examples from each transition
    exs = examples_from_transitions(
        event_sequence,
        exposure_event_type, outcome_event_type,
        feature_vector_function)
    # Turn the general examples into survival examples
    exs = examples_to_survival_examples(exs)
    return exs


def print_survival_example(
        example,
        delimiter='|',
        file=sys.stdout,
        id_idx=field_name2idx['id'],
        dates_idx=field_name2idx['dates'],
        fv_idx=field_name2idx['fv'],
):
    # Unpack / Flatten
    ex = [
        example[id_idx],
        example[dates_idx].lo,
        example[dates_idx].hi,
        *example[(dates_idx + 1):fv_idx],
        *(example[fv_idx] if example[fv_idx] else ()),
    ]
    # Convert `None` to ''
    for idx, field in enumerate(ex):
        if field is None:
            ex[idx] = ''
    print(*ex, sep=delimiter, file=file)


def main_api( # TODO redo everything in terms of `cdmdata`
        exposure_types_filename,
        outcome_types_filename,
        *, # Prevent any additional positional arguments, like from the
           # command line
        in_file=sys.stdin,
        out_file=sys.stdout,
        comment_char='#',
        event_type_parser=parse_event_type,
        exposure_event_type=('exp',),
        outcome_event_type=('out',),
        csv_format=event_data.csv_format,
        include_tables=event_data.tables,
        include_record=None,
        record_transformer=None,
        fact_constructor=event_data.fact_from_record,
        event_constructor=event_data.event_from_record,
        study_period_definer=None,
        replace_mapped_events=False,
        era_max_gap=datetime.timedelta(0),
        feature_vector_header=(),
        feature_vector_function=None,
        output_delimiter='|',
        field_name2idx=field_name2idx,
):
    # Log start
    logger = logging.getLogger(__name__)
    logger.info('Starting `main_api` with arguments:\n{}',
                pprint.pformat(locals()))
    # Read exposure and outcome IDs
    exposure_types = list(read_event_types(
        exposure_types_filename, comment_char, event_type_parser))
    outcome_types = list(read_event_types(
        outcome_types_filename, comment_char, event_type_parser))
    # Log exposures and outcomes
    logger.info('Using {} exposures:\n{}', len(exposure_types),
                '\n'.join(str(x) for x in exposure_types))
    logger.info('Using {} outcomes:\n{}', len(outcome_types),
                '\n'.join(str(x) for x in outcome_types))
    # Map event types to encode exposures and outcomes
    event_type2type = build_exposure_outcome_event_type_map(
        exposure_types, outcome_types, exposure_event_type, outcome_event_type)
    # Read records from input, process into events, assemble into
    # sequences
    logger.info('Reading event records and assembling into sequences')
    seqs = events_to_sequences(
        in_file,
        event_type2type,
        csv_format=csv_format,
        comment_char=comment_char,
        include_tables=include_tables,
        include_record=include_record,
        record_transformer=record_transformer,
        fact_constructor=fact_constructor,
        event_constructor=event_constructor,
        study_period_definer=study_period_definer,
        replace_mapped_events=replace_mapped_events,
        era_max_gap=era_max_gap,
    )
    # Print data header
    id_idx = field_name2idx['id']
    dates_idx = field_name2idx['dates']
    fv_idx = field_name2idx['fv']
    print(fields[id_idx], 'date_lo', 'date_hi',
          *fields[(dates_idx + 1):fv_idx],
          *feature_vector_header,
          sep=output_delimiter, file=out_file)
    # Logger for tracking reading records
    def tracker(count):
        logger.info('Event sequences: {}', count)
    # Generate survival examples from sequences
    logger.info('Generating survival data examples from event sequences')
    for ev_seq in general.track_iterator(
            seqs,
            tracker, track_every=1000,
            track_init=True, track_end=True):
        #ev_seq.pprint(file=sys.stderr)
        exs = list(event_sequence_to_survival_data_examples(
            ev_seq,
            exposure_event_type, outcome_event_type,
            feature_vector_function, field_name2idx))
        if len(exs) == 0:
            logger.info('Discarding event sequence {}: '
                        'No events in study period', ev_seq.id)
        # Print examples
        for ex in exs:
            print_survival_example(
                ex,
                delimiter=output_delimiter,
                file=out_file,
                id_idx=id_idx,
                dates_idx=dates_idx,
                fv_idx=fv_idx,
            )
    logger.info('Done `main_api`')


# Tests


class SurvivalDataTest(unittest.TestCase):

    def mk_ev(date1, date2, ev_type, value=None):
        d1 = datetime.datetime.strptime(date1, '%Y-%m-%d').date()
        d2 = datetime.datetime.strptime(date2, '%Y-%m-%d').date()
        return esal.Event(esal.Interval(d1, d2), ev_type, value)

    # Timeline with exposures with gaps of up to 90 days, outcomes, and
    # other covariates
    #
    #             exp1 exp2 era out a   b
    # 2012-06-17:                   +
    # 2013-01-12: +         +       |
    # 2013-02-11: -         |       |
    # 2013-03-11: +         |       |
    # 2013-04-14: |         |       -
    # 2013-10-07: -         -
    # 2014-05-02: +         +
    # 2014-07-10: |         |           +
    # 2015-02-26: -         |           |
    # 2015-05-22: +         |           |
    # 2015-06-13: |         |       +   |
    # 2015-09-19: -         |       |   |
    # 2015-12-12: +         |       |   |
    # 2016-03-11: -         -       |   |
    # 2016-05-18:                   -   |
    # 2016-08-23: +         +           |
    # 2016-12-05: |         |           -
    # 2016-12-21: |         |       +
    # 2017-01-20: -         |       |
    # 2017-03-29: +         |       |
    # 2017-04-04: |    +    |       |
    # 2017-04-28: -    |    |       |
    # 2017-05-04:      |    |   *   |
    # 2017-06-22:      |    |       |   +
    # 2017-08-02:      -    -       |   |
    # 2017-09-15:               *   |   |
    # 2017-10-27:                   -   |
    # 2017-12-08:      +    +           |
    # 2018-01-16:      |    |   *       |
    # 2018-03-08:      -    |           |
    # 2018-04-21:           |           -
    # 2018-05-27:      +    |
    # 2018-07-20:      |    |       +
    # 2018-10-24:      -    -       |
    # 2018-11-11:               *   |
    # 2018-12-28:                   -
    evs = (
        # Exposure 1
        mk_ev('2013-01-12', '2013-02-11', 'e1'),
        mk_ev('2013-03-11', '2013-10-07', 'e1'),
        mk_ev('2014-05-02', '2015-02-26', 'e1'),
        mk_ev('2015-05-22', '2015-09-19', 'e1'),
        mk_ev('2015-12-12', '2016-03-11', 'e1'),
        mk_ev('2016-08-23', '2017-01-20', 'e1'),
        mk_ev('2017-03-29', '2017-04-28', 'e1'),
        # Exposure 2
        mk_ev('2017-04-04', '2017-08-02', 'e2'),
        mk_ev('2017-12-08', '2018-03-08', 'e2'),
        mk_ev('2018-05-27', '2018-10-24', 'e2'),
        # Exposure eras
        mk_ev('2013-01-12', '2013-10-07', 'era'),
        mk_ev('2014-05-02', '2016-03-11', 'era'),
        mk_ev('2016-08-23', '2017-08-02', 'era'),
        mk_ev('2017-12-08', '2018-10-24', 'era'),
        # Outcome
        mk_ev('2017-05-04', '2017-05-04', 'o'),
        mk_ev('2017-09-15', '2017-09-15', 'o'),
        mk_ev('2018-01-16', '2018-01-16', 'o'),
        mk_ev('2018-11-11', '2018-11-11', 'o'),
        # Covariates
        mk_ev('2012-06-17', '2013-04-14', 'a'),
        mk_ev('2015-06-13', '2016-05-18', 'a'),
        mk_ev('2016-12-21', '2017-10-27', 'a'),
        mk_ev('2018-07-20', '2018-12-28', 'a'),
        mk_ev('2014-07-10', '2016-12-05', 'b'),
        mk_ev('2017-06-22', '2018-04-21', 'b'),
    )

    # Examples from the above events
    examples = [
        # id, itvl, lo, hi, len, exp?, out?, fv
        [0, esal.Interval(datetime.date(2012, 6, 17),
                          datetime.date(2013, 1, 12)),
         0, 209, 209, 0, 0, None],
        [0, esal.Interval(datetime.date(2013, 1, 12),
                          datetime.date(2013, 10, 7)),
         209, 477, 268, 1, 0, None],
        [0, esal.Interval(datetime.date(2013, 10, 7),
                          datetime.date(2014, 5, 2)),
         477, 684, 207, 0, 0, None],
        [0, esal.Interval(datetime.date(2014, 5, 2),
                          datetime.date(2016, 3, 11)),
         684, 1363, 679, 1, 0, None],
        [0, esal.Interval(datetime.date(2016, 3, 11),
                          datetime.date(2016, 8, 23)),
         1363, 1528, 165, 0, 0, None],
        [0, esal.Interval(datetime.date(2016, 8, 23),
                          datetime.date(2017, 5, 4)),
         1528, 1782, 254, 1, 0, None],
        # First outcome
        [0, esal.Interval(datetime.date(2017, 5, 4)),
         1782, 1782, 0, 1, 1, None],
        [0, esal.Interval(datetime.date(2017, 5, 4),
                          datetime.date(2017, 8, 2)),
         1782, 1872, 90, 1, 0, None],
        [0, esal.Interval(datetime.date(2017, 8, 2),
                          datetime.date(2017, 9, 15)),
         1872, 1916, 44, 0, 0, None],
        [0, esal.Interval(datetime.date(2017, 9, 15)),
         1916, 1916, 0, 0, 1, None],
        [0, esal.Interval(datetime.date(2017, 9, 15),
                          datetime.date(2017, 12, 8)),
         1916, 2000, 84, 0, 0, None],
        [0, esal.Interval(datetime.date(2017, 12, 8),
                          datetime.date(2018, 1, 16)),
         2000, 2039, 39, 1, 0, None],
        [0, esal.Interval(datetime.date(2018, 1, 16)),
         2039, 2039, 0, 1, 1, None],
        [0, esal.Interval(datetime.date(2018, 1, 16),
                          datetime.date(2018, 10, 24)),
         2039, 2320, 281, 1, 0, None],
        [0, esal.Interval(datetime.date(2018, 10, 24),
                          datetime.date(2018, 11, 11)),
         2320, 2338, 18, 0, 0, None],
        [0, esal.Interval(datetime.date(2018, 11, 11)),
         2338, 2338, 0, 0, 1, None],
        [0, esal.Interval(datetime.date(2018, 11, 11),
                          datetime.date(2018, 12, 28)),
         2338, 2385, 47, 0, 0, None],
    ]

    def test_set_drug_interval(self):
        record = [
            1, datetime.date(2000, 1, 1), datetime.date(2000, 2, 1),
            'rx', 1234, None, {'days':30, 'qty': 45, 'refills':4}]
        expected = [
            1, datetime.date(2000, 1, 1), datetime.date(2000, 7, 1),
            'rx', 1234, None, {'days':30, 'qty': 45, 'refills':4}]
        actual = set_drug_interval(record, washout=32)
        self.assertEqual(expected, actual)

    def test_set_drug_interval__no_json(self):
        record = [
            1, datetime.date(2000, 1, 1), datetime.date(2000, 1, 11),
            'rx', 1234, None, None]
        expected = [
            1, datetime.date(2000, 1, 1), datetime.date(2000, 2, 14),
            'rx', 1234, None, None]
        actual = set_drug_interval(record, washout=14)
        self.assertEqual(expected, actual)

    def test_limit_to_ages(self):
        mk_ev = SurvivalDataTest.mk_ev
        dob = datetime.date(2000, 1, 1)
        lo = datetime.date(2015, 10, 25)
        hi = datetime.date(2017, 2, 11)
        expected = [
            mk_ev('2015-10-25', '2015-10-25', ('study', 'lo'), ()),
            mk_ev('2015-10-25', '2016-03-11', 'era'),
            mk_ev('2015-10-25', '2016-05-18', 'a'),
            mk_ev('2015-10-25', '2016-12-05', 'b'),
            mk_ev('2015-12-12', '2016-03-11', 'e1'),
            mk_ev('2016-08-23', '2017-01-20', 'e1'),
            mk_ev('2016-08-23', '2017-02-11', 'era'),
            mk_ev('2016-12-21', '2017-02-11', 'a'),
            mk_ev('2017-02-11', '2017-02-11', ('study', 'hi'), ()),
        ]
        ev_seq = esal.EventSequence(self.evs)
        ev_seq['bx', 'dob'] = ('2000-01-01', None) # Include spot for JSON
        actual = limit_to_ages(
            ev_seq,
            (lo - dob).days / 365,
            (hi - dob).days / 365,
        )
        self.maxDiff = None
        self.assertEqual(ev_seq.id, actual.id)
        self.assertEqual(ev_seq.facts(), actual.facts())
        self.assertEqual(expected, list(actual.events()))

    def test_feature_vector_function(self):
        fvf = mk_feature_vector_function(
            age_at_first_event,
            mk_fact_feature(('bx', 'gndr')),
            mk_fact_feature(('bx', 'race')),
            mk_has_event_feature('e'),
            mk_has_event_feature('o'),
            mk_event_count_feature('a'),
            mk_event_count_feature('b'),
            mk_event_count_feature('c'),
        )
        ev_seq = esal.EventSequence(self.evs)
        ev_seq['bx', 'dob'] = ('2000-01-01', None) # Include spot for JSON
        ev_seq['bx', 'gndr'] = ('F', None)
        expected = [12.5, 'F', None, 0, 1, 4, 2, 0]
        actual = fvf(ev_seq)
        # Make sure types agree because `0 == False` in Python
        self.assertEqual([(type(x), x) for x in expected],
                         [(type(x), x) for x in actual])

    def test_make_eras(self):
        # Expected: event sequence with eras as defined above
        era_evs = [(esal.Event(e.when, 'e')
                    if e.type == 'era'
                    else e)
                   for e in self.evs
                   if e.type not in ('e1', 'e2')]
        era_es = esal.EventSequence(era_evs)
        # Actual: event sequence with exposures to be combined into eras
        evs = [(esal.Event(e.when, 'e')
                if e.type in ('e1', 'e2')
                else e)
               for e in self.evs
               if e.type != 'era']
        es = esal.EventSequence(evs)
        # Make eras
        es = make_eras(es, ('e', 'o'), max_gap=datetime.timedelta(90))
        self.assertEqual(len(era_es), len(es))
        for ev1, ev2 in zip(era_es, es):
            self.assertEqual(ev1.type, ev2.type)
            self.assertEqual(ev1.when, ev2.when)

    def test_examples_from_transitions(self):
        evs = [(esal.Event(e.when, 'e')
                if e.type == 'era'
                else e)
               for e in self.evs
               if e.type not in ('e1', 'e2')]
        es = esal.EventSequence(evs, id_=0)
        exs_act = list(examples_from_transitions(es, 'e', 'o'))
        self.assertEqual(self.examples, exs_act)

    def test_examples_to_survival_examples(self):
        exs_exp = self.examples[:6]
        # Update a copy of the example to keep the original list intact
        ex = list(exs_exp[5])
        ex[field_name2idx['out']] = 1
        exs_exp[5] = ex
        exs_act = list(examples_to_survival_examples(self.examples))
        self.assertEqual(exs_exp, exs_act)

    # Concept IDs:
    #   154584207: lo (     x < 3)
    #   443055837: ok (3 <= x < 7)
    #   867640248: hi (7 <= x    )
    #
    # dxs: 1927, 2818, 4181, 9677
    # rxs: 377, 731, 733, 976
    events_csv_text = '''
id|lo|hi|tbl|typ|val|jsn

746|||bx|dob|1944-09-03|
746|||bx|ethn|38003564|
746|||bx|gndr|F|
746|||bx|race|4212311|
746|||bx|record||

746|1979-11-13|1979-11-13|mx|88428|154584207|{"val":1.28,"unit":"g"}
746|1979-11-13||dx|2818||
746|1979-11-13|1980-11-12|rx|976||{"quantity":20,"refills":1}
746|1979-11-13|1979-11-13|vx|2||{"care_site_id":1}
746|1979-11-13||dx|2818||{"provider_id":276750642}

746|2005-02-06|2005-02-06|px|58||
746|2005-02-06|2005-02-06|vx|2||{"care_site_id":1}
746|2005-02-06|2005-02-06|vx|2||{"care_site_id":5}
746|2005-02-06|2005-02-07|rx|377||{"days_supply":30,"refills":10}
746|2005-02-06||dx|9677||

746|2005-05-30|2005-05-30|px|70||{"provider_id":276750642}
746|2005-05-30|2005-05-30|mx|65772|443055837|{"val":5.4,"unit":"u/L"}
746|2005-05-30|2005-05-30|mx|29979|154584207|{"val":2.66,"unit":"mg"}
746|2005-05-30||dx|4181||

746|2007-11-10|2007-11-10|vx|2||{"provider_id":276750642}
746|2007-11-10||dx|1927||{"condition_source_value":"VVV04.08486"}
746|2007-11-10|2007-11-11|rx|733||{"days_supply":90}
746|2007-11-10|2007-11-10|mx|29979|443055837|{"val":3.51,"unit":"mg"}
746|2007-11-10|2007-11-10|ox|16976||{"provider_id":31866686}
746|2007-11-10|2007-11-10|ox|96980||{"provider_id":31866686}
746|2007-11-10|2008-11-09|rx|731||

746|2008-01-25|2008-01-26|rx|733||{"days_supply":90,"refills":12}

746|2008-10-28|2009-10-29|rx|731||{"quantity":30,"provider_id":276750642,"refills":24}

746|2010-10-22||xx|||
'''

    def test_main(self):
        exposures_text = '''
rx|377
rx|733
rx|976
'''
        outcomes_text = '''
xx|
'''
        examples_csv_text = '''
id|date_lo|date_hi|lo|hi|len|exp|out
746|1979-11-13|1980-11-12|0|365|365|1|0
746|1980-11-12|2005-02-06|365|9217|8852|0|0
746|2005-02-06|2006-01-02|9217|9547|330|1|0
746|2006-01-02|2007-11-10|9547|10224|677|0|0
746|2007-11-10|2010-10-22|10224|11301|1077|1|1
'''.lstrip()
        exps_file = io.StringIO(exposures_text)
        outs_file = io.StringIO(outcomes_text)
        evs_file = io.StringIO(self.events_csv_text)
        exs_file = io.StringIO()
        main_api(
            exps_file, outs_file,
            in_file=evs_file, out_file=exs_file,
            include_record=include_record,
            record_transformer=transform_record,
        )
        self.maxDiff = None
        self.assertEqual(examples_csv_text, exs_file.getvalue())

    def test_main__immediate_outcome(self):
        exposures_text = '''
rx|976
'''
        outcomes_text = '''
dx|2818
'''
        examples_csv_text = '''
id|date_lo|date_hi|lo|hi|len|exp|out
746|1979-11-13|1979-11-13|0|0|0|0|1
'''.lstrip()
        exps_file = io.StringIO(exposures_text)
        outs_file = io.StringIO(outcomes_text)
        evs_file = io.StringIO(self.events_csv_text)
        exs_file = io.StringIO()
        main_api(exps_file, outs_file,
                 in_file=evs_file, out_file=exs_file)
        self.maxDiff = None
        self.assertEqual(examples_csv_text, exs_file.getvalue())

    def test_main__limit_to_ages(self):
        exposures_text = '''
qx|111
'''
        outcomes_text = '''
xx|
'''
        examples_csv_text = '''
id|date_lo|date_hi|lo|hi|len|exp|out
746|1994-08-22|2010-10-22|0|5905|5905|0|1
'''.lstrip()
        exps_file = io.StringIO(exposures_text)
        outs_file = io.StringIO(outcomes_text)
        evs_file = io.StringIO(self.events_csv_text)
        exs_file = io.StringIO()
        main_api(
            exps_file, outs_file,
            in_file=evs_file, out_file=exs_file,
            study_period_definer=lambda s: limit_to_ages(s, min_age=50),
        )
        self.maxDiff = None
        self.assertEqual(examples_csv_text, exs_file.getvalue())

    def test_main__empty_study_period(self):
        exposures_text = '''
qx|111
'''
        outcomes_text = '''
xx|
'''
        examples_csv_text = '''
id|date_lo|date_hi|lo|hi|len|exp|out
'''.lstrip()
        exps_file = io.StringIO(exposures_text)
        outs_file = io.StringIO(outcomes_text)
        evs_file = io.StringIO(self.events_csv_text)
        exs_file = io.StringIO()
        main_api(
            exps_file, outs_file,
            in_file=evs_file, out_file=exs_file,
            study_period_definer=lambda s: limit_to_ages(s, max_age=0),
        )
        self.maxDiff = None
        self.assertEqual(examples_csv_text, exs_file.getvalue())

    def test_main__feature_vector(self):
        exposures_text = '''
rx|733
'''
        outcomes_text = '''
xx|
'''
        examples_csv_text = '''
id|date_lo|date_hi|lo|hi|len|exp|out|age|sex|snp-rs6311|snp-rs6313
746|1979-11-13|2007-11-10|0|10224|10224|0|0|35.2|F||
746|2007-11-10|2010-10-22|10224|11301|1077|1|1|63.2|F||
'''.lstrip()
        exps_file = io.StringIO(exposures_text)
        outs_file = io.StringIO(outcomes_text)
        evs_file = io.StringIO(self.events_csv_text)
        exs_file = io.StringIO()
        main_api(
            exps_file, outs_file,
            in_file=evs_file, out_file=exs_file,
            record_transformer=transform_record,
            feature_vector_header=(
                'age', 'sex', 'snp-rs6311', 'snp-rs6313'),
            feature_vector_function=mk_feature_vector_function(
                age_at_first_event,
                mk_fact_feature(('bx', 'gndr')),
                mk_fact_feature(('gx', 'snp-rs6311')), # Empty
                mk_fact_feature(('gx', 'snp-rs6313')), # Empty
            )
        )
        self.maxDiff = None
        self.assertEqual(examples_csv_text, exs_file.getvalue())
