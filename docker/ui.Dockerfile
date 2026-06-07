FROM python:3.10-slim-bookwarm

WORKDIR /app

RUN apt-get update && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-ui.txt .

RUN pip install --no-cache-dir --prefer-binary -r requirements-ui.txt

COPY ui/ ./ui/

ENV PYTHONUNBUFFERED=1
ENV PORT=8501

EXPOSE 8501

CMD ["streamlit", "run", "ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]