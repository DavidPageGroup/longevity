# Query the CDM vocabulary for concept IDs related to common statins

# Usage: bash concept...sh <cdm-vocabulary-db>

# Copyright (c) 2019 Finn Kuusisto.  This is free, open software
# released under the MIT License.  (See `LICENSE.txt` for details.)

# Get the filename of the CDM vocabulary DB from the command line
vocab_db="${1}"
if [[ ! -f "${vocab_db}" ]]; then
    echo "Error: Bad CDM DB filename: '${vocab_db}'" >&2
    exit 2
fi

# Search for concepts matching common statins
sqlite3 -readonly "${vocab_db}" <<EOF
select *
from concept
where domain_id = 'Drug' and
  concept_class_id != 'Drug Interaction' and
  (
    -- These are all the synonyms for statins.  I'm not going to worry
    -- about redundant names.
    concept_name like '%atorvastatin%' or -- atorvastatin
    concept_name like '%lipitor%' or
    concept_name like '%simvastatin%' or -- simvastatin
    concept_name like '%simvastin%' or  -- misspelling
    concept_name like '%flolipid%' or
    concept_name like '%zocor%' or
    concept_name like '%pravastatin%' or -- pravastatin
    concept_name like '%pravachol%' or
    concept_name like '%rosuvastatin%' or -- rosuvastatin
    concept_name like '%crestor%' or
    concept_name like '%lovastatin%' or -- lovastatin
    concept_name like '%mevinolin%' or
    concept_name like '%altoprev%' or
    concept_name like '%mevacor%' or
    concept_name like '%pitavastatin%' or -- pitavastatin
    concept_name like '%livalo%' or
    concept_name like '%zypitamag%'
--  ) and (
    -- Exclude major categories of false positives
  )
order by domain_id, vocabulary_id, concept_id
;
EOF
