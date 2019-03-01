How to find concept IDs in the CDM vocabulary
=============================================


This is how I have been finding concept IDs in the Common Data Model
([CDM]( https://github.com/OHDSI/CommonDataModel)) vocabulary in a
documented and reproducible way.

1. Write a script to find all the matching concepts.  The selection is
   overly-broad to eliminate false negatives.  Examples are the
   `concept.*.raw.csv.sh` scripts.  Basically, make a list of synonyms
   to include and make a list of names of false positives to exclude.

2. Look over the concepts to see if there are any large categories of
   false positives and, as needed, improve the script to remove these
   false positives.

   Here's a strategy: grep the file of candidate concepts to exclude
   known accurate synonyms, look at the output, identify additional
   synonyms or false positives, update grep patterns (with synonyms) or
   query (with false positives), and repeat until you have empty output.
   For example:

       grep -iv -e metformin concept.metformin.raw.csv | less
       grep -iv -e metformin -e diabex -e glucophage concept.metformin.raw.csv | less

   This is a good strategy but it is not foolproof because it is
   possible for grep to exclude lines that are false positives and
   thereby hide them from review.  Thus it is important that the
   exclusion patterns be as specific as possible for both grep and the
   query.

3. Use script to generate CSV table of "raw" concepts.

4. Copy "raw" concepts to "selected" ones (e.g. `cp
   concept.mi.{raw,selected}.csv`).  Edit copied file of concepts by
   hand to remove false positives and produce "selected" concepts.  This
   is where you can fix anything that is not handled well by patterns in
   the query or by patterns for grep.

5. When finished, run `concept2id.sh` (e.g. `bash concept2id.sh
   concept.mi.selected.csv`) to produce a list of concept IDs from the
   table of concept records.  Use this list of IDs in downstream
   processing.

This process documents everything and makes the selection of concept IDs
inspectable and reproducible.  (The concepts excluded by hand can be
identified in the diff of the "raw" and "selected" files.)
