FROM python:3.10

EXPOSE 30000

WORKDIR /home/app

# This is needed for scripts to be able to import from test_observer directory
ENV PYTHONPATH=/home/app

COPY poetry.lock .

COPY pyproject.toml .

RUN pip3 install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

COPY . .

CMD [ "uvicorn",  "test_observer.main:app", "--host", "0.0.0.0", "--port", "30000", "--reload" ]
