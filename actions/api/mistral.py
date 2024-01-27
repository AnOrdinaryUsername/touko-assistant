import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

def conversate_with_user(msg: str) -> str:
    """
    Docs: https://docs.mistral.ai/
    """
    api_key = os.environ["MISTRAL_API_KEY"]

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    """
    Mistral has 32k context (token limit)
    https://docs.mistral.ai/platform/endpoints/#generative-endpoints

    One can append multiple messages so the model can be more 
    aware of what's going on in a conversation.

    This explains it well:
    https://help.openai.com/en/articles/7042661-chatgpt-api-transition-guide
    """
    data = {
        "model": "mistral-tiny",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful and knowledgeable virtual assistant named Touko."
            },
            {
                "role": "user",
                "content": f"{msg}"
            }
        ]
    }

    # See https://docs.mistral.ai/api/#operation/createChatCompletion
    mistral_url = "https://api.mistral.ai/v1/chat/completions"
    
    try:
        response = requests.post(mistral_url, json=data, headers=headers)
        response.raise_for_status()
        chat_response = response.json()

        logging.debug(chat_response)
        logging.debug(f"Time elapsed: {response.elapsed}")
    except requests.exceptions.HTTPError as error:
        logging.error(error.strerror)
        return "Someone tell Vedal there is a problem with my AI"

    return chat_response['choices'][0]['message']['content']
