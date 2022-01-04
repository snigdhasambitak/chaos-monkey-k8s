FROM python:3.9.5-alpine3.13

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r /app/requirements.txt

ADD main.py /app/main.py

ADD ./k8s_pod_killer /app/k8s_pod_killer

ENTRYPOINT ["/usr/local/bin/python", "-u", "/app/main.py"]
