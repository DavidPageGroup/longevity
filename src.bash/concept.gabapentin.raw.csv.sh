# Query the CDM vocabulary for concept IDs related to gabapentin

# Usage: bash concept...sh <cdm-vocabulary-db>

# Copyright (c) 2019 Aubrey Barnard.
#
# This is free, open software released under the MIT License.  (See
# `LICENSE.txt` for details.)

# Get the filename of the CDM vocabulary DB from the command line
vocab_db="${1}"
if [[ ! -f "${vocab_db}" ]]; then
    echo "Error: Bad CDM DB filename: '${vocab_db}'" >&2
    exit 2
fi

# Search for concepts matching generic and grand names
sqlite3 -readonly "${vocab_db}" <<EOF
select *
from concept
where domain_id = 'Drug' and
  concept_class_id != 'Drug Interaction' and
  (
    concept_name like '%gabapentin%' or
    concept_name like '%neurontin%' or
    concept_name like '%gralise%' or
    concept_name like '%horizant%' or
    concept_name like '%neuraptine%'
  )
order by domain_id, vocabulary_id, concept_id
;
EOF

# Run the following command to search for false positives:
# $ grep -iv -e '\<\(gabapentin\|neurontin\|gralise\|horizant\|neuraptine\)\>' <drug-csv> | less
