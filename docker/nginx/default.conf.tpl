server {
    listen 80;
    server_name x-realtors.in localhost;

    location /static/ {
        alias /app/static/;
    }

    location /media/ {
        alias /app/media/;
    }

    location / {
        proxy_pass http://web:8000;
        include /etc/nginx/proxy_params;
    }
}

