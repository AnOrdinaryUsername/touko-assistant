import os
import requests
import logging
import json

from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

def conversate_with_user(messages: List[Dict[str, Any]]) -> str:
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
                "content": ("You are a virtual assistant named Touko. "
                             "Keep responses succinct and concise as possible.")
            },
            *messages
        ],
        "max_tokens": 150
    }

    logging.debug(json.dumps(data, indent=2))

    # See https://docs.mistral.ai/api/#operation/createChatCompletion
    mistral_url = "https://api.mistral.ai/v1/chat/completions"
    
    try:
        response = requests.post(mistral_url, json=data, headers=headers)
        response.raise_for_status()
        chat_response = response.json()

        logging.debug(f"Time elapsed: {response.elapsed}")
        logging.debug(json.dumps(chat_response, indent=2))

    except requests.exceptions.HTTPError as error:
        logging.error(error.strerror)
        return "Someone tell Vedal there is a problem with my AI"

    return chat_response['choices'][0]['message']['content']
