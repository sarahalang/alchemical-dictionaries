# alchemical-dictionaries
This repository contains TEI-XML and RDF resources for alchemical dictionaries (like Ruland or Sommerhoff). The goal is to provide data that can be reused or referenced in other projects where alchemical terms are concerned.

# The dictionaries
Because alchemical terminology is so confusing both historical and modern readers turned to dictionaries. Examples to be included here are: 
- Martin Ruland, *Lexicon Alchemiae* sive dictionarium alchemisticum cum obscuriorum verborum et rerum hermeticarum tum Theophrast-Paracelsicarum phrasium planam explanationem continens. Auctore Martino Rulando, philosophiae et medicinae doctore et Caesareae Maiestatis personae sacerrimae medico etc., Frankfurt am Main 1612. Using data based on the Transkribus output from the NOSCEMUS project: [NOSCEMUS wiki](https://wiki.uibk.ac.at/noscemus/Lexicon_Alchemiae). [This is the Transkribus 'digital sourcebook'](https://transkribus.eu/r/noscemus/#/documents/668514), i.e. (messy, uncorrected) OCR output of the text alongside the facsimile images.


# Things to do (Ruland1612)
1. **TEI checking:** Does the TEI make sense according to the [Dictionaries module](https://tei-c.org/release/doc/tei-p5-doc/en/html/DI.html)? It uses elements like `<entry>` (so far, `@type` for which letter in the dictionary and `@n` which should later become `@xml:id`), `<dictScrap>`, `<sense>`, `<def>` (usually for the Latin definition), `<cit>` (usually contains German text in Fraktur) and some others (but many aren't used consistently and data quality gets worse further into the book). Analyse which elements are used and where/when/how often and come up with suggestions for improvement. I indicated which letter each entry belongs to using `@type` so far - how should such information be encoded according to the guidelines? What to do about the segments in Ancient Greek? (related: are they actually there or are those OCR artifacts?). Do we need u/v or i/j normalization? 
2. **Creating IDs:** Create IDs for the entries. This is already happening in part in the `adding-entry-ids-Ruland1612.xsl` (so far adding them as `@n` as this will not disturb validation in case IDs aren't yet unique). After the script is run, these IDs need to be checked (some include junk characters or the same ID appears multiple times) - once they are of high enough quality to work as `@xml:id`, use a regex replacement to turn `<entry @n` to `<entry xml:id`. What can be done here is to run the XSL on the current data and inspect where it produces validation errors in the resulting XML: If plain text ends up in the output, there might be nesting problems with that respective entry in the input. Also, is anything missing from the template? (such as elements on the nesting level of entry beyond `<fw>` and `<pb>` because only those are covered by the transformation so far). Once the transformation works ok and ids have been added, we can continue working with the output file (and make any necessary manual edits there in the output file) - but while the transformation is still buggy, manual fixes should be added to the base file still. See [this example image](https://github.com/sarahalang/alchemical-dictionaries/blob/main/example-entry-nesting-problem.png) (showing the error that happens in the output and would need to be investigated in the input file). The XML file from which this snapshot was taken (an example of what the output looks like when you transform `Ruland.xml` with the XSL `transform-ruland-include-ids.xsl`) is: `adding-entry-ids-ruland1612.xml`.
3. **Create an HTML preview:** for example, a list item (unordered) per entry, with the lemma in bold (`<b>`). The German parts could be rendered in italics (`<i>`). Maybe use `<xsl:for-each>` to add something like `<h1>A</h1>` before the first entry of `@type='A'`, etc. A mini-to-bootstrap XSL that can be used as a base is [here](https://github.com/sarahalang/Harvard_BeyondTEI_Workshop_SLang2022/blob/main/ADDITIONAL_RESOURCES/XSL_BASE_STYLESHEETS/mini-bootstrap.xsl). 
4. **Improve the TEI Header** by adding information from the Noscemus project and documenting how the data were processed. The encoding was begun in summer term 2023 by Ines Lesjak in Uni Graz DH Projektseminar and while this was a great first step, the resulting data quality was inconsistent. Improve the `<div type='frontmatter'>` 
5. **Cross-Referencing:** This dictionary would be a much more interesting resource if there were cross-referencing (many items get mentioned in some entry that have an entry of their own), however, this can only be semi-automated (maybe regex-but-step-through-replace. Also, it might be relevant to encode synonyms - but for that one would need enough Latin (or familiarity with the relatively limited ways this is expressed in Ruland) to make those decisions.
6. **Create RDF/SKOS**(?) from the dictionary using the `@xml:id` of each entry as the concept name, the Latin name version from `<form @type='lemma'>` and the German version from the related encoding (although the German sections aren't consistently labeled throughout the book, especially later in the book and switch between lemma in German and definition in German). Likely, this will only make sense in a quite reduced manner until the data quality is near perfect.
7. **Open Questions:** Are there nested entries? If yes (seems so), how to proceed? How to indicate they are related? (Apart from this added information, it would make sense to encode them separately). 

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
