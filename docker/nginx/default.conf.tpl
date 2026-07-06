server {
    listen 80;
    server_name heydayrealty.in;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name heydayrealty.in;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    #ssl_certificate /etc/letsencrypt/live/heydayrealty.in/fullchain.pem;
    #ssl_certificate_key /etc/letsencrypt/live/heydayrealty.in/privkey.pem;


    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    location /static/ {
        alias /app/staticfiles/;
    }

    location /media/ {
        alias /app/media/;
    }

    location / {
        proxy_pass http://web:8000;
        include /etc/nginx/proxy_params;
    }
}

