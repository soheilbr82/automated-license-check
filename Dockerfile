FROM python:3.11-slim

# Install libmagic and build-essential
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmagic1 \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a directory for the virtual environment
RUN python -m venv /venv

# # Install dependencies using the virtual environment's pip
# RUN /venv/bin/pip install --upgrade pip && \
#     /venv/bin/pip install scancode-toolkit

# Set the PATH environment variable to prioritize the virtual environment
ENV PATH="/venv/bin:$PATH"

# Activate virtual environment and install dependencies
RUN /bin/bash -c "/venv/bin/pip install --upgrade pip && source /venv/bin/activate && pip install scancode-toolkit"


# Set working directory
WORKDIR /app

# Copy your project files
COPY . /app

# # Create and activate virtual environment
# RUN python -m venv venv

# # Activate virtual environment and install dependencies
# RUN /bin/bash -c "source venv/bin/activate && pip install scancode-toolkit"

# Expose any necessary ports (if applicable)
# EXPOSE 8000

# Set the entry point
# ENTRYPOINT ["/app/venv/bin/scancode"]
ENTRYPOINT ["scancode"]
# CMD ["bash"]