# Query the CDM vocabulary for concept IDs related to methylphenidate

# Usage: bash concept...sh <cdm-vocabulary-db>

# Copyright (c) 2019 Finn Kuusisto.  This is free, open software
# released under the MIT License.  (See `LICENSE.txt` for details.)

# Get the filename of the CDM vocabulary DB from the command line
vocab_db="${1}"
if [[ ! -f "${vocab_db}" ]]; then
    echo "Error: Bad CDM DB filename: '${vocab_db}'" >&2
    exit 2
fi

# Search for concepts matching methylphenidate
sqlite3 -readonly "${vocab_db}" <<EOF
select *
from concept
where domain_id = 'Drug' and
  concept_class_id != 'Drug Interaction' and
  (
    -- I'm not going to worry about redundant names
    concept_name like '%methylphenidate%' or
    concept_name like '%methylphenidan%' or
    concept_name like '%methylphenidatum%' or
    concept_name like '%metilfenidato%' or
    concept_name like '%aptensio%' or
    concept_name like '%biphentin%' or
    concept_name like '%concerta%' or
    concept_name like '%cotempla%' or
    concept_name like '%daytrana%' or
    concept_name like '%foquest%' or
    concept_name like '%metadate%' or
    concept_name like '%methylin%' or
    concept_name like '%quillichew%' or
    concept_name like '%quillivant%' or
    concept_name like '%ritalin%' or
    concept_name like '%relexxii%' or
    concept_name like '%equasym%' or
    concept_name like '%medikinet%' or
    concept_name like '%riphenidate%' or
    concept_name like '%rubifen%'
  ) and (
    -- Exclude false positives
    concept_name not like '%methylinositol%' and
    concept_name not like '%hexamethylindanopyran%' and
    concept_name not like '%dimethoxydimethylindanone%' and
    concept_name not like '%dexmethylphenidate%' -- let's exclude the dextro form - focalin
  )
order by domain_id, vocabulary_id, concept_id
;
EOF
