FROM nginx:1.25-alpine

ENV APP_HOST=web
ENV APP_PORT=8000
ENV LISTEN_PORT=80

COPY ./start.sh /start.sh
RUN sed -i 's/\r$//' /start.sh && \
    chmod +x /start.sh

RUN touch /etc/nginx/conf.d/default.conf

COPY ./proxy_params /etc/nginx/
COPY ./default.conf.tpl /etc/nginx/

# Remove default nginx content to reduce image size
RUN rm -rf /usr/share/nginx/html/* && \
    rm -rf /var/cache/apk/*

ENTRYPOINT [ "/bin/sh", "/start.sh" ]
