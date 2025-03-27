from collections import defaultdict
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_deepseek_response(video_title, user_triggers):
    endpoint = os.getenv("AZURE_MODELS_ENDPOINT")
    model_name = "DeepSeek-R1"

    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(os.getenv("AZURE_AI_KEY")),
    )

    response = client.complete(
        messages=[
            SystemMessage(content="You are an assistant that helps users avoid disturbing content in videos by identifying psychological triggers based on user input. Keep the response short and to the point."),
            UserMessage(content=f"Explain why a music video {video_title} may be distrubring for someone who is sensitive to seeing {', '.join(user_triggers)}")
        ],
        max_tokens=500,
        model=model_name,
        stream=True,
    )
    return response


def filter_thinking_stream(response):
    """Generator that filters <think>...</think> tags from the DeepSeek response stream"""
    inside_thinking = False
    accumulated_text = ""
    
    for update in response:
        if update.choices and update.choices[0].delta:
            chunk = update.choices[0].delta.content or ""
            accumulated_text += chunk
            
            # Process all complete tags
            while True:
                if not inside_thinking:
                    think_start = accumulated_text.find("<think>")
                    if think_start == -1:
                        break
                    
                    # Yield content before the tag
                    if think_start > 0:
                        yield accumulated_text[:think_start]
                    accumulated_text = accumulated_text[think_start + 7:]
                    inside_thinking = True
                else:
                    think_end = accumulated_text.find("</think>")
                    if think_end == -1:
                        break
                    
                    # Skip the thinking content
                    accumulated_text = accumulated_text[think_end + 8:]
                    inside_thinking = False
            
            # Yield any remaining text if we're not in a thinking block
            if not inside_thinking and "<think>" not in accumulated_text:
                yield accumulated_text
                accumulated_text = ""
