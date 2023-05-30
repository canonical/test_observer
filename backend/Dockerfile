FROM python:3.10

EXPOSE 30000

WORKDIR /home/app

COPY poetry.lock .

COPY pyproject.toml .

RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --without dev

COPY . .

CMD [ "uvicorn",  "src.main:app", "--host", "0.0.0.0", "--port", "30000", "--reload" ]