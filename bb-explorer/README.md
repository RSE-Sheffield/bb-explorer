# bb-explorer

This directory contains all code specific to the bb-explorer project that doesn't need to be integrated in openwebui.
At the moment, this is specifically the preparing of the data for the bb-explorer app and for deploying the app on University of Sheffield's servers.

## Data

The structure of the Bibliotech Brittanique (BB) document is roughly as follows:

- BB
    - Topic 1 (Eg. Science)
        - Volume (Eg. Volume 9)
            - Section 1 (Eg. Physique)
                - Article Name 1 (Eg. SUFFRAGES BRITANNIQUES FAVORABLES A LA PHYSIQUE SPÉCULATIVE.)
            - Section 2
                Article Name 2
        - Volume 2
            - Section 1
                - Article Name 1
            - Section 2
                Article Name 2

The data is digitised on google books as pdfs for each volume.

### Download

We are interested in the following volumes of the Bibliotech Brittanique (BB):

- Agriculture
- Literature
 etc.

### Preprocessing

The raw data is in pdfs. The format is pictures of the documents. We need to convert them to text. We do the following steps:

1. Convert pdfs to images (pngs) using an LLM.
2. Convert images to latex to correctly handle the text and metadata (footers, page numbers, etc.). Save to disk.
3. Clean up latex files. Save to disk.
4. Aggregate the latex files into a single file. Save to disk.
5. Translate from English to French. Save to disk.

### Naming Convention

The naming convention for the files is as follows:
- bb
    - {Topic}-{Volume}
        - full_volume.pdf
        - pages
            - images
                - bb-{Topic}-{Volume}-pg{page_number}.jpg
            - latex
                - bb-{Topic}-{Volume}-pg{page_number}.tex
            - bb-{Topic}-{Volume}-all.tex
        - articles
            - {Section}
                - bb-{Topic}-{Volume}-{Section}-{Article Name}-pg{page_number_start}-{page_number_end}_fr.tex
                - bb-{Topic}-{Volume}-{Section}-{Article Name}-pg{page_number_start}-{page_number_end}_eng.tex

