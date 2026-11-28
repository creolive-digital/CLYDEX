# syntax=docker/dockerfile:1
# Operator selects and pins a reviewed Python 3.13 Debian 12 image digest.
ARG PYTHON_IMAGE
FROM ${PYTHON_IMAGE}
ARG ACCEPT_ODBC_EULA=NO
RUN test "$ACCEPT_ODBC_EULA" = YES && apt-get update && apt-get install -y --no-install-recommends ca-certificates curl unixodbc libgssapi-krb5-2 \
 && curl --fail --silent --show-error https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb -o /tmp/microsoft.deb \
 && dpkg -i /tmp/microsoft.deb && apt-get update \
 && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
 && rm -f /tmp/microsoft.deb && rm -rf /var/lib/apt/lists/* \
 && groupadd --gid 10001 clydex && useradd --uid 10001 --gid clydex --no-create-home clydex
RUN --mount=type=secret,id=sql_ca,required=true cp /run/secrets/sql_ca /usr/local/share/ca-certificates/sql-ca.crt \
 && update-ca-certificates
WORKDIR /opt/clydex
COPY pyproject.toml /opt/clydex/pyproject.toml
COPY src /opt/clydex/src
COPY cloud /opt/clydex/cloud
RUN python -m pip install --no-cache-dir -r cloud/requirements-runtime.lock \
 && python -m pip install --no-cache-dir --no-deps . ./cloud
USER 10001:10001
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
# TLS terminates at the private reverse proxy. Only the explicit proxy subnet is trusted.
CMD ["python", "-m", "uvicorn", "clydex_cloud.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log", "--proxy-headers", "--forwarded-allow-ips", "172.31.55.0/28"]
