cp zscaler-cert.pem /usr/local/share/ca-certificates/zscaler-cert.crt
RUN apt-get update && \
    apt-get install -y curl ca-certificates && \
    update-ca-certificates

pip install certifi pytest
