from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        description="Question to ask from uploaded documents.",
        examples=["What are leave policies?"]
    )