# TCK JSON-RPC server for hiero-sdk-python.
# Built from the repository root: docker build -f tck/Dockerfile .
FROM python:3.12-slim-bookworm

COPY --from=docker.io/astral/uv:latest /uv /uvx /bin/

# The project uses pdm-backend with `source = "scm"`, so a version must be
# supplied explicitly - the build context has no usable git metadata.
ENV PDM_BUILD_SCM_VERSION=0.1.0

# Bind to all interfaces so the server is reachable from the runner.
ENV TCK_HOST=0.0.0.0
ENV TCK_PORT=8544

WORKDIR /app

COPY . .

# --all-groups pulls in grpcio-tools (dev group), required by generate_proto.py.
# --all-extras pulls in flask (tck extra), required by the server itself.
RUN uv sync --frozen --all-groups --all-extras
RUN uv run --no-sync generate_proto.py

EXPOSE 8544

CMD ["uv", "run", "--no-sync", "python", "-m", "tck"]
