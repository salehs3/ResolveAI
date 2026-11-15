from pydantic import BaseModel
from openai import OpenAI
from openai import RateLimitError, APIConnectionError
from dotenv import  load_dotenv

from typing import Literal

load_dotenv()
client = OpenAI()

class ComplaintDetails(BaseModel):
    order_id : int | None
    product : str | None
    issue_type : Literal["shipping", "refund", "damaged_product", "other"]
    urgency : Literal["low", "medium", "high"]
    requested_action : str|None


def extract_complaint(complaint: str):
   
    response = client.responses.parse(
    model ="gpt-4o-mini",
    text_format = ComplaintDetails,
    instructions = "Extract only information that is explicitly supported by the customer complaint. "
                    "If a specific detail (such as order ID, product name, or requested action) is not mentioned or cannot "
                    "be directly verified from the text, set that field to null or None. Do not assume, guess, or invent any details.",
    input=complaint
    )

    parsed = response.output_parsed

    if parsed is None:
        raise ValueError("Could not extract complaint details")

    return parsed

# complaint1 = "My laptop from order 1 hasn't arrived. Can you check its status?"
# complaint2 = "I received a damaged PS5 from order 3 and need a replacement urgently."
# complaint3 = "I was charged twice for my purchase and want a refund."

# print(extract_complaint(complaint1))
# print(extract_complaint(complaint2))
# print(extract_complaint(complaint3))
