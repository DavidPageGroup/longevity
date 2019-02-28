# Extract (table, id) pairs from concepts in literal CSV format.  Map
# `domain_id` to EMR table abbreviation.

# Usage: bash concept2id.sh <concepts-csv>

# Copyright (c) 2019 Aubrey Barnard.  This is free, open software
# released under the MIT License.  (See `LICENSE.txt` for details.)

# Get the filename of the CDM vocabulary DB from the command line
concepts_csv="${1}"
if [[ ! -f "${concepts_csv}" ]]; then
    echo "Error: Bad concepts CSV filename: '${concepts_csv}'" >&2
    exit 2
fi

awk -F '|' --file=- <<'EOF' "${concepts_csv}" | sort --field-separator='|' --key=1,1 --key=2,2n --unique
BEGIN {
  dmn2tbl["Condition"] = "dx"
  dmn2tbl["Drug"] = "rx"
  dmn2tbl["Meas Value"] = "mx"
  dmn2tbl["Measurement"] = "mx"
  dmn2tbl["Observation"] = "ox"
  dmn2tbl["Procedure"] = "px"
  OFS = FS
}

{
  if ($3 in dmn2tbl)
    $3 = dmn2tbl[$3]
  print $3, $1
}
EOF
