FROM python:3.11-slim

WORKDIR /app

# Install system deps if needed (psycopg2-binary usually ok without extras)
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the worker source
COPY src/ .

ENTRYPOINT []

# Run the worker main
CMD ["python", "main.py"]

