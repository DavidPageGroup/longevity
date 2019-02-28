# Query the CDM vocabulary for concept IDs related to MI

# Usage: bash concept...sh <cdm-vocabulary-db>

# Copyright (c) 2018 Aubrey Barnard.  This is free, open software
# released under the MIT License.  (See `LICENSE.txt` for details.)

# Get the filename of the CDM vocabulary DB from the command line
vocab_db="${1}"
if [[ ! -f "${vocab_db}" ]]; then
    echo "Error: Bad CDM DB filename: '${vocab_db}'" >&2
    exit 2
fi

# Search for concepts matching "myocardial infarction"
sqlite3 -readonly "${vocab_db}" <<EOF
select *
from concept
where concept_name like '%myocardial%infarction%'
order by domain_id, vocabulary_id, concept_id
;
EOF

# Search for concepts matching "heart attack"
sqlite3 -readonly "${vocab_db}" <<EOF
select *
from concept
where concept_name like '%heart%attack%'
order by domain_id, vocabulary_id, concept_id
;
EOF

# Select the concepts for the MI SNOMED IDs Finn selected
sqlite3 -readonly "${vocab_db}" <<EOF
create temporary table mi (id int);
.import finns_mi_hierarchy_snomed_ids.csv mi

select *
from concept
where concept_code in mi
order by domain_id, vocabulary_id, concept_id
;
EOF
