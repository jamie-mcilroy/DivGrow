
# Use Python 3.10 base image
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

# Run the entrypoint script
ENTRYPOINT ["./entrypoint.sh"]
