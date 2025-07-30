# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /chatbot

# Copy the current directory contents into the container
COPY . /chatbot

# Install dependencies
RUN pip install Flask
RUN pip install PyJWT
RUN pip install langgraph
RUN pip install langchain[openai]
RUN pip install langchain-community

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run the application
CMD ["python", "run.py"]
