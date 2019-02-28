# Query the CDM vocabulary for concept IDs related to atorvastatin

# Usage: bash concept...sh <cdm-vocabulary-db>

# Copyright (c) 2019 Aubrey Barnard.  This is free, open software
# released under the MIT License.  (See `LICENSE.txt` for details.)

# Get the filename of the CDM vocabulary DB from the command line
vocab_db="${1}"
if [[ ! -f "${vocab_db}" ]]; then
    echo "Error: Bad CDM DB filename: '${vocab_db}'" >&2
    exit 2
fi

# Search for concepts matching "atorvastatin"
sqlite3 -readonly "${vocab_db}" <<EOF
select *
from concept
where concept_name like '%atorvastatin%'
  and domain_id = 'Drug'
order by domain_id, vocabulary_id, concept_id
;
EOF
