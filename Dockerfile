FROM python:3.9-slim

# Install dependencies
RUN apt-get update && apt-get install -y python3-venv

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . /app

# Expose the port Streamlit runs on
EXPOSE 8000

# Command to run the app
CMD ["python3", "app.py"]
