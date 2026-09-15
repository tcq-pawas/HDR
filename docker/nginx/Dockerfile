FROM nginx:1.25-alpine

ENV APP_HOST=web
ENV APP_PORT=8000
ENV LISTEN_PORT=80

ARG NGINX_CONFIG

COPY ./start.sh /start.sh
COPY ${NGINX_CONFIG} /etc/nginx/templates/default.conf.template
COPY ./proxy_params /etc/nginx/proxy_params

RUN sed -i 's/\r$//' /start.sh \
    && chmod +x /start.sh \
    && rm -rf /usr/share/nginx/html/*

ENTRYPOINT [ "/bin/sh", "/start.sh" ]
