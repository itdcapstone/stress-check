# Use a Python base image
FROM python:3.10-slim  

# Install dependencies for pywinpty (Rust and Cargo)
RUN apt-get update && \
    apt-get install -y curl build-essential && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    export PATH="$PATH:/root/.cargo/bin"  # Install Rust and Cargo

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . /app/

# Set the FLASK_APP environment variable to point to the server.app
ENV FLASK_APP=server.app

# Expose the port Flask will run on
EXPOSE 5000

# Set the command to run the Flask app
CMD ["flask", "run", "--host=0.0.0.0"]
