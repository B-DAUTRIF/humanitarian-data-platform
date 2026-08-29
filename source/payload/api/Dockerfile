FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=65532:65532 app ./app
COPY --chown=65532:65532 static ./static
RUN mkdir -p /app/data/raw /app/execution_spool /tmp \
    && chown -R 65532:65532 /app/data /app/execution_spool /tmp \
    && chmod 0700 /app/data /app/execution_spool

EXPOSE 8080
USER 65532:65532
CMD ["uvicorn", "app.main_v6:app", "--host", "0.0.0.0", "--port", "8080"]
