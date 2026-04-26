import time
from dotenv import load_dotenv
import os

import streamlit as st
from langchain_community.llms import Ollama
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.vectorstores import FAISS
from langchain_classic.chains import RetrievalQA


start_time = time.perf_counter()
load_dotenv()

DATA_FILE = os.getenv("DATA_FILE")
data_string = ""

# Step 1: Load from DATA_FILE path
if DATA_FILE and os.path.exists(DATA_FILE):
    st.sidebar.success(f"✅ Loading data from: {DATA_FILE}")
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data_string = f.read()
    except Exception as e:
        st.sidebar.error(f"❌ Error reading {DATA_FILE}: {e}")
        st.stop()
else:
    st.sidebar.error(f"❌ File not found: {DATA_FILE}")
    st.sidebar.info("Make sure DATA_FILE is set in .env and points to a valid file")
    st.stop()

st.sidebar.write(f"📄 File size: {len(data_string):,} characters {data_string}")

splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=50, separators=["\n\n", "\n", " ", ""])
chunks = splitter.split_text(data_string)

# --- Step 2: Embeddings & Vectorstore ---
# Cache this so it doesn't reload on every UI click
@st.cache_resource
def init_vectorstore():
    embeddings = OllamaEmbeddings(model=f"{os.getenv("OLLAMA_EMBEDDINGS", "all-minilm:l6-v2")}")
    # Using FAISS with Normalize_L2=True makes distance easier to calculate
    return FAISS.from_texts(chunks, embeddings)

vectorstore = init_vectorstore()

# --- Step 3: Create RAG pipeline ---
# ollama_llm = Ollama(model=f"{os.getenv("OLLAMA_MODEL", "gemma3:latest")}")
# qa = RetrievalQA.from_chain_type(llm=ollama_llm,
#                                  retriever=vectorstore.as_retriever())
llm = ChatOllama(model=f"{os.getenv("OLLAMA_MODEL", "gemma3:latest")}", temperature=0.2)

system_prompt = (
    "You are a strict customer support bot. Use the following context to answer. "
    "If the answer isn't in the context, say you don't know.\n\n{context}"
)
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

# New way to create chains (RetrievalQA is being deprecated)
combine_docs_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(vectorstore.as_retriever(search_kwargs={"k": 3}), combine_docs_chain)

CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
def query_with_confidence(query: str, vectorstore_obj, threshold: float = CONFIDENCE_THRESHOLD):
    # Retrieve documents with scores
    results_with_scores = vectorstore_obj.similarity_search_with_score(query, k=3)

    if not results_with_scores:
        return None, 0.0

    # FAISS returns distances, convert to similarity (lower distance = higher similarity)
    # Distance range is typically 0-2 for normalized embeddings
    # Convert: similarity = 1 - (distance / 2)
    best_doc, best_distance = results_with_scores[0]
    best_similarity = 1 - (best_distance / 2)

    return results_with_scores, best_similarity

# --- Step 4: Streamlit UI ---
st.title("🥣 Question Meeeeee!!!")
query = st.text_input("Enter your query:")

if query:
    with st.spinner("Searching knowledge base..."):
        # Similarity search with score
        docs_and_scores = vectorstore.similarity_search_with_score(query, k=1)

        # FAISS distance: lower is better.
        # For all-minilm, a distance < 1.0 is usually a decent match.
        distance = docs_and_scores[0][1]
        confidence = max(0, 1 - (distance / 1.5))  # Approximate normalization

        if confidence < CONFIDENCE_THRESHOLD:
            response_text = "I'm sorry, I don't have information on that topic in my database."
        else:
            result = rag_chain.invoke({"input": query})
            response_text = result["answer"]

    end_time = time.perf_counter()
    elapsed = end_time - start_time
    st.chat_message("assistant").write(response_text)

    # Metrics Panel
    st.markdown(f"""
    <div style="
        background-color: #d1e3f3; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid #2e77d0;
        color: #1e3a5f;
        font-family: sans-serif;
        line-height: 1.6;
    ">
        <b>📊 Confidence Score:</b> {confidence:.2%}<br>
        <b>⏱️ Time Elapsed:</b> {elapsed:.4f}s<br>
        <b>🧠 Model:</b> {os.getenv("OLLAMA_MODEL")}<br>
        <b>🔗 Embedding:</b> {os.getenv("OLLAMA_EMBEDDINGS")}
    </div>
    """, unsafe_allow_html=True)

# if query:
#     with st.spinner("Thinking..."):
#         results, confidence = query_with_confidence(query, vectorstore)
#         if confidence < CONFIDENCE_THRESHOLD:
#             response = "I don't know - this information isn't in my knowledge base."
#         else:
#             response = qa.run(query)
#         end = time.perf_counter()
#         elapsed = end - start
#     st.success(f"{response}")
#
#     query = ""
#     info_html = f"""
#     <div style="
#         background-color: #d1e3f3;
#         padding: 15px;
#         border-radius: 10px;
#         border-left: 5px solid #2e77d0;
#         color: #1e3a5f;
#         font-family: sans-serif;
#         line-height: 1.6;
#     ">
#         <b>📊 Confidence Score:</b> {confidence:.2%}<br>
#         <b>⏱️ Time Elapsed:</b> {elapsed:.4f}s<br>
#         <b>🧠 Model:</b> {os.getenv("OLLAMA_MODEL")}<br>
#         <b>🔗 Embedding:</b> {os.getenv("OLLAMA_EMBEDDINGS")}
#     </div>
#     """
#     # Render it
#     st.markdown(info_html, unsafe_allow_html=True)