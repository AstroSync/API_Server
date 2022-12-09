#
FROM python:3.10

#
WORKDIR /api_server

COPY ./api_server /api_server/api_server

RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false
COPY ./pyproject.toml /api_server
COPY ./poetry.lock /api_server
RUN poetry install

CMD uvicorn api_server.main:app --proxy-headers --host 0.0.0.0 --port 8080
