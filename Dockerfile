FROM python:3

ENV PYTHONUNBUFFERED 1
RUN groupadd -r technician && useradd --no-log-init -r -g technician technician
WORKDIR /usr/src/code
COPY . .
RUN pip install -r requirements.txt

RUN chown -R technician:technician /usr/src/code
USER technician

CMD ["/usr/src/code/prod_start.sh"]
