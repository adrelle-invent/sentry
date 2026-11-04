FROM nginx:alpine

# Install OpenSSL
RUN apk add --no-cache openssl

# Generate self-signed SSL certificate at build time
RUN mkdir -p /etc/nginx/certs && \
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/certs/local.key \
    -out /etc/nginx/certs/local.crt \
    -subj "/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

# Copy configuration
COPY default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
