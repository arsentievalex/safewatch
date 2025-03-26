import streamlit as st
from llm_inference import get_deepseek_response, filter_thinking_stream
from utils import parse_json_triggers, load_css, is_valid_url, save_json, add_entry_json
from yt_download import download_youtube_video
from azure_storage import upload_mp4_to_azure_blob
from content_understanding import send_video_to_analyzer
import json
from dotenv import load_dotenv
import os

# Page configuration
st.set_page_config(
    page_title="SafeWatch",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Load environment variables
load_dotenv()

# Initialize session state for storing persistent data
if 'user_triggers' not in st.session_state:
    # Default lists for each user
    st.session_state.user_triggers = {
        "John": ["Needles", "Explosions", "Spiders"],
        "Steph": ["Car crash", "Drowning"]
    }

# @st.cache_data
# def parse_triggers(json_response):
#     return parse_json_triggers(json_response)


# User profiles
user_profiles = {
    "John": {"avatar": "https://randomuser.me/api/portraits/men/1.jpg"},
    "Steph": {"avatar": "https://randomuser.me/api/portraits/women/1.jpg"},
}

# Read the CSS from your style.css file
load_css("style.css")

st.markdown("<div style='display: flex; align-items: center;'><div class='header'>SafeWatch</div> <div style='color: white; font-weight: bold; font-size: 40px; margin-left: 10px;'> - Personalized trigger warnings for video content</div></div>", unsafe_allow_html=True)
st.write('')
st.write('')

# Sidebar - User profile and settings
with st.sidebar:
    st.subheader("User Profile")
    
    # User selection
    selected_user = st.selectbox("Who's watching?", list(user_profiles.keys()))
    
    # Display user profile
    st.markdown(
        f"""
        <div class='user-profile'>
            <img src='{user_profiles[selected_user]["avatar"]}' class='user-avatar'>
            <div>
                <strong>{selected_user}</strong><br>
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )

    st.divider()
    st.subheader("Content Preferences")

    # Full list of triggers (you may have a larger predefined list)
    all_triggers = st.session_state.user_triggers[selected_user]

    # Use a separate session state key to track currently selected triggers
    if f"{selected_user}_selected_triggers" not in st.session_state:
        st.session_state[f"{selected_user}_selected_triggers"] = all_triggers.copy()  # Start with all selected

    # Display pills with the option to unselect/select triggers dynamically
    trigger_selection = st.pills(
        label="Selected Triggers",
        options=all_triggers,  # Keep all triggers available for selection
        default=st.session_state[f"{selected_user}_selected_triggers"],
        selection_mode="multi"
    )

    # Update session state if selection changes
    st.session_state[f"{selected_user}_selected_triggers"] = trigger_selection

    st.divider()
    st.subheader("Add Video")

    new_video_url = st.text_input("Enter YouTube video URL:")

    if st.button("Add", type="primary"):
        # Check if the URL is valid
        if is_valid_url(new_video_url):
            with st.spinner("Processing a new video..."):

                # Download the video
                file_path = download_youtube_video(url=new_video_url, max_length=300)
                file_name = os.path.basename(file_path).replace(".mp4", "")

                # Upload to Azure Blob Storage
                CONNECTION_STRING = os.getenv("AZURE_BLOB_CONNECTION_STRING")
                CONTAINER_NAME = "hackathonfiles"
                blob_data = upload_mp4_to_azure_blob(
                    file_path, 
                    connection_string=CONNECTION_STRING,
                    container_name=CONTAINER_NAME
                )

                # Get the URLs for the uploaded video
                https_saas_url = blob_data['https_sas_url']
                # Delete uploaded video locally
                os.remove(file_path)

                # Send the video to the Content Understanding analyzer
                endpoint = os.getenv("AZURE_AI_ENDPOINT")
                subscription_key = os.getenv("AZURE_AI_KEY")
                # Send the video for analysis
                analyzer_response = send_video_to_analyzer(endpoint, subscription_key, "triggers_analyzer", https_saas_url)
                if analyzer_response:
                    # Save the final analysis result to a JSON file
                    save_json(analyzer_response, f"video_analysis/{file_name}.json")
                
                new_entry = {
                    "url": new_video_url,
                    "json_file": f"{file_name}.json",
                    "title": file_name
                }
                # Add the new entry to the processed videos JSON file
                add_entry_json("video_analysis/processed_videos.json", new_entry)
                
                # Parse triggers for the new video
                unique_triggers, filtered_events = parse_json_triggers(f"video_analysis/{file_name}.json")
                
                # Add to session state videos
                st.session_state.videos[new_video_url] = {
                    **new_entry,
                    'unique_triggers': unique_triggers,
                    'filtered_events': filtered_events,
                    'ai_response': None
                }


def initialize_video_data():
    """Initialize video data in session state if not already present."""
    if 'videos' not in st.session_state:
        st.session_state.videos = {}
    
    # Always load from the JSON file to ensure all videos are included
    with open("video_analysis/processed_videos.json", "r") as file:
        processed_videos = json.load(file)
    
    for video in processed_videos:
        url = video['url']
        
        # Only add if not already in session state
        if url not in st.session_state.videos:
            # Parse triggers for each video
            unique_triggers, filtered_events = parse_json_triggers(f"video_analysis/{video['json_file']}")
            
            st.session_state.videos[url] = {
                **video,  # Include original video metadata
                'unique_triggers': unique_triggers,
                'filtered_events': filtered_events,
                'ai_response': None
            }
    
    # Initialize clicked video tracker
    if 'clicked_video' not in st.session_state:
        st.session_state.clicked_video = None


def generate_ai_response(video_data, unique_user_triggers):
    """
    Generate or retrieve AI response for a specific video.
    
    Args:
        video_data (dict): Dictionary containing video metadata
        unique_user_triggers (list): List of user-selected triggers
    
    Returns:
        str: AI-generated response about video triggers
    """
    # Check if response is already in cache
    if video_data['ai_response']:
        return video_data['ai_response']
    
    # Generate new response
    response = get_deepseek_response(
        video_data['title'], 
        unique_user_triggers
    )
    
    def collect_response(response_stream):
        full_response = ""
        for chunk in filter_thinking_stream(response_stream):
            full_response += chunk
            yield chunk
        
        # Cache the full response
        video_data['ai_response'] = full_response
    
    return collect_response(response)


def render_video_grid(num_columns=3):
    """Render video grid with trigger warnings and AI analysis."""
    # Ensure video data is initialized
    initialize_video_data()
    
    st.subheader("Your Videos")
    
    # Create columns dynamically
    columns = st.columns(num_columns)
    
    # Iterate through videos
    for idx, (url, video_data) in enumerate(st.session_state.videos.items()):
        with columns[idx % num_columns]:
            with st.container(border=True):
                # Display video
                st.video(url)
                
                # Check user triggers
                unique_triggers = video_data['unique_triggers']
                filtered_events = video_data['filtered_events']
                
                # Determine if video has user-selected triggers
                has_user_triggers = (
                    len(unique_triggers) > 0 and 
                    any(trigger in st.session_state[f"{selected_user}_selected_triggers"] 
                        for trigger in unique_triggers.keys())
                )
                
                # Render trigger warnings or no triggers found
                if not has_user_triggers:
                    st.write("")
                    st.write("")
                    st.write("✅ No triggers found")
                    st.write("")
                    st.write("")
                else:
                    # Filter and display triggers
                    unique_user_triggers = [
                        trigger for trigger in unique_triggers.keys() 
                        if trigger in st.session_state[f"{selected_user}_selected_triggers"]
                    ]
                    trigger_list = ", ".join(sorted(unique_user_triggers))
                    
                    st.write(f"❗ Trigger Warning: {trigger_list}")
                    
                    with st.expander('See More'):
                        # Filter events for user's selected triggers
                        filtered_user_events = [
                            event for event in filtered_events 
                            if event['trigger'] in st.session_state[f"{selected_user}_selected_triggers"]
                        ]
                        
                        # Display trigger events
                        st.write(f"All triggers chronologically ({len(filtered_user_events)} events):")
                        for event in filtered_user_events:
                            st.write(f"{event['trigger']} at {event['timestamp']}")
                        
                        st.divider()
                        st.write("Why this video may be disturbing for me?")
                        
                        # Use a unique key for each button
                        button_key = f"ask_ai_{url}"
                        
                        if st.button("Ask AI", key=button_key, icon="🪄"):
                            st.session_state.clicked_video = url
                        
                        # Generate or display AI response
                        if st.session_state.clicked_video == url:
                            with st.spinner("Thinking..."):
                                st.write_stream(
                                    generate_ai_response(
                                        video_data, 
                                        unique_user_triggers
                                    )
                                )

# Call the function to render videos
render_video_grid()




# List of video URLs and corresponding json responses from Content Understanding endpoint, and YouTube video titles
# videos = [
#     ("https://www.youtube.com/watch?v=u9WgtlgGAgs", "response_the_cardigans.json", "The Cardigans - My Favourite Game"),
#     ("https://www.youtube.com/watch?v=HUHC9tYz8ik", "response_billie_eilish.json", "Billie Eilish - bury a friend)"),
#     ("https://www.youtube.com/watch?v=L5uV3gmOH9g", "response_teardrops.json", "Bring Me The Horizon - Teardrops"),
#     ("https://www.youtube.com/watch?v=-KT-r2vHeMM", "response_marcy_playground.json", "Marcy Playground - Sex & Candy"),
#     ("https://www.youtube.com/watch?v=q3zqJs7JUCQ", "response_taylor_swift.json", "Taylor Swift - Fortnight (feat. Post Malone)"),
#     ("https://www.youtube.com/watch?v=W3q8Od5qJio", "response_rammstein.json", "Rammstein - Du Hast"),
# ]

# # Initialize session state for video data if not already present
# if 'video_data' not in st.session_state:
#     st.session_state.video_data = {}
    
#     # Pre-process all video data once to avoid reprocessing on reruns
#     for idx, (url, jsn, title) in enumerate(videos):
#         video_id = f"video_{idx}"
#         unique_triggers, filtered_events = parse_triggers(jsn)
        
#         st.session_state.video_data[video_id] = {
#             'url': url,
#             'json_file': jsn,
#             'title': title,
#             'unique_triggers': unique_triggers,
#             'filtered_events': filtered_events,
#             'ai_response': None,  # To store AI responses
#             'show_ai_response': False  # Flag to track if AI response should be shown
#         }

# # Track which video's AI button was clicked
# if 'clicked_video' not in st.session_state:
#     st.session_state.clicked_video = None

# st.subheader("Your Videos")

# # Create columns dynamically (2 per row)
# columns = st.columns(2)

# # Iterate over videos and place each one in the appropriate column
# for idx in range(len(videos)):
#     video_id = f"video_{idx}"
#     video_data = st.session_state.video_data[video_id]
    
#     with columns[idx % 2]:  # Distribute videos in columns cyclically
#         with st.container(border=True):
#             st.video(video_data['url'])
            
#             unique_triggers = video_data['unique_triggers']
#             filtered_events = video_data['filtered_events']
            
#             # Check if any triggers match user's selected triggers
#             has_user_triggers = len(unique_triggers) > 0 and any(trigger in st.session_state[f"{selected_user}_selected_triggers"] for trigger in unique_triggers.keys())
            
#             if not has_user_triggers:
#                 st.write("")
#                 st.write("")
#                 st.write("✅ No triggers found")
#                 st.write("")
#                 st.write("")
#             else:
#                 # Filter triggers to keep only those that are in the user's list
#                 unique_user_triggers = [trigger for trigger in unique_triggers.keys() if trigger in st.session_state[f"{selected_user}_selected_triggers"]]
#                 trigger_list = ", ".join(sorted(unique_user_triggers))
                
#                 st.write(f"❗ Trigger Warning: {trigger_list}")
                
#                 with st.expander('See More'):
#                     # Filter events to keep only those that are in the user's list
#                     filtered_user_events = [event for event in filtered_events if event['trigger'] in st.session_state[f"{selected_user}_selected_triggers"]]
                    
#                     # Display all events chronologically
#                     st.write(f"All triggers chronologically ({len(filtered_user_events)} events):")
#                     for event in filtered_user_events:
#                         st.write(f"{event['trigger']} at {event['timestamp']}")

#                     st.divider()
#                     st.write("Why this video may be disturbing for me?")
                    
#                     # Use a unique key for each button
#                     button_key = f"ask_ai_{video_id}"
                    
#                     if st.button("Ask AI", key=button_key, icon="🪄"):
#                         st.session_state.clicked_video = video_id
                    
#                     # Check if this video's button was clicked
#                     if st.session_state.clicked_video == video_id:
#                         # Only generate response if not already generated
#                         if not video_data['ai_response']:
#                             response = get_deepseek_response(video_data['title'], unique_user_triggers)
                            
#                             # Create a container for the response
#                             response_container = st.empty()
                            
#                             with st.spinner("Thinking..."):
#                                 # Stream and collect the response
#                                 st.write_stream(filter_thinking_stream(response))
#                         else:
#                             # If response was already generated, just display it
#                             st.write(video_data['ai_response'])