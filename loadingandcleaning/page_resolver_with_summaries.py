from typing import Dict, List
from langchain_core.prompts import PromptTemplate
from unstructured.documents.elements import (
    Text,
    Image,
    Table,
    FigureCaption,
    NarrativeText
)

import os
from dotenv import load_dotenv
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint


load_dotenv()

# ================= MODEL =================
endpoint = HuggingFaceEndpoint(
    repo_id="Qwen/Qwen2.5-7B-Instruct",
    task="text-generation",
    temperature=0.2,
)

llm = ChatHuggingFace(llm=endpoint)


# ================= PROMPTS =================
TABLE_PROMPT = PromptTemplate(
    input_variables=["table"],
    template="""
You are a technical documentation assistant.

Summarize the table below into clear, complete, factual statements.
- Preserve all numeric values, units, ranges
- Do NOT invent data
- Do NOT omit important rows

Table:
{table}

Summary:
"""
)

IMAGE_PROMPT = PromptTemplate(
    input_variables=["context"],
    template="""
You are a technical assistant.

Using the provided image and surrounding text context, describe what the image shows.
- Be factual
- Do NOT hallucinate unseen details
- Keep it concise but informative

Context:
{context}

Image description:
"""
)

# ================= HELPERS =================
def normalize(text: str) -> str:
    return " ".join(text.split())


def is_valid_text(text: str) -> bool:
    if not text:
        return False
    if len(text) >= 20:
        return True
    return " " in text


def collect_image_context(elements: List, img_index: int) -> str:
    """
    Collect nearby text for image context.
    Priority:
    FigureCaption > NarrativeText > Text > Title/Header
    """
    context_parts = []

    # Look backward
    for i in range(img_index - 1, max(img_index - 6, -1), -1):
        el = elements[i]

        if isinstance(el, (Image, Table)):
            break

        if isinstance(el, FigureCaption):
            context_parts.insert(0, el.text)
            break

        if isinstance(el, NarrativeText):
            context_parts.insert(0, el.text)

        elif isinstance(el, Text):
            if is_valid_text(el.text):
                context_parts.insert(0, el.text)

    # Look forward
    for i in range(img_index + 1, min(img_index + 4, len(elements))):
        el = elements[i]

        if isinstance(el, (Image, Table)):
            break

        if isinstance(el, FigureCaption):
            context_parts.append(el.text)
            break

        if isinstance(el, NarrativeText):
            context_parts.append(el.text)

        elif isinstance(el, Text):
            if is_valid_text(el.text):
                context_parts.append(el.text)

    return normalize(" ".join(context_parts))


# ================= MAIN RESOLVER =================
def resolve_pages_with_summaries(
    pages: Dict[int, List],
    
) -> Dict[int, List]:

    resolved_pages = {}

    for page_num, elements in pages.items():
        resolved_elements = []

        for idx, el in enumerate(elements):

            # ---------- TABLE ----------
            if isinstance(el, Table) and el.text:
                prompt = TABLE_PROMPT.format(table=el.text)
                #summary = llm.invoke(prompt).content.strip()
                summary = llm.invoke(prompt).strip()
                print('table-summary idx:',idx,"\n",summary)
                resolved_elements.append(
                    Text(
                        text=summary,
                        metadata=el.metadata
                    )
                )
                continue

            # ---------- IMAGE ----------
            if isinstance(el, Image):
                context = collect_image_context(elements, idx)

                prompt = IMAGE_PROMPT.format(context=context)
                summary = llm.invoke(prompt).content.strip()
                #summary = llm.invoke(prompt).strip()
                print('image-summary idx:',idx,'\n',summary)
                resolved_elements.append(
                    Text(
                        text=summary,
                        metadata=el.metadata
                    )
                )
                continue

            # ---------- NORMAL TEXT ----------
            resolved_elements.append(el)

        resolved_pages[page_num] = resolved_elements
        print("resolved page-num",page_num)
    print("resolved both")
    return resolved_pages
