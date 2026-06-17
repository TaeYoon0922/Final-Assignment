FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# 0.0.0.0 바인딩 필수 (컨테이너 외부에서 접근 가능하도록)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
