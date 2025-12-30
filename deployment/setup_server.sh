#!/bin/bash

# Deployment Setup Script
# Run this script with sudo privileges

set -e

echo "Installing Nginx and Supervisor..."
sudo apt-get update
sudo apt-get install -y nginx supervisor

echo "Copying Supervisor Configuration..."
if [ -f "supervisor_villen.conf" ]; then
    sudo cp supervisor_villen.conf /etc/supervisor/conf.d/villen.conf
    echo "Supervisor config copied."
else
    echo "Error: supervisor_villen.conf not found!"
    exit 1
fi

echo "Copying Nginx Configuration..."
if [ -f "nginx_villen.conf" ]; then
    sudo cp nginx_villen.conf /etc/nginx/sites-available/villen
    # Remove default link if exists
    if [ -f "/etc/nginx/sites-enabled/default" ]; then
        sudo rm /etc/nginx/sites-enabled/default
    fi
    # Create symlink
    if [ ! -f "/etc/nginx/sites-enabled/villen" ]; then
        sudo ln -s /etc/nginx/sites-available/villen /etc/nginx/sites-enabled/villen
    fi
    echo "Nginx config copied and linked."
else
    echo "Error: nginx_villen.conf not found!"
    exit 1
fi

echo "Creating Log Directory..."
if [ ! -d "/var/log/villen" ]; then
    sudo mkdir -p /var/log/villen
    sudo chown -R www-data:www-data /var/log/villen
    sudo chmod -R 755 /var/log/villen
fi

echo "Reloading Services..."
sudo supervisorctl reread
sudo supervisorctl update
sudo systemctl restart supervisor
sudo nginx -t && sudo systemctl restart nginx

echo "Deployment Setup Complete!"
echo "Check status with: sudo supervisorctl status"
