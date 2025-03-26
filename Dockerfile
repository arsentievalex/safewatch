FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . /app

# Expose the port Streamlit runs on
EXPOSE 8080

# Command to run the Streamlit app
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080"]