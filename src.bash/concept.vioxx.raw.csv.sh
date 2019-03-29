# Query the CDM vocabulary for concept IDs related to Vioxx and generic

# Usage: bash concept...sh <cdm-vocabulary-db>

# Copyright (c) 2019 Finn Kuusisto.  This is free, open software
# released under the MIT License.  (See `LICENSE.txt` for details.)

# Get the filename of the CDM vocabulary DB from the command line
vocab_db="${1}"
if [[ ! -f "${vocab_db}" ]]; then
    echo "Error: Bad CDM DB filename: '${vocab_db}'" >&2
    exit 2
fi

# Search for concepts matching "vioxx"
sqlite3 -readonly "${vocab_db}" <<EOF
select *
from concept
where domain_id = 'Drug' and
  concept_class_id != 'Drug Interaction' and
  (
    -- I'm not going to worry about redundant names
    concept_name like '%vioxx%' or
    concept_name like '%rofecoxib%'
--  ) and (
    -- Exclude false positives
    --concept_name not like '%cobimetinib%'
  )
order by domain_id, vocabulary_id, concept_id
;
EOF
