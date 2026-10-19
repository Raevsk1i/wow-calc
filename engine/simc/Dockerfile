# SimulationCraft worker image (GPL-3.0). Run as a separate process — do not link into proprietary code.
FROM ubuntu:24.04 AS build

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

FROM ubuntu:24.04
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    libstdc++6 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /src/engine/simc /usr/local/bin/simc
COPY --from=build /src/profiles /opt/simc/profiles

ENV SIMC_PATH=/usr/local/bin/simc
ENV SIMC_PROFILES_DIR=/opt/simc/profiles

ENTRYPOINT ["/usr/local/bin/simc"]
