# Query the CDM vocabulary for concept IDs related to all statins

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
where domain_id = 'Drug' and
  concept_class_id != 'Drug Interaction' and
  (
    -- These are all the synonyms for statins.  I'm not going to worry
    -- about redundant names.
    concept_name like '%atorvastatin%' or
    concept_name like '%atorlip%' or
    concept_name like '%atorva%' or
    concept_name like '%atorvachol%' or
    concept_name like '%atorvasa%' or
    concept_name like '%atorvastacalc%' or
    concept_name like '%lipitor%' or
    concept_name like '%cerivastatin%' or
    concept_name like '%baycol%' or
    concept_name like '%lipobay%' or
    concept_name like '%fluvastatin%' or
    concept_name like '%canef%' or
    concept_name like '%lescol%' or
    concept_name like '%vastin%' or
    concept_name like '%lovastatin%' or
    concept_name like '%altocor%' or
    concept_name like '%altoprev%' or
    concept_name like '%mevacor%' or
    concept_name like '%mevinolin%' or
    concept_name like '%monacolin%' or
    concept_name like '%pitavastatin%' or
    concept_name like '%livalo%' or
    concept_name like '%livazo%' or
    concept_name like '%pitava%' or
    concept_name like '%pravastatin%' or
    concept_name like '%lipostat%' or
    concept_name like '%pravachol%' or
    concept_name like '%selektine%' or
    concept_name like '%rosuvastatin%' or
    concept_name like '%crestor%' or
    concept_name like '%rosulip%' or
    concept_name like '%zuvamor%' or
    concept_name like '%simvastatin%' or
    concept_name like '%simvastin%' or  -- misspelling
    concept_name like '%flolipid%' or
    concept_name like '%lipex%' or
    concept_name like '%zocor%'
  ) and (
    -- Exclude major categories of false positives
    concept_name not like '%avastin%' and
    concept_name not like '%bevacizumab%' and
    concept_name not like '%acrivastine%'
  )
order by domain_id, vocabulary_id, concept_id
;
EOF

# Search for the following keywords to eliminate false positives:
# avastin (chemotherapy)
# bevacizumab (chemotherapy)
# acrivastine (antihistamine)
# capsicum (supplement)
# monascus purpureus (allow? no. supplement: not standardized or supervised)
# monacolin
# aspirin (seems commonly available with pravastatin)
# niacin (seems commonly available with simvastatin)
# ezetimibe (cholesterol reduction, commonly available with simvastatin)
# fenofibrate (cholesterol reduction)
# ramipril, *pril (ACE inhibitors)
# sitagliptin (antihyperglycemic)
# amlodipine (calcium channel blocker: antihypertensive)
# acetylsalicylic acid (aspirin)
# drug interaction
# linolenate
# lipostat
# otc drug
