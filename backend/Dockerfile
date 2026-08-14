FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y libreoffice-impress \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY app ./app

EXPOSE 8000

CMD ["python", "-m", "app.main"]
