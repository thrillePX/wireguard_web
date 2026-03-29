FROM python:3.11-slim

LABEL maintainer="WireGuard Manager"
LABEL description="WireGuard Connection Manager Backend"

WORKDIR /app

RUN apt-get update && apt-get install -y \
    wireguard-tools \
    iproute2 \
    sudo \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ /app/

ENV PYTHONUNBUFFERED=1
ENV WG_PATH=/etc/wireguard

EXPOSE 5001

CMD ["python", "app.py"]
