# Query the CDM vocabulary for concept IDs related to common ACE inhibitors

# Usage: bash concept...sh <cdm-vocabulary-db>

# Copyright (c) 2019 Finn Kuusisto.  This is free, open software
# released under the MIT License.  (See `LICENSE.txt` for details.)

# Get the filename of the CDM vocabulary DB from the command line
vocab_db="${1}"
if [[ ! -f "${vocab_db}" ]]; then
    echo "Error: Bad CDM DB filename: '${vocab_db}'" >&2
    exit 2
fi

# Search for concepts matching a several of ACE inhibitors
sqlite3 -readonly "${vocab_db}" <<EOF
select *
from concept
where domain_id = 'Drug' and
  concept_class_id != 'Drug Interaction' and
  (
    -- I'm not going to worry about redundant names
    concept_name like '%lisinopril%' or -- lisinopril
    concept_name like '%prinivil%' or
    concept_name like '%qbrelis%' or
    concept_name like '%zestril%' or
    concept_name like '%enalapril%' or -- enalapril
    concept_name like '%benazepril%' or -- benazepril
    concept_name like '%lotensin%' or
    concept_name like '%ramipril%' or -- ramipril
    concept_name like '%altace%' or
    concept_name like '%ramace%'
  ) and (
    -- Exclude false positives
    concept_name not like '%tramacet%'
  )
order by domain_id, vocabulary_id, concept_id
;
EOF
