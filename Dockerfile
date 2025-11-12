# Dockerfile (use BuildKit cache for pip)
# NOTE: must use BuildKit (DOCKER_BUILDKIT=1) when building

FROM quay.io/astronomer/astro-runtime:11.3.0

COPY requirements.txt /tmp/requirements.txt

# Use BuildKit cache mount so pip downloads are cached across builds
# (requires Docker BuildKit: DOCKER_BUILDKIT=1)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r /tmp/requirements.txt

# copy the rest of the app
COPY packages.txt /tmp/packages.txt
RUN if [ -s /tmp/packages.txt ]; then apt-get update && xargs -a /tmp/packages.txt apt-get install -y --no-install-recommends; rm -rf /var/lib/apt/lists/*; fi

COPY ETL /usr/local/airflow/dags/etl
COPY SQL /usr/local/airflow/dags/sql
