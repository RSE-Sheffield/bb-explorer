"""
Based on https://python.langchain.com/docs/how_to/parent_document_retriever/
pip install langchain[openai] langchain-chroma langchain-community langgraph
"""

# llm imports
import os
from langgraph.graph import START, StateGraph
from typing_extensions import List, TypedDict
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate

# parent doc retrieval imports
from pathlib import Path
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import pickle

os.environ["OPENAI_API_KEY"] = "REDACTED"

# Folder where .tex inputs can be found
dataset_dir = Path('dataset')

# Split the documents into chunks
# The vectorstore to use to index the child chunks
vectorstore = Chroma(
    collection_name="BB-Literature", embedding_function=OpenAIEmbeddings(),
    persist_directory="./chroma_db"
)

# The storage layer for the parent documents
store = InMemoryStore()

# If pickle exists, load that instead of doing re-processing
if os.path.exists("in_memory_store.pkl"):
    with open("in_memory_store.pkl", "rb") as f:
        store.store = pickle.load(f)

# Load missing documents
existing_docs = set()
for k,v in store.store.items():
    existing_docs.add(v.metadata["source"]);
#print(existing_docs)

# This text splitter is used to create the child documents
child_splitter = RecursiveCharacterTextSplitter(chunk_size=400)

retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=store,
    child_splitter=child_splitter,
)

# Add docs and persist storage
docs = []
for tex_file in dataset_dir.glob('*.tex'):
    if not str(tex_file) in existing_docs:
        docs.extend(TextLoader(tex_file).load())
        # Attach metadata
        # This should help inform similarity search
        docs[-1].metadata["file"] = tex_file.name
        #print("Add doc: %s"%(tex_file))

if len(docs):
    retriever.add_documents(docs, ids=None)

# Export the vector store to chroma_db dir
# vectorstore.persist() In new Chroma docs are automatically persisted
with open("in_memory_store.pkl", "wb") as f:
    pickle.dump(store.store, f)


# store.yield_keys() should now return a list of N keys, where N is number of documents loaded
# vectorstore.similarity_search("test string") can now be used to perform similarity search
# retriever.invoke("test string") can now return the full page content of chunks
# Note: Retriever returns larger chunks, but there's no explicit link to the small chunks
# Can also recursively make

# @todo It should be possible to serialise the retriever state to save hammering API on every restart

#t = vectorstore.similarity_search("Caroline")
#print(len(t)) # 4

#t = retriever.invoke("Caroline")
#print(len(t)) # 2

llm = init_chat_model("gpt-4.1-nano", model_provider="openai")
# https://python.langchain.com/docs/tutorials/rag/
prompt = ChatPromptTemplate([
    #("system", "You are a helpful AI bot. Your name is {name}."),
    ("human", """
You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise. Although the context is provided in 1800's French, you should respond in modern English unless the question specifies different.

The context you are provided are excerpts from the series of French books Bibliothèque Britannique which is a scholarly periodical founded in 1796 in Geneva by Marc-Auguste Pictet, Charles Pictet de Rochemont, and Frédéric-Guillaume Maurice. Its purpose was to introduce French-speaking European audiences to the scientific, literary, and industrial advancements of Britain, particularly during a time of political tension between France and Britain (e.g., during and after the French Revolution and the Napoleonic Wars).

In particular, your excerpts are taken from the Literature volume 56, pertaining to the novel Patronage by Maria Edgeworth.

Question: {question} 
Context: {context} 
Answer:"""),
])

# Define state for application
class State(TypedDict):
    question: str
    wide_context: List[Document]
    acute_context: List[Document]
    answer: str


# Define application steps
def retrieve_acute(state: State):
    # This is the basic vector search, returns many small chunks
    retrieved_docs = vectorstore.similarity_search(state["question"])
    return {"acute_context": retrieved_docs}
    
def retrieve_wide(state: State):
    # This is the fancy vector search, returns parent documents of what acute would return?
    retrieved_docs = retriever.invoke(state["question"])
    return {"wide_context": retrieved_docs}


def generate(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["wide_context"])
    messages = prompt.invoke({"question": state["question"], "context": docs_content})
    response = llm.invoke(messages)
    return {"answer": response.content}

# Compile application and test
graph_builder = StateGraph(State).add_sequence([retrieve_wide, generate])
graph_builder.add_edge(START, "retrieve_wide")
graph = graph_builder.compile()

#print("Ask question: What do you know about Caroline?")
#response = graph.invoke({"question":"What do you know about Caroline?"})
#print(response["answer"])

while True:
    q = input("Ask question: ")
    response = graph.invoke({"question":q})
    print(response["answer"]+"\n")
    