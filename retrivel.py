import re
from typing import List
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

from dotenv import load_dotenv

load_dotenv()

# ================= EMBEDDINGS =================
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

""" embeddings = OllamaEmbeddings(
    model="nomic-embed-text"
) """

""" embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
) """


vectorstore = Chroma(
    persist_directory="./chroma_store",
    embedding_function=embeddings
)


# ================= HYBRID RETRIEVER =================
class HybridRetriever:
    def __init__(
        self,
        vectorstore,
        k: int = 4,
        fetch_k: int = 20,
        lambda_mult: float = 0.4
    ):
        self.vectorstore = vectorstore
        self.k = k
        self.fetch_k = fetch_k
        self.lambda_mult = lambda_mult

    def _extract_exact_terms(self, query: str) -> List[str]:
        """
        Extract numeric + unit phrases exactly as they appear in text
        Example:
        - 5.5 mm
        - 10 bar
        - 200 rpm
        """
        pattern = r"\b\d+(?:\.\d+)?\s?(?:mm|cm|m|bar|rpm|kg|°c|kw|nm)\b"
        return re.findall(pattern, query.lower())

    def invoke(self, query: str) -> List[Document]:
        # 1️⃣ Semantic retrieval (MMR)
        semantic_docs = self.vectorstore.max_marginal_relevance_search(
            query=query,
            k=self.k,
            fetch_k=self.fetch_k,
            lambda_mult=self.lambda_mult,
        )

        # 2️⃣ Extract numeric constraints
        exact_terms = self._extract_exact_terms(query)

        if not exact_terms:
            return semantic_docs

        # 3️⃣ Prefer documents containing numeric constraints
        strong_matches = []
        weak_matches = []

        for doc in semantic_docs:
            text = doc.page_content.lower()
            if any(term in text for term in exact_terms):
                strong_matches.append(doc)
            else:
                weak_matches.append(doc)

        # 4️⃣ Return strong matches first, fallback if needed
        if strong_matches:
            return strong_matches

        return semantic_docs


# ================= PUBLIC RETRIEVER =================
retriever = HybridRetriever(
    vectorstore=vectorstore,
    k=4,
    fetch_k=20,
    lambda_mult=0.5
)


def retriver(query: str) -> List[Document]:

    print("retriver ")
    docs = retriever.invoke(query)
    print("retrived docs",docs)

    """ for d in docs:
        print("\nPage:", d.metadata.get("page"))
        print(d.page_content[:500]) """

    return docs
