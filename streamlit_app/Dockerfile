# syntax=docker/dockerfile:1
FROM python:3.11-slim

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m appuser
WORKDIR /app

# copy requirements and wheelhouse first to leverage cache
COPY requirements.txt /app/requirements.txt
COPY wheelhouse /wheels

# install deps from local wheels when available; fallback to PyPI otherwise
RUN pip install --no-cache-dir -U pip setuptools wheel && \
    if [ -d /wheels ] && [ "$(ls -A /wheels 2>/dev/null)" ]; then \
      pip install --no-index --find-links=/wheels -r /app/requirements.txt ; \
    else \
      pip install --no-cache-dir -r /app/requirements.txt ; \
    fi

# copy rest of source
COPY . /app
RUN [ -f ./wait_for_dag.py ] && chmod +x ./wait_for_dag.py || true

USER appuser
ENV STREAMLIT_SERVER_HEADLESS=true STREAMLIT_BROWSER_GATHER_USAGE_STATS=false WAIT_FOR_DAG=yes
EXPOSE 8501
CMD ["sh","-c","if [ \"$WAIT_FOR_DAG\" = \"yes\" ] && [ -f ./wait_for_dag.py ]; then python ./wait_for_dag.py; fi; streamlit run app.py --server.address=0.0.0.0 --server.port=8501 --server.headless true"]
