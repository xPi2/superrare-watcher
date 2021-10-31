FROM python:3.9

WORKDIR /usr/tracker

COPY dist .
COPY scrapy.cfg .

RUN pip3 install --no-cache-dir *.whl

CMD ["scrapy"]