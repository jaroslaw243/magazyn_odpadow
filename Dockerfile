FROM python:3

ENV PYTHONUNBUFFERED 1
RUN mkdir /code
RUN groupadd -r technician && useradd --no-log-init -r -g technician technician
WORKDIR /code
COPY . /code/
COPY ./prod_start.sh /code/
RUN pip install -r requirements.txt

RUN chown -R technician:technician /code
USER technician

CMD ["/code/prod_start.sh"]