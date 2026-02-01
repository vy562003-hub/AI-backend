from pydantic import BaseModel, Field
from typing import List, Optional


class PageReference(BaseModel):
    page: int = Field(
        description="Page number in the original PDF"
    )
    path: str = Field(
        description="Server path or URL to the rendered PDF page"
    )


class RAGAnswer(BaseModel):
    answer: str = Field(
        description="Final natural language answer to the user's question"
    )

    pages: Optional[List[PageReference]] = Field(
        default=None,
        description="Pages used to answer the question with server paths"
    )
