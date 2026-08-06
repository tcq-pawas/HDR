server {
    listen 80;
    server_name x-realtors.in;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name x-realtors.in;

    #ssl_certificate /etc/nginx/ssl/fullchain.pem;
    #ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    ssl_certificate /etc/letsencrypt/live/x-realtors.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/x-realtors.in/privkey.pem;


    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    # Allow large property image / document uploads (default nginx limit is 1m)
    client_max_body_size 50M;
    client_body_timeout 300s;

    location /static/ {
        # Serve Django STATIC_ROOT (collectstatic output)
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
