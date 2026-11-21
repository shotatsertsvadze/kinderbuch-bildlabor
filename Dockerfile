# Öffentliche, nur lesbare Demo. Bauen aus dem committeten Stand: deploy/deploy.sh
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never UV_NO_CACHE=1

WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev --no-install-project

# Nur was die Demo zur Laufzeit braucht: kein docs/ (historische Prüfakten), keine Tests,
# keine Arbeitskopien außer dem kuratierten demo/
COPY app.py ./
COPY .streamlit/config.toml .streamlit/config.toml
COPY src src
COPY static static
COPY sammlung sammlung
COPY Kinderbuch_Bildlabor_Start Kinderbuch_Bildlabor_Start
COPY demo demo
COPY rechtliches rechtliches
RUN uv sync --locked --no-dev && rm /usr/local/bin/uv

# Der Bau bricht ab, solange Demonstrationsstand oder Pflichtangaben offen sind
RUN BILDLABOR_DEMO=1 .venv/bin/python -m kinderbuch_bildlabor.demo_data check \
    && ! grep -rn "OFFEN:" rechtliches

RUN useradd --system --no-create-home --uid 10001 demo
USER demo
ENV BILDLABOR_DEMO=1 PYTHONDONTWRITEBYTECODE=1 HOME=/tmp
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s \
    CMD ["/app/.venv/bin/python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health')"]
# hideWelcomeMessage: sonst fragt Streamlit bei jedem Start checkip.amazonaws.com ab
CMD ["/app/.venv/bin/streamlit", "run", "app.py", \
     "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", \
     "--server.fileWatcherType=none", "--server.runOnSave=false", "--server.maxUploadSize=1", \
     "--client.showErrorDetails=none", "--client.toolbarMode=viewer", \
     "--browser.gatherUsageStats=false", "--logger.hideWelcomeMessage=true"]
