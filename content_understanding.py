import requests
import json
import time
import os
from dotenv import load_dotenv
from utils import load_json, save_json

# Load environment variables from .env file
load_dotenv()


# Create a custom analyzer
def create_analyzer(endpoint, subscription_key, analyzer_id, json_file):
    request_body = load_json(json_file)  # Load JSON from file
    url = f"{endpoint}/contentunderstanding/analyzers/{analyzer_id}?api-version=2024-12-01-preview"
    headers = {"Ocp-Apim-Subscription-Key": subscription_key, "Content-Type": "application/json"}

    response = requests.put(url, headers=headers, json=request_body)
    if response.status_code == 201:
        print("Analyzer creation request submitted successfully.")
        operation_url = response.headers["Operation-Location"]
        return poll_status(operation_url, headers, "analyzer creation")
    else:
        print(f"Failed to create analyzer. Status code: {response.status_code}")
        print(response.json())
        return None


# Send a video for analysis
def send_video_to_analyzer(endpoint, subscription_key, analyzer_id, file_url):
    url = f"{endpoint}/contentunderstanding/analyzers/{analyzer_id}:analyze?api-version=2024-12-01-preview"
    headers = {"Ocp-Apim-Subscription-Key": subscription_key, "Content-Type": "application/json"}
    request_body = {"url": file_url}

    response = requests.post(url, headers=headers, json=request_body)
    if response.status_code == 202:
        print("Video analysis request accepted.")
        operation_url = response.headers["Operation-Location"]
        return poll_status(operation_url, headers, "video analysis")
    else:
        print(f"Failed to submit video for analysis. Status code: {response.status_code}")
        print(response.json())
        return None


# Poll the operation status periodically (replaces time.sleep)
def poll_status(operation_url, headers, operation_type):
    print(f"Polling {operation_type} status. This may take some time...")
    while True:
        response = requests.get(operation_url, headers=headers)
        if response.status_code == 200:
            status_data = response.json()
            status = status_data.get("status")
            if status == "Succeeded":
                print(f"{operation_type.capitalize()} completed successfully!")
                return status_data  # Return final result data
            elif status in ["Running", "NotStarted"]:
                print(f"{operation_type.capitalize()} in progress... Checking again in 30 seconds.")
                time.sleep(30)
            else:
                print(f"{operation_type.capitalize()} failed with status: {status}")
                return None
        else:
            print(f"Failed to poll {operation_type} status. Status code: {response.status_code}")
            print(response.json())
            return None


