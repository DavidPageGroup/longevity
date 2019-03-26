# Query the CDM vocabulary for concept IDs related to common CCBs

# Usage: bash concept...sh <cdm-vocabulary-db>

# Copyright (c) 2019 Finn Kuusisto.  This is free, open software
# released under the MIT License.  (See `LICENSE.txt` for details.)

# Get the filename of the CDM vocabulary DB from the command line
vocab_db="${1}"
if [[ ! -f "${vocab_db}" ]]; then
    echo "Error: Bad CDM DB filename: '${vocab_db}'" >&2
    exit 2
fi

# Search for concepts matching the CCBs
sqlite3 -readonly "${vocab_db}" <<EOF
select *
from concept
where domain_id = 'Drug' and
  concept_class_id != 'Drug Interaction' and
  (
    -- I'm not going to worry about redundant names
    concept_name like '%amlodipine%' or -- amlodipine
    concept_name like '%amlodipino%' or
    concept_name like '%amlodipinum%' or
    concept_name like '%copalia%' or
    concept_name like '%norvasc%' or
    concept_name like '%nifedipine%' or -- nifedipine
    concept_name like '%nifedipino%' or
    concept_name like '%nifedipinum%' or
    concept_name like '%adalat%' or
    concept_name like '%procardia%' or
    concept_name like '%afeditab%' or
    concept_name like '%nifediac%' or
    concept_name like '%verapamil%' or -- verapamil
    concept_name like '%calan%' or
    concept_name like '%covera-hs%' or
    concept_name like '%isoptin%' or
    concept_name like '%verelan%' or
    concept_name like '%apo-verap%' or
    concept_name like '%novo-veramil%' or
    concept_name like '%nu-verap%' or
    concept_name like '%diltiazem%' or -- diltiazem
    concept_name like '%diltiaz%' or
    concept_name like '%cardizem%' or
    concept_name like '%dilacor%' or
    concept_name like '%tiazac%' or
    concept_name like '%cartia xt%' or
    concept_name like '%dilt-cd%' or
    concept_name like '%diltia xt%' or
    concept_name like '%diltizac%' or
    concept_name like '%matzim%' or
    concept_name like '%taztia xt%' or
    concept_name like '%tiadylt er%' or
    concept_name like '%felodipine%' or -- felodipine
    concept_name like '%felodipina%' or
    concept_name like '%felodipino%' or
    concept_name like '%felodipinum%' or
    concept_name like '%plendil%' or
    concept_name like '%renedil%' or
    concept_name like '%isradipine%' or -- isradipine
    concept_name like '%isradipino%' or
    concept_name like '%isradipinum%' or
    concept_name like '%dynacirc%' or
    concept_name like '%prescal%' or
    concept_name like '%nicardipine%' or -- nicardipine
    concept_name like '%nicardipino%' or
    concept_name like '%nicardipinum%' or
    concept_name like '%cardene%' or
    concept_name like '%nisoldipine%' or -- nisoldipine
    concept_name like '%nisoldipin%' or
    concept_name like '%sular%' or
--  ) and (
    -- Exclude false positives
  )
order by domain_id, vocabulary_id, concept_id
;
EOF
