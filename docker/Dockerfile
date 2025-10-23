FROM python:3.11-slim

WORKDIR /src

COPY /docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY /src .

 
# RUN chmod +x ./start.sh

# CMD ["./start.sh"]
