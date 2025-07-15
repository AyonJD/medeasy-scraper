#!/bin/bash

# MedEasy Data Extractor VPS Setup Script
# This script sets up a VPS for running the data extraction system

set -e

echo "🚀 Setting up MedEasy Data Extractor on VPS..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Update system
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install essential packages
print_status "Installing essential packages..."
sudo apt install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release

# Install Docker
print_status "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    print_status "Docker installed successfully"
else
    print_status "Docker is already installed"
fi

# Install Docker Compose
print_status "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_status "Docker Compose installed successfully"
else
    print_status "Docker Compose is already installed"
fi

# Create application directory
print_status "Creating application directory..."
APP_DIR="$HOME/medeasy_extractor"
mkdir -p $APP_DIR
cd $APP_DIR

# Clone repository (if not already present)
if [ ! -d ".git" ]; then
    print_status "Please clone your repository to this directory"
    print_warning "Run: git clone <your-repo-url> ."
    print_warning "Then run this script again"
    exit 1
fi

# Create environment file
print_status "Creating environment file..."
if [ ! -f ".env" ]; then
    cp env.example .env
    print_status "Environment file created. Please edit .env with your configuration"
else
    print_status "Environment file already exists"
fi

# Create logs directory
print_status "Creating logs directory..."
mkdir -p logs

# Set proper permissions
print_status "Setting permissions..."
sudo chown -R $USER:$USER $APP_DIR
chmod +x scripts/*.sh

# Create systemd service for auto-start (optional)
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/medeasy-extractor.service > /dev/null <<EOF
[Unit]
Description=MedEasy Data Extractor
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Enable service
sudo systemctl enable medeasy-extractor.service

# Create monitoring script
print_status "Creating monitoring script..."
cat > monitor.sh << 'EOF'
#!/bin/bash

echo "=== MedEasy Data Extractor Status ==="
echo

# Check if containers are running
echo "Container Status:"
docker-compose ps
echo

# Check API health
echo "API Health:"
curl -s http://localhost:8000/health | jq . 2>/dev/null || echo "API not responding"
echo

# Check scraping status
echo "Scraping Status:"
curl -s http://localhost:8000/scrape/status | jq . 2>/dev/null || echo "Could not get scraping status"
echo

# Show recent logs
echo "Recent Logs:"
docker-compose logs --tail=10 api
EOF

chmod +x monitor.sh

# Create backup script
print_status "Creating backup script..."
cat > backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="medeasy_backup_$DATE.sql"

mkdir -p $BACKUP_DIR

echo "Creating database backup..."
docker-compose exec -T postgres pg_dump -U medeasy_user medeasy_db > $BACKUP_DIR/$BACKUP_FILE

echo "Backup created: $BACKUP_DIR/$BACKUP_FILE"

# Keep only last 7 backups
ls -t $BACKUP_DIR/medeasy_backup_*.sql | tail -n +8 | xargs -r rm

echo "Backup completed successfully!"
EOF

chmod +x backup.sh

# Create start script
print_status "Creating start script..."
cat > start.sh << 'EOF'
#!/bin/bash

echo "Starting MedEasy Data Extractor..."
docker-compose up -d

echo "Waiting for services to start..."
sleep 10

echo "Checking service status..."
./monitor.sh

echo "To start scraping, run:"
echo "curl -X POST 'http://localhost:8000/scrape/start?resume=true'"
EOF

chmod +x start.sh

# Create stop script
print_status "Creating stop script..."
cat > stop.sh << 'EOF'
#!/bin/bash

echo "Stopping MedEasy Data Extractor..."
docker-compose down

echo "Services stopped successfully!"
EOF

chmod +x stop.sh

# Print completion message
echo
print_status "🎉 VPS setup completed successfully!"
echo
echo "Next steps:"
echo "1. Edit .env file with your configuration:"
echo "   nano .env"
echo
echo "2. Start the services:"
echo "   ./start.sh"
echo
echo "3. Start scraping:"
echo "   curl -X POST 'http://localhost:8000/scrape/start?resume=true'"
echo
echo "4. Monitor progress:"
echo "   ./monitor.sh"
echo
echo "5. View logs:"
echo "   docker-compose logs -f api"
echo
echo "Useful commands:"
echo "  ./monitor.sh    - Check system status"
echo "  ./backup.sh     - Create database backup"
echo "  ./start.sh      - Start services"
echo "  ./stop.sh       - Stop services"
echo
print_warning "Don't forget to:"
echo "  - Configure firewall rules"
echo "  - Set up SSL certificates if needed"
echo "  - Configure regular backups"
echo "  - Monitor system resources"
echo
print_status "Setup complete! 🚀" 