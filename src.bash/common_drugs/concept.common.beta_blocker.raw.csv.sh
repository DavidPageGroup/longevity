# Query the CDM vocabulary for concept IDs related to common beta blockers

# Usage: bash concept...sh <cdm-vocabulary-db>

# Copyright (c) 2019 Finn Kuusisto.  This is free, open software
# released under the MIT License.  (See `LICENSE.txt` for details.)

# Get the filename of the CDM vocabulary DB from the command line
vocab_db="${1}"
if [[ ! -f "${vocab_db}" ]]; then
    echo "Error: Bad CDM DB filename: '${vocab_db}'" >&2
    exit 2
fi

# Search for concepts matching the beta blockers
sqlite3 -readonly "${vocab_db}" <<EOF
select *
from concept
where domain_id = 'Drug' and
  concept_class_id != 'Drug Interaction' and
  (
    -- I'm not going to worry about redundant names
    concept_name like '%metoprolol%' or -- metoprolol
    concept_name like '%betaloc%' or
    concept_name like '%kapspargo%' or
    concept_name like '%lopresor%' or
    concept_name like '%lopressor%' or
    concept_name like '%toprol%' or
    concept_name like '%atenolol%' or -- atenolol
    concept_name like '%atenol%' or
    concept_name like '%tenormin%' or
    concept_name like '%propranolol%' or -- propranolol
    concept_name like '%propranalol%' or
    concept_name like '%detensol%' or
    concept_name like '%hemangeol%' or
    concept_name like '%hemangiol%' or
    concept_name like '%inderal%' or
    concept_name like '%innopran%' or
    concept_name like '%novo-pranol%' or
    concept_name like '%nebivolol%' or -- nebivolol
    concept_name like '%narbivolol%' or
    concept_name like '%bystolic%' or
    concept_name like '%acebutolol%' or -- acebutolol
    concept_name like '%monitan%' or
    concept_name like '%rhotral%' or
    concept_name like '%sectral%' or
    concept_name like '%bisoprolol%' or -- bisoprolol
    concept_name like '%monocor%' or
    concept_name like '%zebeta%' or
    concept_name like '%nadolol%' or -- nadolol
    concept_name like '%corgard%'
  ) and (
    -- Exclude false positives
    concept_name not like '%leptoprol%' and
--okay    concept_name not like '%jenatenol%' and
--okay    concept_name not like '%duratenol%' and
--okay    concept_name not like '%nifatenol%' and
    concept_name not like '%dispatenol%' and
    concept_name not like '%monocortin%'
  )
order by domain_id, vocabulary_id, concept_id
;
EOF
