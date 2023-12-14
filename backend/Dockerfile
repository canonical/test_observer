FROM python:3.10

EXPOSE 30000

WORKDIR /home/app

ENV C3_CLIENT_ID=BuoR2ztGalNUbpo3qtLKtz8BpiryhGKxaEOWBMFu
ENV C3_CLIENT_SECRET=zYXw8xGgigJNhFdjAR6wkv69v9WQWVr3fCt1T8JSLFzusxqRjvizRzXIWjJM7zfYy2StwlHvgnsbGQTa6B2HeEKb24CiNPLpR0HYWSdPE1HEtvWuFPA2b5QmflvZhTVr

COPY poetry.lock .

COPY pyproject.toml .

RUN pip3 install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --without dev

COPY . .

CMD [ "uvicorn",  "test_observer.main:app", "--host", "0.0.0.0", "--port", "30000", "--reload" ]
