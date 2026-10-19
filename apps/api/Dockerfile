FROM ubuntu:24.04 AS simc-build
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    git make g++ ca-certificates \
    && rm -rf /var/lib/apt/lists/*
ARG SIMC_COMMIT=d91a57073f82f023076e6e3737389bb86193a0f9
WORKDIR /src
RUN git clone --depth 1 --branch midnight https://github.com/simulationcraft/simc.git . \
    && git fetch --depth 1 origin ${SIMC_COMMIT} \
    && git checkout ${SIMC_COMMIT}
WORKDIR /src/engine
RUN make SC_NO_NETWORKING=1 CXX=g++ -j"$(nproc)"

FROM python:3.12-slim
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    libstdc++6 build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY apps/api /app/apps/api
COPY apps/worker /app/apps/worker
COPY packages/game-data /opt/game-data
COPY --from=simc-build /src/engine/simc /usr/local/bin/simc

RUN pip install --no-cache-dir -e "/app/apps/api[dev]" psycopg[binary]

ENV PYTHONPATH=/app/apps/api
ENV SIMC_PATH=/usr/local/bin/simc
ENV GAME_DATA_DIR=/opt/game-data
ENV SIMC_PROFILES_DIR=/opt/game-data/presets/12.1.5

WORKDIR /app/apps/api
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
