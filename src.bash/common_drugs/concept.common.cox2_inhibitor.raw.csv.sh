# Query the CDM vocabulary for concept IDs related to common COX-2 inhibitors

# Usage: bash concept...sh <cdm-vocabulary-db>

# Copyright (c) 2019 Finn Kuusisto.  This is free, open software
# released under the MIT License.  (See `LICENSE.txt` for details.)

# Get the filename of the CDM vocabulary DB from the command line
vocab_db="${1}"
if [[ ! -f "${vocab_db}" ]]; then
    echo "Error: Bad CDM DB filename: '${vocab_db}'" >&2
    exit 2
fi

# Search for concepts matching common COX-2 inhibitors
sqlite3 -readonly "${vocab_db}" <<EOF
select *
from concept
where domain_id = 'Drug' and
  concept_class_id != 'Drug Interaction' and
  (
    concept_name like '%celecoxib%' or -- celecoxib
    concept_name like '%celebrex%' or
    concept_name like '%capxib%' or
    concept_name like '%lidoxib%' or
    concept_name like '%articox%' or
    concept_name like '%articoxib%' or
    concept_name like '%artilog%' or
    concept_name like '%artix%' or
    concept_name like '%artixib%' or
    concept_name like '%blockten%' or
    concept_name like '%caditar%' or
    concept_name like '%cefinix%' or
    concept_name like '%celact%' or
    concept_name like '%celebra%' or
    concept_name like '%onsenal%' or
    concept_name like '%valdyne%' or
    concept_name like '%rofecoxib%' or -- rofecoxib
    concept_name like '%vioxx%' or
    concept_name like '%valdecoxib%' or -- valdecoxib
    concept_name like '%bextra%' or
    concept_name like '%etoricoxib%' or -- etoricoxib
    concept_name like '%algix%' or
    concept_name like '%arcoxia%' or
    concept_name like '%coxyveen%' or
    concept_name like '%etorix%' or
    concept_name like '%nucoxia%' or
    concept_name like '%tauxib%'
  ) and (
    -- Exclude false positives
    concept_name not like '%celebration%'
  )
order by domain_id, vocabulary_id, concept_id
;
EOF
