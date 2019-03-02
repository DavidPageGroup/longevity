# Generate survival data that includes age and sex as covariates

# Copyright (c) 2018 Aubrey Barnard.  This is free, open software
# released under the MIT License.  (See `LICENSE.txt` for details.)

# Run like: /usr/bin/time -v xzcat ev.csv.xz | /usr/bin/time -v python3 mk_data.py exp_ids.csv out_ids.csv 1>data.csv 2>data.csv.$(date +'%Y%m%d-%H%M%S').log


import datetime
import pathlib
import sys

from barnapy import logging

# "Install" related modules by updating import path
this_dir = pathlib.Path(__file__).absolute().parent
sys.path.append(str(this_dir))

import survival_data


# Configuration

# Starting tracking survival at age 30
initial_age = 30

# TODO discard patients with outcome before start age?
# TODO washout?

# Amount of time between exposure or outcome events and still consider
# part of a single era
era_max_gap = datetime.timedelta(days=360)


# Data processing

logging.default_config()
logging.log_runtime_environment(logging.getLogger(__name__))

survival_data.main_api(
    # Read exposures and outcomes from command line
    *sys.argv[1:],

    # Data filtering

    # Include only the relevant tables (event types)
    include_tables={'bx', 'rx', 'dx', 'xx'},
    # Discard person table rows and medication mentions
    include_record=survival_data.include_record,

    # Data interpretation and transformation

    # Infer drug intervals based on refills, etc.
    record_transformer=survival_data.transform_record,
    # Define exposure / outcome eras
    era_max_gap=era_max_gap,
    # Start tracking survival at the given age
    study_period_definer=lambda s: (
        survival_data.limit_to_ages(s, min_age=initial_age)),

    # Covariates

    feature_vector_header=('age', 'sex'),
    feature_vector_function=survival_data.mk_feature_vector_function(
        survival_data.age_at_first_event,
        survival_data.mk_fact_feature(('bx', 'gndr')),
    ),
)
