server {
    listen 80;
    server_name hhectare.com;

    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name hhectare.com;

    ssl_certificate /etc/letsencrypt/live/hhectare.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/hhectare.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    client_max_body_size 50M;
    client_body_timeout 300s;

    location /static/ {
        alias /app/static/;
    }

    location /media/ {
        alias /app/media/;
        client_max_body_size 50M;
    }

    location / {
        proxy_pass http://web:8000;
        include /etc/nginx/proxy_params;
        client_max_body_size 50M;
    }
}
