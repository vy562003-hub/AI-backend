from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import os
from dotenv import load_dotenv

load_dotenv()


# ---------- Embedding model ----------
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)



""" embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
) """

""" embeddings = OllamaEmbeddings(
    model="nomic-embed-text"
) """

# ---------- Store in Chroma ----------
def store_pages_in_vector_db(
    resolved_pages: dict,
    persist_dir: str = "../bhroma_store"
):
    """
    resolved_pages format:
    {
        page_num: [elements]   # elements are Text only (tables/images resolved)
    }
    """

    docs = []

    for page_num, elements in resolved_pages.items():
        parts = []

        for el in elements:
            if not hasattr(el, "text"):
                continue

            text = el.text.strip()
            if not text:
                continue

            parts.append(text)

        if not parts:
            continue

        page_content = "\n".join(parts)

        docs.append(
            Document(
                page_content=page_content,
                metadata={
                    "page": page_num
                }
            )
        )

    print(f"🧬 Storing {len(docs)} pages in vector DB")

    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=persist_dir
    )

    return vectorstore
