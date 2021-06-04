FROM python:3.8-slim-buster

ADD Pipfile Pipfile.lock get_walk_borme.py /app/
ADD config/ /app/config/borme-extractor
WORKDIR /app
RUN python -m pip install pipenv && python -m pipenv install --system --deploy --ignore-pipfile
ENTRYPOINT python get_walk_borme.py
