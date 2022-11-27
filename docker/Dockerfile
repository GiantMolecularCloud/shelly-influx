FROM python:3.10-slim
LABEL maintainer="@GiantMolecularCloud"

WORKDIR /src
COPY docker/requirements.txt .
COPY ./src /src

RUN pip config set global.no-cache-dir false
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN rm requirements.txt

ENV PYTHONUNBUFFERED=1

CMD ["python", "/src/run.py", "/config/config.yaml"]