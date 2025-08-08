# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
ENV AZURE_SEARCH_ADMIN_KEY=${AZURE_SEARCH_ADMIN_KEY}

# Set the working directory in the container
WORKDIR /chatbot

# Copy the current directory contents into the container
COPY . /chatbot

# Install dependencies
RUN pip install Flask
RUN pip install flask-login
RUN pip install flask-bcrypt
RUN pip install PyJWT
RUN pip install langgraph
RUN pip install langchain[openai]
RUN pip install langchain-community
RUN pip install azure-search-documents

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run the application
CMD ["python", "chatbot/run.py"]
