FROM alpine:3.3

RUN apk add --no-cache python gcc python-dev libffi-dev openssl-dev musl-dev && \
    python -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip install --upgrade pip setuptools && \
    rm -r /root/.cache 

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
RUN apk del gcc python-dev libffi-dev openssl-dev musl-dev
EXPOSE 8421
CMD ["/usr/bin/python", "web.py"]
