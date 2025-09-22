# --- Ensure environment variables are loaded FIRST ---
from dotenv import load_dotenv
load_dotenv()
# ----------------------------------------------------

import os
import pandas as pd
from typing import List, Tuple, Any
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
# The correct LangChain class for Sentence Transformers
from langchain_community.embeddings import SentenceTransformerEmbeddings 
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.documents import Document # For creating synthetic documents

# --- Configuration ---
# Gets the correct host.docker.internal URL from the .env file
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL")
MODEL_NAME = "mistral" # Model confirmed by you
VECTOR_DB_PATH = "./chroma_db"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2" 

# RAG components will be stored here after first successful initialization
RAG_CHAIN = None
RAG_ERROR = None
VECTOR_STORE = None


# --- Data Loading and Splitting ---

def load_and_split_data(finops_file: str, csv_file: str) -> List[Document]:
    """Loads and splits the FinOps tips and synthetic data into documents."""
    documents = []
    
    # 1. Load FinOps Tips (Unstructured Data)
    try:
        loader = TextLoader(finops_file)
        documents.extend(loader.load())
    except FileNotFoundError:
        print(f"Warning: FinOps tips file not found at {finops_file}.")

    # 2. Load Synthetic Data (Structured Data as Text)
    try:
        df = pd.read_csv(csv_file)
        # Convert the first 50 rows of data into a text document
        data_text = "FinOps Billing Data Summary (First 50 Records):\n"
        data_text += df.head(50).to_string(index=False)
        
        data_document = Document(
            page_content=data_text, 
            metadata={"source": "synthetic_data_summary"}
        )
        documents.append(data_document)
    except Exception as e:
        print(f"Error processing structured data for RAG: {e}")

    # Split documents into smaller, manageable chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=150
    )
    return text_splitter.split_documents(documents)

# --- RAG Initialization (The safe, lazy function) ---

def get_rag_chain() -> Tuple[Any, str]:
    """
    Initializes the RAG chain on first call (lazy-loading).
    Returns (rag_chain, error_message).
    """
    global RAG_CHAIN, RAG_ERROR, VECTOR_STORE
    
    if RAG_CHAIN:
        return RAG_CHAIN, RAG_ERROR # Already initialized

    print("Attempting RAG System Initialization (First call)...")
    
    # 1. Component Check
    # OLLAMA_BASE_URL is now correctly loaded from the .env file.
    if not OLLAMA_BASE_URL or 'host.docker.internal' not in OLLAMA_BASE_URL:
        RAG_ERROR = "OLLAMA_BASE_URL is missing or incorrect. Must be http://host.docker.internal:11434 in .env."
        return None, RAG_ERROR
        
    try:
        # 2. Embeddings (Downloads model on first run if needed)
        embeddings = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        
        # 3. Vector Store
        VECTOR_STORE = Chroma(
            persist_directory=VECTOR_DB_PATH, 
            embedding_function=embeddings
        )
        
        # 4. Initialize Ollama LLM
        # This is the line that will now succeed since OLLAMA_BASE_URL is properly loaded.
        llm = Ollama(model=MODEL_NAME, base_url=OLLAMA_BASE_URL)
        
        # 5. Build/Load Vector Store Data
        current_count = VECTOR_STORE._collection.count()
        if current_count == 0:
            print("Vector store is empty. Loading data and creating embeddings...")
            documents = load_and_split_data("data/finops_tips.md", "data/synthetic_data.csv")
            if documents:
                VECTOR_STORE.add_documents(documents)
                print(f"Vector store initialized with {len(documents)} documents.")
            else:
                print("No documents to load. RAG will not function.")

        # 6. Setup LangChain RAG Chain
        system_template = (
            "***ROLE and CONSTRAINTS***\n"
    "You are an **AI FinOps Copilot** and your sole purpose is to assist with cloud cost management and optimization. "
    "Your response MUST be based ONLY on the provided context. If the context does not contain the necessary information, state clearly that you cannot answer the question based on the available data.\n"
    
    "***OUTPUT FORMAT and TONE***\n"
    "1. Maintain a professional, concise, and data-driven tone.\n"
    "2. If applicable, summarize the relevant data or FinOps principle BEFORE giving the recommendation.\n"
    "3. Every final response MUST conclude with a bulleted list containing 1 to 3 specific, actionable next steps for cost optimization.\n"

    "***CONTEXT AND QUESTION***\n"
    "The context includes general FinOps best practices and recent synthetic billing data summaries (CSV records).\n"
    "\n\nContext:\n{context}\n\nQuestion: {input}"
        )
        prompt = ChatPromptTemplate.from_template(system_template)
        retriever = VECTOR_STORE.as_retriever()
        document_chain = create_stuff_documents_chain(llm, prompt)
        RAG_CHAIN = create_retrieval_chain(retriever, document_chain)

        print("RAG System Initialized successfully.")
        return RAG_CHAIN, None

    except Exception as e:
        # Catch any failure during RAG setup and store the error
        RAG_ERROR = f"RAG Initialization Failed: {type(e).__name__}: {e}"
        print(f"FATAL RAG ERROR: {RAG_ERROR}")
        return None, RAG_ERROR