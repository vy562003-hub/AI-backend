from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from outputschema import RAGAnswer
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from retrivel import retriver
from dotenv import load_dotenv
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder



load_dotenv()


# ===============================
# LLM SETUP
# ===============================
endpoint = HuggingFaceEndpoint(
    repo_id="openai/gpt-oss-120b",
    provider="novita",
    temperature=0.2,
)

llm = ChatHuggingFace(llm=endpoint)


""" llm = ChatOllama(
    model="qwen2.5:0.5b",     # or llama3:8b / mistral / qwen2.5
    temperature=0.2,
)
 """

""" llm = ChatOpenAI(
    model="gpt-4o-mini",  # fast + cheap + very reliable JSON
    temperature=0.2
) """
""" llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",   # fast + cheap (recommended)
    temperature=0.2,
)
 """

 # ===============================
# SESSION MEMORY STORE
# ===============================

session_store = {}

def get_session_history(session_id: str):

    if session_id not in session_store:
        session_store[session_id] = ChatMessageHistory()

    return session_store[session_id]



# ===============================
# OUTPUT PARSER
# ===============================
output_parser = JsonOutputParser(pydantic_object=RAGAnswer)


# ===============================
# PROMPTS
# ===============================

rag_prompt = ChatPromptTemplate.from_messages([

    # System message (rules)
    (
        "system",
        """
You are a technical assistant answering questions from an engine manual.

RULES:
- Use ONLY the provided context.
- If the answer is not present, say "I don't know".
- Do NOT guess.

{format_instructions}
"""
    ),

    # Chat history goes here (memory)
    MessagesPlaceholder("history"),

    # Human message (context + question)
    (
        "human",
        """
Context:
{context}

Question:
{question}
"""
    )
])

general_prompt = PromptTemplate(
    input_variables=["question"],
    template="""
You are a helpful and knowledgeable AI assistant.

Answer the question clearly and accurately.

Question:
{question}

Answer:
"""
)


# ===============================
# HELPERS
# ===============================
def build_context(docs):
    return "\n\n".join(
        f"(Page {d.metadata.get('page')}) {d.page_content}"
        for d in docs
    )


def extract_pages(docs):
    """
    Collect unique page numbers used in retrieval
    """
    pages = []
    for d in docs:
        page = d.metadata.get("page")
        if page is not None and page not in pages:
            pages.append(page)
    return pages


# ===============================
# FINAL ORCHESTRATION
# ===============================
def answer_query(query: str) -> RAGAnswer:
    """
    1. Try RAG
    2. If RAG says 'I don't know' → fallback to general LLM
    """
    print('anser query')

    # ---------- RETRIEVE ----------
    docs = retriver(query)

    print("retrived documents")

    # ---------- RAG MODE ----------
    if docs:
        print("if docs available")
        context = build_context(docs)

        """ prompt = rag_prompt.format(
            context=context,
            question=query,
            format_instructions=output_parser.get_format_instructions()
        )

        print("prompt" )

        raw = llm.invoke(prompt) """

        rag_chain = rag_prompt | llm

        chat_with_memory = RunnableWithMessageHistory(
            rag_chain,
            get_session_history,
            input_messages_key="question",
            history_messages_key="history"
        )

        raw = chat_with_memory.invoke(
            {
                "context": context,
                "question": query,
                "format_instructions": output_parser.get_format_instructions()
            },
            config={
                "configurable": {
                "session_id": "default"
            }
            }
        )


        print("raw",raw)

        raw_text = raw.content.strip()

        print("RAW LLM OUTPUT:\n", raw_text)

        try:
            print('parsing started')
            parsed: RAGAnswer = output_parser.parse(raw_text)
            print('parsing completed ' ,parsed)

            if parsed['answer'].lower().strip() != "i don't know":
                parsed['pages'] = extract_pages(docs)
                return parsed

        except Exception as e:
            print("⚠️ Parsing failed:", e)

            """ if raw_text:
                parsed = RAGAnswer(
                answer=raw_text,
                pages=None
            )
            else:
                parsed = None

            # ---------- POST-PARSE VALIDATION ----------
            if parsed:
                answer_text = parsed.answer.strip().lower()

            # Treat "i don't know" as RAG miss
            if answer_text != "i don't know":
                parsed.pages = extract_pages(docs)
                return parsed """

    # ---------- GENERAL FALLBACK ----------
    raw = llm.invoke(
        general_prompt.format(question=query)
    )

    print("general raw",raw)


    return RAGAnswer(
        answer=raw.content.strip(),
        pages=None
    )


# ===============================
# USAGE
# ===============================
if __name__ == "__main__":
    query = "fetchdata from page 211"
    result = answer_query(query)
    print("result",result)
