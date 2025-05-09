# Langchain RAG

The script in this directory is separate from the OpenWebUI implementation in the rest of this repo.

It uses OpenAI and ParentDocumentRetriever, to return larger chunks as context for the LLM to perform RAG. It attempts to cache embdeddings between runs, only extending if new documents are found inside `dataset`.

It has currently been tested with a small dataset of excerpts from BB Literature Vol 56/57 which pertain to the book Patronage by Maria Edgeworth.

It should be feasible to extend this to a larger dataset, although that will require processing other sets of excerpts to latex and amending the prompt to provide general context to each dataset.

With multiple datasets, it may be worth looking how we can amend the generated context to automatically include a summary of the parents book/dataset (by reviewing it's metadata).

Eventually, if deemed suitable, it should be possible to link this to OpenWebUI via LangServe.