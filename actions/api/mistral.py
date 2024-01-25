import os
from dotenv import load_dotenv

from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

load_dotenv()

def rephrase_response(user_msg: str) -> str:
    """
    Docs: https://docs.mistral.ai/
    """
    api_key = os.environ["MISTRAL_API_KEY"]
    model = "mistral-tiny"

    client = MistralClient(api_key=api_key)

    chat_response = client.chat(
        model=model,
        messages=[
            ChatMessage(role="system", 
                        content="You will rephrase the following sentence."),
            ChatMessage(role="user", content=user_msg)
            ],
    )
    return chat_response.choices[0].message.content
