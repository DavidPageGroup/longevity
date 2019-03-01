# Query the CDM vocabulary for concept IDs related to MI

# Usage: bash concept...sh <cdm-vocabulary-db>

# Copyright (c) 2019 Finn Kuusisto.  This is free, open software
# released under the MIT License.  (See `LICENSE.txt` for details.)

# Get the filename of the CDM vocabulary DB from the command line
vocab_db="${1}"
if [[ ! -f "${vocab_db}" ]]; then
    echo "Error: Bad CDM DB filename: '${vocab_db}'" >&2
    exit 2
fi

# Search for concepts matching "stroke"
sqlite3 -readonly "${vocab_db}" <<EOF
select *
from concept
where concept_name like '%stroke%'
and concept_name not like '%history%' -- skip those regarding to past
and concept_name not like '% review%'
and concept_name not like '% following%'
and concept_name not like '%post-stroke%'
and concept_name not like '%post stroke%'
and concept_name not like '%sequela%'
and concept_name not like '%heatstroke%' -- skip heat and sun stroke
and concept_name not like '%heat stroke%'
and concept_name not like '%sunstroke%'
and concept_name not like '%sun stroke%'
and concept_name not like '%upstroke%' -- some extra specific exclusions
and concept_name not like '%stroke volume%'
and concept_name not like '%stroke work%'
and concept_name not like '%test negative%'
and concept_name not like '%delivery %'
and concept_name not like '%provision %'
and concept_name not like '%assessment %'
and concept_name not like '%management %'
and concept_name not like '%education %'
order by domain_id, vocabulary_id, concept_id
;
EOF

# Search for concepts matching "cerebrovascular accident"
sqlite3 -readonly "${vocab_db}" <<EOF
select *
from concept
where concept_name like '%cerebrovascular%accident%'
and concept_name not like '%history%' -- skip those regarding to past
and concept_name not like '% review%'
and concept_name not like '% following%'
and concept_name not like '%post-stroke%'
and concept_name not like '%post stroke%'
and concept_name not like '%sequela%'
and concept_name not like '%heatstroke%' -- skip heat and sun stroke
and concept_name not like '%heat stroke%'
and concept_name not like '%sunstroke%'
and concept_name not like '%sun stroke%'
and concept_name not like '%upstroke%' -- some extra specific exclusions
and concept_name not like '%stroke volume%'
and concept_name not like '%stroke work%'
and concept_name not like '%test negative%'
and concept_name not like '%delivery %'
and concept_name not like '%provision %'
and concept_name not like '%assessment %'
and concept_name not like '%management %'
and concept_name not like '%education %'
order by domain_id, vocabulary_id, concept_id
;
EOF

# Select the concepts for the MI SNOMED IDs Finn selected
#sqlite3 -readonly /z/Proj/mcrf/sqlite_dbs/vcb.sqlite <<EOF
#create temporary table mi (id int);
#.import finns_mi_hierarchy_snomed_ids.csv mi
#
#select *
#from concept
#where concept_code in mi
# order by domain_id, vocabulary_id, concept_id
#;
#EOF

