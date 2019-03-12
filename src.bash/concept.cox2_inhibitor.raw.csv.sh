# Query the CDM vocabulary for concept IDs related to COX-2 inhibitors

# Usage: bash concept...sh <cdm-vocabulary-db>

# Copyright (c) 2019 Finn Kuusisto.  This is free, open software
# released under the MIT License.  (See `LICENSE.txt` for details.)

# Get the filename of the CDM vocabulary DB from the command line
vocab_db="${1}"
if [[ ! -f "${vocab_db}" ]]; then
    echo "Error: Bad CDM DB filename: '${vocab_db}'" >&2
    exit 2
fi

# Search for concepts matching COX-2 inhibitors
sqlite3 -readonly "${vocab_db}" <<EOF
select *
from concept
where domain_id = 'Drug' and
  concept_class_id != 'Drug Interaction' and
  (
    concept_name like '%celecoxib%' or -- celecoxib
    concept_name like '%celebrex%' or
    concept_name like '%capxib%' or
    concept_name like '%lidoxib%' or
    concept_name like '%articox%' or
    concept_name like '%articoxib%' or
--    concept_name like '%artiflex%' or -- overloaded name - no good matches
    concept_name like '%artilog%' or
    concept_name like '%artix%' or
    concept_name like '%artixib%' or
    concept_name like '%blockten%' or
    concept_name like '%caditar%' or
    concept_name like '%cefinix%' or
    concept_name like '%celact%' or
    concept_name like '%celebra%' or
    concept_name like '%onsenal%' or
    concept_name like '%valdyne%' or
    concept_name like '%rofecoxib%' or -- rofecoxib
    concept_name like '%vioxx%' or
    concept_name like '%valdecoxib%' or -- valdecoxib
    concept_name like '%bextra%' or
    concept_name like '%lumiracoxib%' or -- lumiracoxib
    concept_name like '%prexige%' or
    concept_name like '%etoricoxib%' or -- etoricoxib
    concept_name like '%algix%' or
    concept_name like '%arcoxia%' or
    concept_name like '%coxyveen%' or
    concept_name like '%etorix%' or
    concept_name like '%nucoxia%' or
    concept_name like '%tauxib%' or
    concept_name like '%parecoxib%' or -- parecoxib
    concept_name like '%dynastat%' or
    concept_name like '%nabumetone%' or -- nabumetone
    concept_name like '%nabumeton%' or
    concept_name like '%relafen%' or
    concept_name like '%arthaxan%' or
    concept_name like '%balmox%' or
    concept_name like '%dolsinal%' or
    concept_name like '%listran%' or
    concept_name like '%mebutan%' or
    concept_name like '%nabuser%' or
    concept_name like '%relif%' or
    concept_name like '%relifen%' or
    concept_name like '%relifex%' or
    concept_name like '%etodolac%' or -- etodolac
    concept_name like '%lodine%' or
    concept_name like '%ultradol%' or
    concept_name like '%bodopine%' or
    concept_name like '%dolarit%' or
    concept_name like '%dolchis%' or
    concept_name like '%doloc%' or
    concept_name like '%dualgan%' or
    concept_name like '%eccoxolac%' or
    concept_name like '%edolar fort%' or
    concept_name like '%edopain%' or
--    concept_name like '%elac%' or -- too many false positives to be useful
    concept_name like '%elderin%' or
--    concept_name like '%eric%' or -- too many false positives to be useful
    concept_name like '%esodax%' or
    concept_name like '%etodin%' or
    concept_name like '%etodol%' or
    concept_name like '%etoflam%' or
    concept_name like '%etol fort%' or
    concept_name like '%etolac%' or
    concept_name like '%etomax%' or
    concept_name like '%etonox%' or
    concept_name like '%etopan%' or
    concept_name like '%etopin%'
  ) and (
    -- Exclude false positives
    concept_name not like '%celebration%' and
    concept_name not like '%itch relif%' and
    concept_name not like '%pain relif%' and
    concept_name not like '%purelife%' and
    concept_name not like '%betamethasone%' and
    concept_name not like '%relifor%' and
    concept_name not like '%dolocodon%' and
    concept_name not like '%dolocupin%' and
    concept_name not like '%artelac%' and
    concept_name not like '%relacon%' and
    concept_name not like '%melacine%' and
    concept_name not like '%melaclear%' and
    concept_name not like '%gelactiv%' and
    concept_name not like '%delactic%' and
    concept_name not like '%stelactiv%' and
    concept_name not like '%surelac%' and
    concept_name not like '%loperamide%' and
    concept_name not like '%ass elac%' and
    concept_name not like '%relacta%' and
    concept_name not like '%ketodine%' and
    concept_name not like '%acetolactate%' and
    concept_name not like '%ketomax%' and
    concept_name not like '%metomax%' and
    concept_name not like '%ketopine%'
  )
order by domain_id, vocabulary_id, concept_id
;
EOF
