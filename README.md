# Alchemical Dictionaries in TEI-XML
This repository contains TEI-XML resources for alchemical dictionaries (like Ruland or Sommerhoff). 
The goal is to provide data that can be reused or referenced in other projects where alchemical terms are concerned.

A current version of this dataset was released under a [CC-BY license](https://creativecommons.org/licenses/by/4.0/legalcode) on Zenodo: [https://zenodo.org/records/14638445](https://zenodo.org/records/14638445) and discussed in a data paper in a [Journal of Humanities Data special issue on data-driven history of ideas](https://openhumanitiesdata.metajnl.com/collections/historyofideas).  

---

**Things to do** can be found in the [TODOs.md file](https://github.com/sarahalang/alchemical-dictionaries/blob/main/TODOs.md).

The current final versions of the TEI-XML-encoded dicitonaries are:
1. **Ruland 1612:** `alchemical-dictionaries/Ruland1612/Ruland.xml` (ca. 3200 entries)
2. **Sommerhoff 1702:** `alchemical-dictionaries/Lexikon_Sommerhoff_Mayer2022_slighlyEdited2025-01-08.xml` (ca. 17.000 entries)
Together, they contain some 20.000 entries. 

---

# The repository and its contents

## Overview
Because alchemical terminology is so confusing both historical and modern readers turned to dictionaries. 
This repository contains TEI XML resources for alchemical dictionaries. 

Alchemical language was notoriously obscure, leading to the creation of dictionaries from the 17th century onwards. 
Two examples are Ruland's *Lexicon Alchemiae* and Sommerhoff's bilingual Latin-German *Lexicon pharmaceutico-chymicum*, which are available in TEI encodings following the TEI dictionary module in this repository. The repository may be expanded in the future to include additional alchemical dictionaries.

These resources may be reused in other projects, such as linking them to digital scholarly editions to provide contemporary definitions for historical terms. 
Although the data requires further refinement before it can count as a true digital scholarly edition, it is already useful for many academic purposes. By making these resources public, we hope to inspire additional contributions and maybe even collaborative efforts to improve the data based on this first version.

## Repository contents
The repository currently contains an encoding of Ruland and Sommerhoff dictionaries adhering to the TEI dictionary module. 

The data provided here is based on the Transkribus output from the University of Innsbruck's NOSCEMUS ERC project (see [NOSCEMUS wiki metadata on Ruland](https://wiki.uibk.ac.at/noscemus/Lexicon_Alchemiae); [this is the Transkribus 'digital sourcebook'](https://transkribus.eu/r/noscemus/#/documents/668514), i.e. (messy, uncorrected) OCR output of the text alongside the facsimile images. The Transkribus output from the Noscemus GM HTR model (without `<facsimile>`) can still be seen in: `2022_Ruland_ohne_linebreaks_und_facs-lauftitel-entfernt.xml`.) 
While the data is shareable and usable for computational analysis, it does not yet meet the quality standards required for a digital scholarly edition in that it does contain messy HTR output, even if the quality is very high.

The HTR (Handwritten Text Recognition) output was generated using the Nosemus GM OCR model in Transkribus, which has a very low character error rate. 
However, the OCR output has not been thoroughly proofread and may contain errors. Despite these issues, the data is of sufficient quality to be resuable in many contexts. 

## Data Encoding
- Facsimile references were removed to make the (very lengthy) dictionaries manageable in XML editors.
- Regular expressions were used to structure the dictionaries according to the TEI dictionary module.
- Entries typically include: Lemma and annotations for text in languages other than Latin (e.g., German and Ancient Greek fragments). The TEI dictionary module would allow a much more detailed encoding which was not fully taken advantage of in the current state of the data. 
- Alchemical symbols in *Sommerhoff* are underrepresented due to incomplete OCR proofreading. Encoding of glyphs is limited to the first 22 pages.

## Contributors
Both dictionaries were prepared as part of a University of Graz project seminar (2022 and 2023). 
Rosa Mayer (Sommerhoff dictionary, 2022) and Ines Lesjak (Ruland dictionary, 2023) received the XML output of the high-performing Noscemus GM4 OCR model and applied TEI encoding, partially manually, partially using regular expressions, to generate a basic encoding of the dictionaries according to the TEI dictionary module. The focus was on making the entries addressable by their IDs and headwords, less on the frontmatter or backmatter of the books. 

Since these encodings still contained many errors and lacked entry ids, edits were made by Sarah Lang in 2024-12 to 2025-01 to bring the data to publishable quality and thus, make the data accessible and reusable even though there are of course many more improvements that could be done (but this would make it likely that the data languish for many more years to come rather than being available as a public resource). 

## Potential Future Work
Several potential future developments for this repository include:
1. Develop a term annotator tool to automatically identify terms in a given XML file that are covered by the dictionaries. This would allow automatic annotation of digital scholarly editions with links to these dictionaries.
2. Provide machine-generated translations of terms into English. This feature would support researchers with limited proficiency in Latin while still referencing the original Latin source. It should, of course, indicate clearly that translations are machine-generated.
3. Create RDF representations for terms and their interrelations. This would require several rounds of data corrections and improvements before reliable RDF can be automatically extracted from the data.
4. Many entries in the dictionaries cross-reference other terms. Encoding this linking process could significantly enhance the data's usability: For example, in *Sommerhoff*, German-to-Latin translations exist for Latin terms. A script could be used to generate identifiers for these entries semi-automatically. An XML editor like Oxygen could be used to help autocomplete links/ref after initial id-assignments are made (e.g. adapting the script in this repo for adding ids to Ruland) in the Latin part of the dictionary.
5. Expand the detailed encoding of glyphs and symbols. For instance, *Sommerhoff* contains alchemical symbols not part of Unicode. Such symbols are currently only encoded for the first 22 pages. Since many of these symbols are not part of Unicode and the OCR has accordingly not captured them, this would require substantial work.
6. Add more dictionaries to the repository.

---

# On the dictionaries 
These descriptions rely on the highly useful [Noscemus wiki](https://wiki.uibk.ac.at/noscemus/Main_Page) (see list of references below). 
The messy OCR that these TEI-dictionary encodings are based on was originally created in the NOSCEMUS ERC project at the University of Innsbruck.

Many thanks to Stefan Zathammer for making this data available for this project. The goal which was to encode alchemical lexica/dictionaries using the TEI dictionary module to make the data accessible for digital humanities research and computational analysis. 

## Sommerhoff's *Lexicon pharmaceutico-chymicum Latino-Germanicum et Germanico-Latinum* 

### Source Description
The bilingual lexicon (Latin-German and German-Latin) was authored by the German pharmacist Johann Christoph Sommerhoff and first published in 1701. 
It includes Latin-German and German-Latin sections, with approximately 12,000 entries in the former (~400 pages) and 5,500 entries in the latter (~100 pages).  

**Full Title:** *Lexicon pharmaceutico-chymicum Latino-Germanicum et Germanico-Latinum continens terminorum pharmaceuticorum et chymicorum tam usualium quam minus usualium succinctam et genuinam explicationem cum versione Germanica et additione signorum, quotquot hactenus innotuere, characteristica. Cui accessit vocabularium Germanico-Latinum locupletissimum vegetabilium, animalium et mineralium in officinis pharmaceuticis et alias usitatorum. Adiuncti sunt sub finem characteres metallorum, mineralium, planetarum, ponderum aliarumque rerum chymicarum. Opus et medicis et pharmacopoeis et aliis de notitia harum rerum sollicitis necessarium et perutile.*  
**Author:** Johann Christoph Sommerhoff  
**Year of Publication:** 1701  
**Place:** Nuremberg  
**Publisher/Printer:** Johann Zieger, Georg Lehmann, Christian Siegmund Froberg  

The book is introduced by three title pages, an author portrait, a dedicatory elogium, bilingual prefaces (Latin and German), five laudatory poems (two in Latin, three in German), and a Latin letter addressed to Sommerhoff by a friend. Errata are provided at the end of the volume.

The lexicon covers pharmaceutical, zoological, botanical, mineralogical, (al)chemical, and medical terminology. Terms are supplemented with a rich array of alchemical symbols, many of which serve as abbreviations in the lexicon.  
It is a rare example of a scientific lexicon with a near-symmetrical relationship between Latin and German. While the Latin-German section is more extensive, both lexica are alphabetized independently.  Vernacular German material was likely included to support users with limited Latin proficiency, such as pharmaceutical apprentices lacking technical Latin knowledge.  

Following the main entries, additional materials include:
- A "Chemical Alphabet" (*Alphabetum chymicum*, p. 99)  
- An alphabetically arranged list of alchemical symbols (pp. 100–113)  
- Short lists of symbols for:  
  - Alchemical diphthongs  
  - The four elements  
  - The four "degrees of fire"  
  - The twelve months and zodiac signs  
  - The seven celestial bodies regarded as planets at the time (Moon, Sun, Venus, Mars, Mercury, Jupiter, Saturn)  
  - Units of weight  
  - The four seasons  
  - Days and weeks  
  - "Chemical vowels" (pp. 113–114)  
- Two pages of errata for the entries  

Symbols play a prominent role in the text, either complementing or replacing linguistic terms, sometimes entirely. 
The Latin-German section often cites sources, indicating that much of the compiled knowledge was drawn from earlier works.

### Rosa Mayer's initial TEI-dictionary encoding (2022)
Mayer's project seminar work focused on the TEI encoding of 22 pages from the *Lexicon pharmaceutico-chymicum Latino-Germanicum et Germanico-Latinum*. 

- The encoding starts at the letter "A" in the Latin-German section (page 1 of the lexicon).  
- Corresponding entries in the German-Latin section were not encoded in this project. However, entries in the Latin-German section were given XML IDs to facilitate future linking.  
- The focus was placed on encoding alchemical symbols, which appear both in the text and in a glossary at the end of the book.  
- 618 symbols were encoded across the first 22 pages that were annotated in detail (with approximately 280 unique symbols). 
  - <g>` elements were used in the main text to represent symbols.  
  - `<glyph>` elements in the TEI header contained descriptions of these symbols and were referenced by `<g>` elements.  
  - Symbols were ordered in the TEI header based on their first appearance in the text, not the glossary.  
  - Many symbols were mapped to Unicode ranges for "Alchemical Symbols" (1F700–1F77F) and "Miscellaneous Symbols" (U+2600–U+26FF).  
  - Symbols not available in Unicode were approximated using visually similar characters, such as letters, digits, or other symbols.  
  - Approximations were documented in `<glyph>` descriptions, though some may lead to ambiguities.  
  - Certain symbols have multiple meanings (e.g., the "♂" symbol represents Mars, iron, or masculinity). When context clarified a specific meaning, the symbol was encoded accordingly (e.g., as "iron" in 
  - Some Unicode ranges were not fully supported by tools like Oxygen XML Editor, complicating the encoding process.  
  - The "Medieval Unicode Font Initiative" was a valuable resource for locating additional symbols.  
- The rest of the dictionary was encoded in a more minimalistic implementation of the TEI dictionary guidelines: 
  - `<entry>` elements encapsulated each lexicon entry.  
  - `<form>` with `type="lemma"` was used to mark headwords. Variants were marked with `type="variant"`.  
  - `<sense>` and `<def>` elements were used for prose definitions, while `<cit>` elements captured translations.  
  - Automated insertion of tags was attempted but frequently required extensive manual correction.  Automated approaches struggled with irregularities in text structure, such as abbreviations, misplaced punctuation, and line breaks in the historical source and its Transkribus HTR output. Identifying logical boundaries for `<form>` and `<sense>` elements often required manual intervention. 
  - When multiple senses were present, they were encoded with numbered `<sense>` elements.  

---


## Ruland's *Lexicon Alchemiae*

### Source Description
The *Lexicon Alchemiae* is a chymical dictionary comprising approximately 500 pages and 3,000–5,000 entries (ca. 3200 according to the number of entries in the TEI encoding, although many are exceedingly long). It is dedicated to Heinrich Julius, Duke of Braunschweig and Lüneburg. The letter of dedication outlines the author’s intention to impose order on the "Babylonian confusion" of alchemical terminology and promote the study of alchemy. The *Lexicon Alchemiae* is a cornerstone of alchemical literature, reflecting the state of the alchemical lexicographical endeavour in the early 17th century. Its comprehensive approach and bilingual nature make it a valuable resource for understanding the historical development of alchemical terminology and its intersections with the wider worlds of medicine, metallurgy and natural philosophy.

**Full Title:** *Lexicon Alchemiae sive dictionarium alchemisticum cum obscuriorum verborum et rerum hermeticarum tum Theophrast-Paracelsicarum phrasium planam explanationem continens. Auctore Martino Rulando, philosophiae et medicinae doctore et Caesareae Maiestatis personae sacerrimae medico etc.*  
**Author:** Martin Ruland the Younger (*Martin Ruland d.J.*)  
**Year of Publication:** 1612  
**Place:** Frankfurt am Main  
**Publisher/Printer:** Zacharias Palthenius  

The entries vary significantly in scope, ranging from simple explanations (e.g., *Acetum amincum, id est, album*) to comprehensive lists of synonyms, detailed lexicon entries, and even short scholarly treatises. Many entries include subentries for additional clarification.
Latin is the dominant language but German translations, paraphrases, and explanations are provided extensively.  
The book was likely designed to meet a widespread need for clarification in the field of alchemy. The imperial privilege prohibiting unauthorized reprints for ten years suggests that it was expected to achieve significant commercial success.  

### Ines Lesjak's initial TEI-dictionary encoding (2023)
This project seminar work at the University of Graz involved encoding the *Lexicon Alchemiae* in TEI XML following the dictionary module.
The significant variation in entry length and structure requires a flexible approach to encoding (from automation using regular expressions to manual correction).  

Lesjak's work went from the Noscemus Transkribus HTR output that didn't contain lots of semantic encoding (mostly `<lb/>`) to a first version of this dictionary following the TEI Dictionary module. This was achieved partly manually and partly using regular-expression-powered search-and-replace.
  - Some things that were removed:
    - `<ab>` elements that resulted in a nesting error when entries spanned more than one page.
    - The `<facsimile>` information that cluttered the document for a book this size (but may be reintroduced from the original file if needed at a later date, the `<pb/>` still contain the relevant ids.
    - Alphabetical indexing was removed.
    - OCR junk (such as 'digitized by Google') was removed. Otherwise, some OCR errors may have been corrected but the OCR is not fully proof-read. 
  - Page headers and page numbering were encoded as `<fw>`.
  - For structuring the entries, structural characteristics of the text, such as the presence of 'id est' (indicating a definition) were used to find the beginning of new entries (however, unfortunately, not all entries are structured exactly the same).
  - `<form>` was assigned the `@type` 'phrase' or 'lemma' depending on whether it was a word or multi-word entity (however, in cases where this attribute was missing, this was later (2024-12-12) automatically made into 'lemma' by use of regex). In the case of variants, 'variant' was assigned but it seems that many of the more detailed encodings (that go beyond identifying the entry, a definition, a lemma or a text bit in German, was not done consistently throughout the whole text. In case a variant with only minor orthographic variation appeared after the lemma, `<orth>` was used. `<def>` was used in case something seemed like a definition - in cases where this wasn't clear, either only `<sense>` was used or `<note>` elements were added.
  - `<cit>` and `<quote>` were used for German text insertions (that can either be single-word synonyms, more general text or specifically the definition in German).
  - Some pages had landscape tables and diagrams that were included as `<list>`.
  - The regex search-and-replace workflow worked relatively well for short entries but was error-prone the longer entries got.
  - The following is an example of the typical encoding of an entry containing some German:
```
<entry><dictScrap>
  <form type="lemma">Ampulla vitrea</form>
  <sense>,
    <def>id est,
      <cit type="translation" xml:lang="de" style="font-variant: fraktur">
        <quote>Kolbe</quote>
      </cit>
    </def>.
  </sense>
</dictScrap></entry>
```

---

## References

- Gaede, Jonathan (2017). Zur Verwendung astrologischer und alchemistischer Symbole in früh-neuhochdeutschen Fachtexten. In: Klein, Wolf-Peter; Schulz, Matthias; Staffeldt, Sven & Stahl, Peter (Hrsg.). WespA. Würzburger elektronische sprachwissenschaftliche Arbeiten. Nr. 19. Würzburg: Online-Publikationsservice der Universität Würzburg. URN: urn:nbn:de:bvb:20-opus-153198.
- Sommerhoff, Johann Christoph (1701). *Lexicon pharmaceutico-chymicum Latino-Germanicum et Germanico-Latinum*. [Noscemus Wiki Entry](http://wiki.uibk.ac.at/noscemus/Lexicon_pharmaceutico-chymicum_Latino-Germanicum_et_Germanico-Latinum) (last revised: 06.10.2021).  
- Ruland, Martin (d.J.) (1612). *Lexicon Alchemiae*. Noscemus Wiki. [URL](http://wiki.uibk.ac.at/noscemus/Lexicon_Alchemiae) (last revised: 27.05.2021).  

---

