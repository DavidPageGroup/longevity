# Query the CDM vocabulary for concept IDs related to guanfacine

# Usage: bash concept...sh <cdm-vocabulary-db>

# Copyright (c) 2019 Finn Kuusisto.  This is free, open software
# released under the MIT License.  (See `LICENSE.txt` for details.)

# Get the filename of the CDM vocabulary DB from the command line
vocab_db="${1}"
if [[ ! -f "${vocab_db}" ]]; then
    echo "Error: Bad CDM DB filename: '${vocab_db}'" >&2
    exit 2
fi

# Search for concepts matching guanfacine
sqlite3 -readonly "${vocab_db}" <<EOF
select *
from concept
where domain_id = 'Drug' and
  concept_class_id != 'Drug Interaction' and
  (
    -- I'm not going to worry about redundant names
    concept_name like '%guanfacine%' or
    concept_name like '%guanfacina%' or
    concept_name like '%guanfacinum%' or
    concept_name like '%intuniv%' or
    concept_name like '%tenex%' or
    concept_name like '%estulic%'
  ) and (
    -- Exclude false positives
    concept_name not like '%antenex%' and
    concept_name not like '%lightenex%' and
    concept_name not like '%neltenexine%'
  )
order by domain_id, vocabulary_id, concept_id
;
EOF
