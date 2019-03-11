# Query the CDM vocabulary for concept IDs related to ACE inhibitors

# Usage: bash concept...sh <cdm-vocabulary-db>

# Copyright (c) 2019 Finn Kuusisto.  This is free, open software
# released under the MIT License.  (See `LICENSE.txt` for details.)

# Get the filename of the CDM vocabulary DB from the command line
vocab_db="${1}"
if [[ ! -f "${vocab_db}" ]]; then
    echo "Error: Bad CDM DB filename: '${vocab_db}'" >&2
    exit 2
fi

# Search for concepts matching a bunch of ACE inhibitors
sqlite3 -readonly "${vocab_db}" <<EOF
select *
from concept
where domain_id = 'Drug' and
  concept_class_id != 'Drug Interaction' and
  (
    -- I'm not going to worry about redundant names
    concept_name like '%captopril%' or -- captopril
    concept_name like '%captopryl%' or
    concept_name like '%capoten%' or
    concept_name like '%lopirin%' or
    concept_name like '%zofenopril%' or -- zofenopril
    concept_name like '%enalapril%' or -- enalapril
    concept_name like '%ramipril%' or -- ramipril
    concept_name like '%altace%' or
    concept_name like '%ramace%' or
    concept_name like '%quinapril%' or -- quinapril
    concept_name like '%accupril%' or
    concept_name like '%perindopril%' or -- perindopril
    concept_name like '%aceon%' or
    concept_name like '%arcosyl%' or
    concept_name like '%coversyl%' or
    concept_name like '%lisinopril%' or -- lisinopril
    concept_name like '%prinivil%' or
    concept_name like '%qbrelis%' or
    concept_name like '%zestril%' or
    concept_name like '%benazepril%' or -- benazepril
    concept_name like '%lotensin%' or
    concept_name like '%imidapril%' or -- imidapril
    concept_name like '%trandolapril%' or -- trandolapril
    concept_name like '%mavik%' or
    concept_name like '%cilazapril%' or -- cilazapril
    concept_name like '%inhibace%' or
    concept_name like '%fosinopril%' or -- fosinopril
    concept_name like '%monopril%' or
    concept_name like '%moexipril%' or -- moexipril
    concept_name like '%univasc%' or
    concept_name like '%spirapril%' or -- spirapril
    concept_name like '%renormax%' or
    concept_name like '%rescinnamine%' or -- rescinnamine
    concept_name like '%moderil%' or
    concept_name like '%cinnasil%' or
    concept_name like '%anaprel%'
--  ) and (
    -- Exclude false positives
    -- concept_name not like '%cobimetinib%'
  )
order by domain_id, vocabulary_id, concept_id
;
EOF
