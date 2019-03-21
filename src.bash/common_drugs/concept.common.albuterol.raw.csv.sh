# Query the CDM vocabulary for concept IDs related to albuterol

# Usage: bash concept...sh <cdm-vocabulary-db>

# Copyright (c) 2019 Finn Kuusisto.  This is free, open software
# released under the MIT License.  (See `LICENSE.txt` for details.)

# Get the filename of the CDM vocabulary DB from the command line
vocab_db="${1}"
if [[ ! -f "${vocab_db}" ]]; then
    echo "Error: Bad CDM DB filename: '${vocab_db}'" >&2
    exit 2
fi

# Search for concepts matching albuterol
sqlite3 -readonly "${vocab_db}" <<EOF
select *
from concept
where domain_id = 'Drug' and
  concept_class_id != 'Drug Interaction' and
  (
    -- I'm not going to worry about redundant names
    concept_name like '%albuterol%' or -- albuterol
    concept_name like '%salbutamol%' or
    concept_name like '%accuneb%' or
    concept_name like '%airomir%' or
    concept_name like '%asmavent%' or
    concept_name like '%proair%' or
    concept_name like '%proventil%' or
    concept_name like '%salbulin%' or
    concept_name like '%salbu-2%' or
    concept_name like '%salbu-4%' or
    concept_name like '%ventodisk%' or
    concept_name like '%ventolin%' or
    concept_name like '%apo-salvent%' or
    concept_name like '%novo-salmol%' or
    concept_name like '%vospire%'
--  ) and (
    -- Exclude false positives
  )
order by domain_id, vocabulary_id, concept_id
;
EOF
