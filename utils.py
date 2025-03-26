import json
import re
from collections import defaultdict
import os
import streamlit as st
import requests


def time_to_seconds(time_str):
    """Convert MM:SS format to total seconds"""
    minutes, seconds = map(int, time_str.split(':'))
    return minutes * 60 + seconds


def format_trigger_name(trigger):
    """Format trigger name by replacing underscores with spaces and capitalizing first letter"""
    # Replace underscores with spaces
    formatted = trigger.replace('_', ' ')
    # Capitalize first letter
    formatted = formatted[0].upper() + formatted[1:]
    return formatted


def parse_json_triggers(file_path):
    """
    Parse JSON file and extract fields with valueBoolean = true along with their timestamps.
    Filter out duplicate triggers that occur within 5 seconds of each other.
    Exclude any triggers that happen at 00:00 as these are likely bugs.
    Format trigger names by replacing underscores with spaces and capitalizing first letter.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        - Dictionary of unique event types and their timestamps
        - List of all unique event timestamps with their trigger types
    """
    # Read and parse JSON file
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    raw_triggers = []
    
    # Process each content entry
    for content in data['result']['contents']:
        # Extract start time from markdown using regex
        markdown = content['markdown']
        time_range_match = re.search(r'# Shot (\d+:\d+)\.\d+ => \d+:\d+\.\d+', markdown)
        
        if not time_range_match:
            continue
            
        # Round to seconds by capturing only minutes and seconds
        start_time = time_range_match.group(1)
        
        # Skip if the timestamp is 00:00 (likely a bug)
        if start_time == "00:00":
            continue
        
        # Check all fields for boolean values set to true
        for field_name, field_value in content['fields'].items():
            # Skip the timestamps field
            if field_name == 'timestamps':
                continue
                
            # Check if this field has valueBoolean set to true
            if field_value.get('type') == 'boolean' and field_value.get('valueBoolean') == True:
                # Format the trigger name
                formatted_trigger = format_trigger_name(field_name)
                
                raw_triggers.append({
                    'trigger': formatted_trigger,
                    'original_trigger': field_name,
                    'timestamp': start_time,
                    'seconds': time_to_seconds(start_time)
                })
    
    # Sort triggers by timestamp
    raw_triggers.sort(key=lambda x: x['seconds'])
    
    # Filter out duplicate triggers within 5 seconds
    filtered_triggers = []
    last_trigger_time = {}  # Store the last time each trigger type was seen
    
    for trigger in raw_triggers:
        trigger_type = trigger['original_trigger']  # Use original for comparison
        formatted_type = trigger['trigger']
        current_time = trigger['seconds']
        
        # If we haven't seen this trigger type before, or it's been more than 5 seconds
        if (trigger_type not in last_trigger_time or 
            current_time - last_trigger_time[trigger_type] >= 5):
            filtered_triggers.append({
                'trigger': formatted_type,
                'timestamp': trigger['timestamp']
            })
            last_trigger_time[trigger_type] = current_time
    
    # Create a dictionary of unique trigger types with their timestamps
    unique_triggers = defaultdict(list)
    for event in filtered_triggers:
        unique_triggers[event['trigger']].append(event['timestamp'])
    
    return unique_triggers, filtered_triggers


def load_css(file_name):
    with open("style.css") as css_file:
        css = css_file.read()

    # Use st.html to include the CSS
    st.html(f"""
        <style>
        {css}
        </style>
    """)


def is_valid_url(url, timeout=5):
    """
    Check URL validity by attempting to connect and get a 200 OK response.
    
    Args:
        url (str): The URL to validate
        timeout (int, optional): Connection timeout in seconds. Defaults to 5.
    
    Returns:
        bool: True if URL is valid and returns 200 OK, False otherwise
    """
    try:
        # Add default scheme if not present
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        # Send a HEAD request to minimize data transfer
        response = requests.head(url, timeout=timeout)
        
        # Check if status code is 200
        return response.status_code == 200
    
    except (requests.ConnectionError, 
            requests.Timeout, 
            requests.RequestException):
        return False


# Function to load JSON from a file
def load_json(filename):
    with open(filename, 'r') as file:
        return json.load(file)


# Function to save JSON to a file
def save_json(data, filename):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)
    print(f"Response saved locally as {filename}")


def add_entry_json(file_path, new_entry):
    """
    Add a new entry to an existing JSON file.
    """
    # Read the existing JSON file
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Append the new entry
    data.append(new_entry)

    # Write the updated data back to the file
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)