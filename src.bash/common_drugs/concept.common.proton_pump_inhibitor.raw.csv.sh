# Query the CDM vocabulary for concept IDs related to common PPIs

# Usage: bash concept...sh <cdm-vocabulary-db>

# Copyright (c) 2019 Finn Kuusisto.  This is free, open software
# released under the MIT License.  (See `LICENSE.txt` for details.)

# Get the filename of the CDM vocabulary DB from the command line
vocab_db="${1}"
if [[ ! -f "${vocab_db}" ]]; then
    echo "Error: Bad CDM DB filename: '${vocab_db}'" >&2
    exit 2
fi

# Search for concepts matching common PPIs
sqlite3 -readonly "${vocab_db}" <<EOF
select *
from concept
where domain_id = 'Drug' and
  concept_class_id != 'Drug Interaction' and
  (
    concept_name like '%omeprazole%' or -- omeprazole
    concept_name like '%omeprazol%' or
    concept_name like '%losec%' or
    concept_name like '%prilosec%' or
    concept_name like '%esomeprazole%' or -- esomeprazole
    concept_name like '%esomeprazol%' or
    concept_name like '%perprazole%' or
    concept_name like '%nexium%' or
    concept_name like '%lansoprazole%' or -- lansoprazole
    concept_name like '%lansoprazol%' or
    concept_name like '%prevacid%' or
    concept_name like '%dexlansoprazole%' or -- dexlansoprazole
    concept_name like '%dexilant%' or
    concept_name like '%kapidex%' or
    concept_name like '%pantoprazole%' or -- pantoprazole
    concept_name like '%pantoprazol%' or
    concept_name like '%controloc control%' or
    concept_name like '%panto iv%' or
    concept_name like '%panto-byk%' or
    concept_name like '%pantozol%' or
    concept_name like '%protonix%' or
    concept_name like '%somac control%' or
    concept_name like '%tecta%' or
    concept_name like '%rabeprazole%' or -- rabeprazole
    concept_name like '%aciphex%'
  ) and (
    -- Exclude false positives
    concept_name not like '%secnidazole%' and
    concept_name not like '%solosec%' and
    concept_name not like '%protecta%' and
    concept_name not like '%mucotectan%'
  )
order by domain_id, vocabulary_id, concept_id
;
EOF
