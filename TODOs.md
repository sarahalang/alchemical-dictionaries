# TODOs

## For the Sommerhoff lexicon (Sommerhoff1701)
- similar to the Ruland tasks that are described below in lots of detail, `<pc>` was removed from the document and `<dictScrap>` introduced in its stead.
- **DONE (2025-01)** The entries were corrected so that the result became a valid TEI document.
- **DONE (2025-01)** A simple TEI header was added (like for Ruland).
- **TODO** Unlike in Ruland, headers and pagenumbers are not currently addressable in `<fw>` with respective `@type` but this could presumably automatically be done in an XSL transformation that checks whether the `<fw>` contains digits.
- some IDs were already added in the initial encoding by Mayer, **TODO** although it might make sense to create `@n` as I did with the XSL identity transform for Ruland.
- **TODO** The German and Latin entries should be put into different `<div>`s.
- **TODO** Create a simple HTML preview for this as well so that one can look at the dictionary a bit better. (plus clean up the preview template)
- **TODO**
- **TODO** in the future, encoding frontmatter and backmatter as well as the titlePage would be nice.  
  
## For the Ruland lexicon (Ruland1612)
### DONE (2025-01):
- fixing the major TEI errors, nesting errors etc is now completed. With that being done, I was able to run the transformation to add ids on the improved Lesjak file. Now we can continue working with the final version which I have uploaded to finally replace `Ruland.xml`.
- added minimal TEI header that should be enough for the data publication.
- created a simple HTML preview (erroneous and ugly with dummy text remaining but functional).

### TODO:

1. **TEI checking:** 
   - **Does the TEI make sense** according to the [Dictionaries module](https://tei-c.org/release/doc/tei-p5-doc/en/html/DI.html)? It uses elements like `<entry>` (so far, `@type` for which letter in the dictionary and `@n` which should later become `@xml:id`), `<dictScrap>`, `<sense>`, `<def>` (usually for the Latin definition), `<cit>` (usually contains German text in Fraktur) and some others (but many aren't used consistently and data quality gets worse further into the book). Analyse which elements are used and where/when/how often and come up with suggestions for improvement. I indicated which letter each entry belongs to using `@type` so far - how should such information be encoded according to the guidelines? What to do about the segments in Ancient Greek? (related: are they actually there or are those OCR artifacts?; I added some `<seg type="greek">` when I found some by accident). Do we need u/v or i/j normalization? What should really be used for segments in different languages? For German, so far it's the weird `<cit><quote>` construct that may need changing, for Greek I sometimes used `<seg type="Greek">` which should probably be `<seg xml:lang="el">` or something).
   - **improve the TEI header** to make it more detailed. **(partially DONE, 2025-01-08) is the following:** by adding information from the Noscemus project and documenting how the data were processed. The encoding was begun in summer term 2023 by Ines Lesjak in Uni Graz DH Projektseminar and while this was a great first step, the resulting data quality was inconsistent.  See: [NOSCEMUS wiki](https://wiki.uibk.ac.at/noscemus/Lexicon_Alchemiae) for metadata. 
   - **create a (titlePage) encoding for the frontmatter** (currently simply set aside by nesting into `<div type="frontmatter">`)
   - **check final 'TODO's** (by full-text searching `TODO' and verifying the encodings)
   - **document the encoding** (maybe rather here than in the TEI as they encoding may need improvement later). There are definitely inconsistencies in how detailed the encoding is and in some cases, Ines Lesjak seems to have used slightly different ways of encoding things (such as documenting form and variants specifically) but it is not clear whether it was done consistently (not likely). 
   - **Some of this has already been done** (so it may not be necessary anymore): Check `@type='lemma'` that must have been added to all/most entries via regex (this was missing in many cases and I don't think there was a reason for it); TODO the same should probably be done with the attributes indicating German Fraktur snippets (these are missing in the `<cit>` towards the end of the dataset and I also have a feeling there aren't any such elements used for anything other than German snippets, although I might be wrong about this... would need to be checked before replace-all.
   - **DONE:** Consider reintroducing alphabetical indexing (like 'Letter A begins here') by putting [a milestone element](https://tei-c.org/release/doc/tei-p5-doc/en/html/CO.html#CORS5) (most likely `<milestone>`) or similar potentially suitable non-nesting elements in the relevant places (shouldn't take too long). Encoding suggestion: `<milestone unit="letter" n="A"/>`. --> Alphabetical indexing was introduced like so. **TODO:** research if there would have been a better way of encoding this. Searching for things like `//entry[@type="P"]` or  `//entry[@type="P"][1]` shows the locations of elements of supposedly letter P (or any other) that show up in places where they shouldn't be (suggesting that there is an annotation error, most likely that a new entry element was begun when the text really should have been part of the previous one - although this is conjecture and wasn't verified with [the Noscemus digital sourcebook](https://transkribus.eu/r/noscemus/#/documents/668514). I have already marked some of them with 'TODO' in a comment.
   - **correct fws**: Mostly done except `<fw type="TODO">` (check these few instances using [the Noscemus digital sourcebook](https://transkribus.eu/r/noscemus/#/documents/668514) (find via full-text search; find in XML using `//fw[@type='TODO']`). The following should be done: The XPath `//fw[not(@*)]` will find all `<fw>` without attributes (this shouldn't exist). These can be corrected to either add `type='header'` (as is true for most cases) but I have also found some weird ones that seemed to contain text that probably shouldn't be in `<fw>` at all.
2. **(DONE as of 2025-01-07) Creating IDs:** Create IDs for the entries. This is already happening in part in the `adding-entry-ids-Ruland1612.xsl` (so far adding them as `@n` as this will not disturb validation in case IDs aren't yet unique). After the script is run, these IDs need to be checked (some include junk characters or the same ID appears multiple times) - once they are of high enough quality to work as `@xml:id`, use a regex replacement to turn `<entry @n` to `<entry xml:id`. What can be done here is to run the XSL on the current data and inspect where it produces validation errors in the resulting XML: If plain text ends up in the output, there might be nesting problems with that respective entry in the input. Also, is anything missing from the template? (such as elements on the nesting level of entry beyond `<fw>` and `<pb>` because only those are covered by the transformation so far). Once the transformation works ok and ids have been added, we can continue working with the output file (and make any necessary manual edits there in the output file) - but while the transformation is still buggy, manual fixes should be added to the base file still. See [this example image](https://github.com/sarahalang/alchemical-dictionaries/blob/main/example-entry-nesting-problem.png) (showing the error that happens in the output and would need to be investigated in the input file). The XML file from which this snapshot was taken (an example of what the output looks like when you transform `Ruland.xml` with the XSL `transform-ruland-include-ids.xsl`) is: `adding-entry-ids-ruland1612.xml`.
5. **Cross-Referencing:** This dictionary would be a much more interesting resource if there were cross-referencing (many items get mentioned in some entry that have an entry of their own), however, this can only be semi-automated (maybe regex-but-step-through-replace. Also, it might be relevant to encode synonyms - but for that one would need enough Latin (or familiarity with the relatively limited ways this is expressed in Ruland) to make those decisions.
6. **Create RDF/SKOS**(?) from the dictionary using the `@xml:id` of each entry as the concept name, the Latin name version from `<form @type='lemma'>` and the German version from the related encoding (although the German sections aren't consistently labeled throughout the book, especially later in the book and switch between lemma in German and definition in German). Likely, this will only make sense in a quite reduced manner until the data quality is near perfect.
7. **(most likely DONE but check) Open Questions:** Are there nested entries? If yes (seems so), how to proceed? How to indicate they are related? (Apart from this added information, it would make sense to encode them separately). 
8. **HTML preview:**
   - **Create an HTML preview:** (mostly DONE as of 2025-01-07) for example, a list item (unordered) per entry, with the lemma in bold (`<b>`). The German parts could be rendered in italics (`<i>`). Maybe use `<xsl:for-each>` to add something like `<h1>A</h1>` before the first entry of `@type='A'`, etc. A mini-to-bootstrap XSL that can be used as a base is [here](https://github.com/sarahalang/Harvard_BeyondTEI_Workshop_SLang2022/blob/main/ADDITIONAL_RESOURCES/XSL_BASE_STYLESHEETS/mini-bootstrap.xsl).
   - **TODO:** improve the HTML preview to make it nicer to look at and use it to identify and correct remaining errors in the encoding.  
   - Improving the HTML preview (adding enough detail so that all elements are covered and the output is a simple HTML file that people can use). The current version of the XSL runs on the imperfect/error-laden XML output (`HTML-preview/adding-entry-ids-ruland1612.xml`) of the transformation before it (`transform-ruland-include-ids.xsl`): [The folder 'HTML-preview'](https://github.com/sarahalang/alchemical-dictionaries/tree/main/HTML-preview) contains the relevant files (`HTML-preview/ruland-xml-preview.html` is the output of `HTML-preview/visualize-ruland-in-html.xsl`).
   - In the end, it should, of course, be run on the final correct XML data.
   - When running and improving the transformation for the simple HTML preview, one notices a number of errors in the XML, such as likely Transkribus-caused transcription errors in the header lines such as `RVLANDI PHILOS. ET MEDICI ` or `RVLANDI PHIL. Ex MEDICI. `. One could either check if these go back to actual print anomalies and encode them in TEI in a way that makes sense (so that they're encoded as `fw @type='header'` and thus, equally suppressed in the HTML preview.) or just find textual versions of these headers and add `@type='header'` so they get processed as they should. They're not the most central element of the TEI, so fixing them isn't a priority beyond making the transformation to HTML work alright.
   - **DONE:** Since the alphabetical indexing using `<milestone>` has been introduced, it was easy adding links to jump there. 
10. **Maybe interesting for later:**
   - introduce linking between entries.
   - full semi-automated OCR correction (maybe using my [LLM-powered OCR-correction approach](https://github.com/sarahalang/LLM-powered-OCR-correction)).
   - handle long lists inside the dictionary. Some diagrams were encoded as lists by Ines Lesjak but there are many numbered lists in the dictionay that are currently somewhat awkwardly encoded as notes or similar. This could be improved. It should be easy to find them by full-text searching something like '1. '. 
   - automatically create RDF or SKOS from the TEI data once it has the TEI is optimal and maybe has even been verified manually to ensure correct inference.
   - maybe provide an LLM-generated English translation for all entries (that is marked as such but may be really useful when people want to use this in digital scholarly editions to make the terms easier to understand). For this to work well, only small portions of the dictionary should be handed over to the LLM to get the best possible output.

---

# What has already been done 
## Ruland 1612
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
---


