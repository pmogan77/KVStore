FROM python:3.11-slim

WORKDIR /app

COPY store.py api.py test_store.py ./

# Install Flask only
RUN pip install --no-cache-dir Flask==2.3.2 pytest

EXPOSE 5000

CMD ["python", "api.py"]
