#!/bin/bash

# SYNX Independent VPS Deployer
echo "Starting SYNX deployment on independent VPS..."

# 1. Update and install dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv ffmpeg nginx git

# 2. Setup project directory
mkdir -p /var/www/synx
cd /var/www/synx

# 3. Clone repository (assuming public for setup)
git clone https://github.com/neyzenrose/synx_app.git .

# 4. Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# 5. Setup Systemd Service
cat <<EOF | sudo tee /etc/systemd/system/synx.service
[Unit]
Description=Gunicorn instance to serve SYNX App
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/synx
Environment="PATH=/var/www/synx/venv/bin"
ExecStart=/var/www/synx/venv/bin/gunicorn --workers 3 --bind unix:synx.sock api.index:app

[Install]
WantedBy=multi-user.target
EOF

# 6. Setup Nginx
cat <<EOF | sudo tee /etc/nginx/sites-available/synx
server {
    listen 80;
    server_name synxai.ca www.synxai.ca;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/synx/synx.sock;
    }

    location /static {
        alias /var/www/synx/api/static;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/synx /etc/nginx/sites-enabled
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# 7. Start and Enable Service
sudo systemctl start synx
sudo systemctl enable synx

echo "SYNX Deployment Complete! Please set up SSL using certbot if domain is pointed."
