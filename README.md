# SafeWatch - Personalized Trigger Warning System

SafeWatch is a Streamlit-based web application that provides personalized trigger warnings for video content. It analyzes videos for potentially triggering content and provides AI-powered insights for users with specific sensitivities.

## Features

- **User Profiles**: Multiple sample users for demo purposes
- **Video Analysis**: Video analysis with Azure AI Content Understanding
- **YouTube Integration**: Direct YouTube video processing and analysis
- **Real-time AI Insights**: AI-powered explanations of potentially disturbing content
- **Personalized Warnings**: Custom trigger warnings based on user preferences

## Architecture

<img src="https://i.postimg.cc/Y2nJYBsx/safewatch.png"/>

## Prerequisites

- Python 3.9+
- Azure Account with:
  - Azure AI Foundry & Content Understanding
  - Azure Blob Storage

## Installation

1. Clone the repository:
```sh
git clone <repository-url>
cd safewatch
```

2. Install dependencies:
```sh
pip install -r requirements.txt
```

3. Create a `.env` file with the following variables:
```sh
AZURE_AI_ENDPOINT=<your-azure-ai-endpoint>
AZURE_AI_KEY=<your-azure-ai-key>
AZURE_BLOB_CONNECTION_STRING=<your-blob-storage-connection-string>
AZURE_MODELS_ENDPOINT=<your-azure-foundry-endpoint>
```

## Usage

1. Start the Streamlit app:
```sh
streamlit run app.py
```

2. Select a user profile from the sidebar
3. Configure your trigger preferences
4. Add videos by pasting YouTube URLs
5. View analyzed videos with personalized trigger warnings

## Project Structure

- `app.py` - Main Streamlit application
- `content_understanding.py` - Azure AI Content Understanding integration
- `azure_storage.py` - Azure Blob Storage operations
- `llm_inference.py` - AI response generation
- `yt_download.py` - YouTube video download functionality
- `utils.py` - Utility functions
- `video_analysis/` - Processed video analysis results
- `.streamlit/` - Streamlit configuration
- `style.css` - Custom styling
