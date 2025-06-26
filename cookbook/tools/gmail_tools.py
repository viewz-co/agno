"""
Gmail Agent that can read, draft and send emails using the Gmail.
"""

from agno.agent import Agent
from agno.models.google import Gemini
from agno.models.openai import OpenAIChat
from agno.tools.gmail import GmailTools
from pydantic import BaseModel, Field


class FindEmailOutput(BaseModel):
    message_id: str = Field(..., description="The message id of the email")
    thread_id: str = Field(..., description="The thread id of the email")
    references: str = Field(..., description="The references of the email")
    in_reply_to: str = Field(..., description="The in-reply-to of the email")
    subject: str = Field(..., description="The subject of the email")
    body: str = Field(..., description="The body of the email")


agent = Agent(
    name="Gmail Agent",
    model=OpenAIChat(id="gpt-4o"),
    tools=[GmailTools()],
    description="You are an expert Gmail Agent that can read, draft and send emails using the Gmail.",
    instructions=[
        "Based on user query, you can read, draft and send emails using Gmail.",
        "While showing email contents, you can summarize the email contents, extract key details and dates.",
        "Show the email contents in a structured markdown format.",
        "Attachments can be added to the email",
    ],
    markdown=True,
    show_tool_calls=False,
    response_model=FindEmailOutput,
)

# Example 1: Find the last email from a specific sender
email = "<replace_with_email_address>"
response: FindEmailOutput = agent.run(
    f"Find the last email from {email} along with the message id, references and in-reply-to",
    markdown=True,
    stream=True,
).content


agent.print_response(
    f"""Send an email in order to reply to the last email from {email}.
    Use the thread_id {response.thread_id} and message_id {response.in_reply_to}. The subject should be 'Re: {response.subject}' and the body should be 'Hello'""",
    markdown=True,
    stream=True,
)

# Example 2: Send a new email with attachments
# agent.print_response(
#     """Send an email to user@example.com with subject 'Subject'
#     and body 'Body' and Attach the file 'tmp/attachment.pdf'""",
#     markdown=True,
#     stream=True,
# )
