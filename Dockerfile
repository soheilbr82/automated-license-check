FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install toml pip-licenses

ENTRYPOINT ["python", "license_checker.py"]