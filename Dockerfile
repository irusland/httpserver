FROM python:3.7.9

COPY requirements.txt app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
COPY . .


EXPOSE 8000
CMD python httpserver.py -c config.json -l console
