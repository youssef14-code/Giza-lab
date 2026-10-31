from pydantic import BaseModel, Field


class ResultResponse(BaseModel):
    """
    Response schema when communicating with the user or requesting missing test result inquiry details.
    """

    reply: str = Field(
        description="The conversational text response to send back to the user in polite Egyptian Arabic."
    )

    summary: str = Field(
        description="Updated concise summary of the conversation state and collected patient details."
    )