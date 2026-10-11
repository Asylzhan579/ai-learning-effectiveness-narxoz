FROM python:3.12.7-slim-bookworm
WORKDIR /app
COPY . /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN python -m unittest discover -s tests -v
CMD ["python", "-m", "src.benchmark", "--config", "configs/config.json"]
