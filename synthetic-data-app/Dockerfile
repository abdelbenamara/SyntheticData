FROM python:3.8-slim-buster

WORKDIR /app

COPY . .

RUN chmod +x production/setup.sh \
    && chmod +x production/start.sh \
    && production/setup.sh

ENTRYPOINT ["production/start.sh"]
