# Query the CDM vocabulary for concept IDs related to gabapentinoids

# Usage: bash concept...sh <cdm-vocabulary-db>

# Copyright (c) 2019 Finn Kuusisto.  This is free, open software
# released under the MIT License.  (See `LICENSE.txt` for details.)

# Get the filename of the CDM vocabulary DB from the command line
vocab_db="${1}"
if [[ ! -f "${vocab_db}" ]]; then
    echo "Error: Bad CDM DB filename: '${vocab_db}'" >&2
    exit 2
fi

# Search for concepts matching the gabapentinoids
sqlite3 -readonly "${vocab_db}" <<EOF
select *
from concept
where domain_id = 'Drug' and
  concept_class_id != 'Drug Interaction' and
  (
    -- I'm not going to worry about redundant names
    concept_name like '%gabapentin%' or -- gabapentin
    concept_name like '%neurontin%' or
    concept_name like '%gralise%' or
    concept_name like '%pregabalin%' or -- pregabalin
    concept_name like '%lyrica%'
--  ) and (
    -- Exclude false positives
  )
order by domain_id, vocabulary_id, concept_id
;
EOF
