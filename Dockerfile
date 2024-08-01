FROM python:3.10-alpine
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt --no-cache-dir

EXPOSE 80 5000
CMD ["gunicorn" , "app:app" ,"--bind" , "0.0.0.0:5000" ,"--timeout", "300"]
