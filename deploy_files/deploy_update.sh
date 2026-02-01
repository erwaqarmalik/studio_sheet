#!/bin/bash
# Deploy script to update server with latest git changes

# Configuration
DROPLET_IP="165.22.214.244"
ROOT_PATH="/root/studio_sheet"
BRANCH="main"  # Change to your branch name

echo "=========================================="
echo "Deploying Latest Changes to Server"
echo "=========================================="
echo ""

# Step 1: Pull latest code
echo "STEP 1: Pulling latest code from git..."
ssh root@$DROPLET_IP "cd $ROOT_PATH && git pull origin $BRANCH"
echo "[OK] Code updated"
echo ""

# Step 2: Install/update dependencies
echo "STEP 2: Installing dependencies..."
ssh root@$DROPLET_IP "cd $ROOT_PATH && source venv/bin/activate && pip install -r requirements.txt --quiet"
echo "[OK] Dependencies updated"
echo ""

# Step 3: Run migrations
echo "STEP 3: Running database migrations..."
ssh root@$DROPLET_IP "cd $ROOT_PATH && source venv/bin/activate && python manage.py migrate"
echo "[OK] Migrations applied"
echo ""

# Step 4: Collect static files
echo "STEP 4: Collecting static files..."
ssh root@$DROPLET_IP "cd $ROOT_PATH && source venv/bin/activate && python manage.py collectstatic --noinput"
echo "[OK] Static files collected"
echo ""

# Step 5: Restart services
echo "STEP 5: Restarting services..."
ssh root@$DROPLET_IP "sudo systemctl restart passport_app_gunicorn"
ssh root@$DROPLET_IP "sudo systemctl restart passport_app_celery"
ssh root@$DROPLET_IP "sudo systemctl reload nginx"
sleep 3
echo "[OK] Services restarted"
echo ""

# Step 6: Test deployment
echo "STEP 6: Testing deployment..."
HTTP_STATUS=$(ssh root@$DROPLET_IP "curl -s -o /dev/null -w '%{http_code}' http://$DROPLET_IP")
if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "302" ]; then
    echo "[OK] Application is responding (HTTP $HTTP_STATUS)"
else
    echo "[WARNING] Application returned HTTP $HTTP_STATUS"
fi
echo ""

echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Server: http://$DROPLET_IP"
echo ""
echo "To view logs:"
echo "  ssh root@$DROPLET_IP 'tail -f $ROOT_PATH/logs/django.log'"
echo ""
