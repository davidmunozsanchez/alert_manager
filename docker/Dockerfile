FROM python:3.11-slim

WORKDIR /src

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./scr ./scr

 
# COPY start.sh /scr/start.sh
# RUN chmod +x /scr/start.sh

# CMD ["/app/start.sh"]
