FROM python:3.11-slim

WORKDIR /src

COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ../src ./src

 
COPY ../src/start.sh ./src
RUN chmod +x ./src/start.sh

CMD ["./src/start.sh"]
