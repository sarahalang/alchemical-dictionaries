# alchemical-dictionaries
This repository contains TEI-XML and RDF resources for alchemical dictionaries (like Ruland or Sommerhoff). The goal is to provide data that can be reused or referenced in other projects where alchemical terms are concerned.

# The dictionaries
Because alchemical terminology is so confusing both historical and modern readers turned to dictionaries. Examples to be included here are: 
- Martin Ruland, *Lexicon Alchemiae* sive dictionarium alchemisticum cum obscuriorum verborum et rerum hermeticarum tum Theophrast-Paracelsicarum phrasium planam explanationem continens. Auctore Martino Rulando, philosophiae et medicinae doctore et Caesareae Maiestatis personae sacerrimae medico etc., Frankfurt am Main 1612. Using data based on the Transkribus output from the NOSCEMUS project: [NOSCEMUS wiki](https://wiki.uibk.ac.at/noscemus/Lexicon_Alchemiae). [This is the Transkribus 'digital sourcebook'](https://transkribus.eu/r/noscemus/#/documents/668514), i.e. (messy, uncorrected) OCR output of the text alongside the facsimile images. The Transkribus output from the Noscemus GM HTR model (without `<facsimile>`) can still be seen in: `2022_Ruland_ohne_linebreaks_und_facs-lauftitel-entfernt.xml`.


# Things to do 
Have now been moved to the [TODOs.md file](https://github.com/sarahalang/alchemical-dictionaries/blob/main/TODOs.md).

# What has already been done (Ruland1612)
- removed `<pc>` around each punctuation (which didn't make sense to me but was used to 'hide' nesting problems in the dictionary that would have otherwise not been valid). 
- added `@type='lemma'` to all entries via regex (this was missing in many cases and I don't think there was a reason for it); TODO the same should probably be done with the attributes indicating German Fraktur snippets (these are missing in the `<cit>` towards the end of the dataset and I also have a feeling there aren't any such elements used for anything other than German snippets, although I might be wrong about this... would need to be checked before replace-all.
- **preparatory work by Ines Leskak (summer 2023):** went from the Noscemus Transkribus HTR output that didn't contain lots of semantic encoding (mostly `<lb/>`) to a first version of this dictionary roughly following the TEI Dictionary module. This was achieved partly manually and partly using regular-expression-powered search-and-replace.
  - Some things that were removed:
    - `<ab>` elements that resulted in a nesting error when entries spanned more than one page.
    - The `<facsimile>` information that cluttered the document for a book this size (but may be reintroduced from the original file if needed at a later date, the `<pb/>` still contain the relevant ids.
    - It also seems that the alphabetical indexing was removed.
    - OCR junk (such as 'digitized by Google') was removed. Otherwise, some OCR errors may have been corrected but the OCR is not fully proof-read. 
  - Page headers and page numbering were encoded as `<fw>`.
  - For structuring the entries, structural characteristics of the text, such as the presence of 'id est' (indicating a definition) were used to find the beginning of new entries (however, unfortunately, not all entries are structured exactly the same).
  - `<form>` was assigned the `@type` 'phrase' or 'lemma' depending on whether it was a word or multi-word entity (however, in cases where this attribute was missing, this was later (2024-12-12) automatically made into 'lemma' by use of regex). In the case of variants, 'variant' was assigned but it seems that many of the more detailed encodings (that go beyond identifying the entry, a definition, a lemma or a text bit in German, was not done consistently throughout the whole text. In case a variant with only minor orthographic variation appeared after the lemma, `<orth>` was used. `<def>` was used in case something seemed like a definition - in cases where this wasn't clear, either only `<sense>` was used or `<note>` elements were added.
  - `<cit>` and `<quote>` were used for German text insertions (that can either be single-word synonyms, more general text or specifically the definition in German).
  - Some pages had landscape tables and diagrams that were included as `<list>`.
  - The regex search-and-replace workflow worked relatively well for short entries but was error-prone the longer entries got.
  - The following is an example of the typical encoding of an entry containing some German (`<pc>` has since been removed):
```
<entry>
  <form type="lemma">Ampulla vitrea</form>
  <sense><pc>,</pc>
    <def>id est<pc>,</pc>
      <cit type="translation" xml:lang="de" style="font-variant: fraktur">
        <quote>Kolbe</quote>
      </cit>
    </def><pc>.</pc>
  </sense>
</entry>
```
