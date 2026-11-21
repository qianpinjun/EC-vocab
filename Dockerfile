FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV HOST=0.0.0.0
ENV PORT=5000
ENV DEBUG=False

EXPOSE 5000

CMD ["gunicorn", "--workers", "4", "--threads", "4", "--bind", "0.0.0.0:5000", "--timeout", "60", "wsgi:application"]
