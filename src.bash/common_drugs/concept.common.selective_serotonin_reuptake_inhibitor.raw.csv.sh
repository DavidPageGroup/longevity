# Query the CDM vocabulary for concept IDs related to common SSRIs

# Usage: bash concept...sh <cdm-vocabulary-db>

# Copyright (c) 2019 Finn Kuusisto.  This is free, open software
# released under the MIT License.  (See `LICENSE.txt` for details.)

# Get the filename of the CDM vocabulary DB from the command line
vocab_db="${1}"
if [[ ! -f "${vocab_db}" ]]; then
    echo "Error: Bad CDM DB filename: '${vocab_db}'" >&2
    exit 2
fi

# Search for concepts matching a several SSRIs
sqlite3 -readonly "${vocab_db}" <<EOF
select *
from concept
where domain_id = 'Drug' and
  concept_class_id != 'Drug Interaction' and
  (
    -- I'm not going to worry about redundant names
    concept_name like '%sertraline%' or -- sertraline
    concept_name like '%sertralina%' or
    concept_name like '%sertralinum%' or
    concept_name like '%zoloft%' or
    concept_name like '%fluoxetine%' or -- fluoxetine
    concept_name like '%fluoxetina%' or
    concept_name like '%fluoxetinum%' or
    concept_name like '%fxt 10%' or
    concept_name like '%fxt 20%' or
    concept_name like '%fxt 40%' or
    concept_name like '%prozac%' or
    concept_name like '%sarafem%' or
    concept_name like '%citalopram%' or -- citalopram
    concept_name like '%nitalapram%' or
    concept_name like '%celexa%' or
    concept_name like '%escitalopram%' or -- escitalopram
    concept_name like '%cipralex%' or
    concept_name like '%lexapro%' or
    concept_name like '%paroxetine%' or -- paroxetine
    concept_name like '%paroxetina%' or
    concept_name like '%paroxetinum%' or
    concept_name like '%brisdelle%' or
    concept_name like '%paxil%' or
    concept_name like '%seroxat%' or
    concept_name like '%pexeva%'
  ) and (
    -- Exclude false positives
    concept_name not like '%paxillin%'
  )
order by domain_id, vocabulary_id, concept_id
;
EOF
