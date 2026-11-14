FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends nginx util-linux && rm -rf /var/lib/apt/lists/* && useradd -u 1000 proxyuser
WORKDIR /app
COPY backend.py nginx.conf /app/
RUN chmod -R a+rX /app
CMD ["sleep", "infinity"]
