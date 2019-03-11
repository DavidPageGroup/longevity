How to run survival analysis
============================


This is how I have been running the survival analysis in a documented
and reproducible way.  This assumes you have EMR event data in CSV form
[1] and have already defined your exposure and outcome IDs as instructed
in `src.bash/README.md`.

0. Install `barnapy` by following the instructions at
   https://github.com/afbarnard/barnapy.

1. Optional: Copy and modify `mk_data.<data-number>.<covariates>.py` to
   define your survival analysis data.  Each new set of data decisions
   (a set of arguments to `survival_data.py:main_api`) should get a new
   data number.  Document what the number means in `CONTENTS.md`.

2. Make an appropriate experimental directory like
   `.../longevity-experiments/statins_vs_mi` and go there.

3. Define the exposure and outcome IDs for this set of experiments.

       cat .../longevity/ids/ids.statins.csv > exp_ids.statins.csv
       cat .../longevity/ids/ids.mi.csv .../longevity/ids/ids.xx.csv > out_ids.mi_xx.csv

4. Make the survival analysis data by running a command similar to the
   following:

       xzcat ev.csv.xz | python3 ~/repos/dpg/longevity/src.py/mk_data.01.w_age_sex.py exp_ids.statins.csv out_ids.mi_xx.csv 1>data.01.statins-mi_xx.w_age_sex.csv 2>data.01.statins-mi_xx.w_age_sex.csv.$(date +'%Y%m%d-%H%M%S').log &

   This may take many hours (so use `nohup` or `disown` the process).
   When it finishes, check the log to make sure it says "Done
   \`main_api\`".  If that message is not present, the process did not
   finish correctly.

5. Optional: Copy and modify
   `survival_analysis.<data-number>.<covariates>.R` to match
   `mk_data.<data-number>.<covariates>.py`.

6. Run the survival analysis.

       Rscript ~/repos/dpg/longevity/src.R/survival_analysis.01.w_age_sex.R data.01.statins-mi_xx.w_age_sex.csv &> survival_analysis_results.01.statins-mi_xx.w_age_sex.txt


[1] See [`tables_evs.sqlite.sql`](
    https://github.com/DavidPageGroup/cdm-data/blob/master/sql/tables_evs.sqlite.sql)
    and [`dump_events.sqlite.sh`](
    https://github.com/DavidPageGroup/cdm-data/blob/master/bash/dump_events.sqlite.sh).
