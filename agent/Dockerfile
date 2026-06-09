FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /srv

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY entrypoint.sh ./

RUN uv pip install --system . \
    && chmod +x entrypoint.sh

EXPOSE 8000
CMD ["./entrypoint.sh"]
