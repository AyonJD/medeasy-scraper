# MedEasy Data Extractor

A comprehensive data extraction system for scraping medicine data from MedEasy (https://medeasy.health). This system is designed to handle large-scale data extraction with resume capabilities, duplicate prevention, and robust error handling.

## Features

- **Large-scale scraping**: Designed to handle 29K+ medicines efficiently
- **Resume capability**: Automatically resumes from where it left off if interrupted
- **Duplicate prevention**: Prevents duplicate entries in the database
- **Robust error handling**: Comprehensive retry logic and error recovery
- **Real-time monitoring**: API endpoints for monitoring scraping progress
- **Flexible data model**: Stores both structured and raw data for maximum flexibility
- **Multiple scraping methods**: Supports both HTTP requests and Selenium for JavaScript-heavy pages
- **Rate limiting**: Configurable delays to be respectful to the target website

## Technology Stack

- **Backend**: Python 3.11, FastAPI
- **Database**: PostgreSQL (chosen for ACID compliance and better performance with structured data)
- **Caching/Queue**: Redis
- **Web Scraping**: BeautifulSoup4, Selenium, aiohttp
- **Containerization**: Docker & Docker Compose
- **Logging**: Loguru

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL (for local development)

### Using Docker (Recommended for VPS)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd data_extractor
   ```

2. **Copy environment file**
   ```bash
   cp env.example .env
   ```

3. **Start the services**
   ```bash
   docker-compose up -d
   ```

4. **Check the API**
   ```bash
   curl http://localhost:8000/health
   ```

5. **Start scraping**
   ```bash
   curl -X POST "http://localhost:8000/scrape/start?resume=true"
   ```

### Local Development Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up PostgreSQL**
   ```bash
   # Create database and user
   createdb medeasy_db
   createuser medeasy_user
   psql -c "ALTER USER medeasy_user PASSWORD 'medeasy_password';"
   psql -c "GRANT ALL PRIVILEGES ON DATABASE medeasy_db TO medeasy_user;"
   ```

3. **Set up Redis**
   ```bash
   # Install Redis (Ubuntu/Debian)
   sudo apt-get install redis-server
   sudo systemctl start redis-server
   ```

4. **Configure environment**
   ```bash
   cp env.example .env
   # Edit .env with your database credentials
   ```

5. **Initialize database**
   ```bash
   python -c "from database.connection import init_db; init_db()"
   ```

6. **Run the API**
   ```bash
   uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

7. **Run scraper directly (optional)**
   ```bash
   python scripts/run_scraper.py
   ```

## API Endpoints

### Scraping Management

- `POST /scrape/start?resume=true` - Start scraping process
- `POST /scrape/stop` - Stop scraping process
- `GET /scrape/status` - Get current scraping status and progress

### Data Access

- `GET /medicines` - Get medicines with pagination and filtering
- `GET /medicines/{id}` - Get specific medicine details
- `GET /statistics` - Get scraping and data statistics
- `GET /logs` - Get scraping logs

### System

- `GET /` - API information
- `GET /health` - Health check

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@localhost/medeasy_db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `API_HOST` | API host address | `0.0.0.0` |
| `API_PORT` | API port | `8000` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `DELAY_BETWEEN_REQUESTS` | Delay between requests (seconds) | `1` |
| `MAX_RETRIES` | Maximum retry attempts | `3` |
| `TIMEOUT` | Request timeout (seconds) | `30` |
| `SELENIUM_HEADLESS` | Run Selenium in headless mode | `true` |

### Scraping Configuration

The scraper is designed to be respectful to the target website:

- Configurable delays between requests
- User agent rotation
- Retry logic with exponential backoff
- Rate limiting
- Error handling and logging

## Database Schema

### Medicines Table

Stores comprehensive medicine information:

- Basic info: name, generic name, brand name, manufacturer
- Product details: strength, dosage form, pack size, price
- Medical info: description, indications, contraindications, side effects
- Metadata: product code, category, URLs, timestamps
- Raw data: Complete HTML content for flexibility

### Scraping Progress Table

Tracks scraping progress and enables resume functionality:

- Current page and total pages
- Processed items count
- Status tracking (running, completed, failed, paused)
- Resume data storage

### Scraping Logs Table

Comprehensive logging for monitoring and debugging:

- Log levels (INFO, WARNING, ERROR, DEBUG)
- Task-specific logging
- URL tracking for debugging

## Monitoring and Management

### Real-time Progress Monitoring

```bash
# Check scraping status
curl http://localhost:8000/scrape/status

# Get statistics
curl http://localhost:8000/statistics

# View recent logs
curl http://localhost:8000/logs
```

### Database Queries

```sql
-- Get total medicines count
SELECT COUNT(*) FROM medicines;

-- Get medicines by manufacturer
SELECT name, manufacturer, price FROM medicines WHERE manufacturer ILIKE '%Square%';

-- Get recent medicines
SELECT name, created_at FROM medicines ORDER BY created_at DESC LIMIT 10;

-- Get price statistics
SELECT MIN(price), MAX(price), AVG(price) FROM medicines WHERE price IS NOT NULL;
```

## Deployment on VPS

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

### 2. Application Deployment

```bash
# Clone repository
git clone <repository-url>
cd data_extractor

# Configure environment
cp env.example .env
# Edit .env with your VPS details

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f api
```

### 3. Start Scraping

```bash
# Start the scraping process
curl -X POST "http://your-vps-ip:8000/scrape/start?resume=true"

# Monitor progress
curl http://your-vps-ip:8000/scrape/status
```

## Performance Optimization

### Database Optimization

- Indexes on frequently queried columns
- Connection pooling
- Regular maintenance and vacuuming

### Scraping Optimization

- Concurrent requests with rate limiting
- Efficient HTML parsing
- Memory management for large datasets

### Monitoring

- Health checks for all services
- Comprehensive logging
- Performance metrics tracking

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL service status
   - Verify connection string in .env
   - Ensure database and user exist

2. **Scraping Stuck**
   - Check logs: `curl http://localhost:8000/logs`
   - Restart scraping: `curl -X POST "http://localhost:8000/scrape/stop" && curl -X POST "http://localhost:8000/scrape/start?resume=true"`

3. **Memory Issues**
   - Reduce `BATCH_SIZE` in config
   - Increase system memory
   - Monitor with `docker stats`

### Log Analysis

```bash
# View application logs
docker-compose logs api

# View database logs
docker-compose logs postgres

# Check scraping progress
curl http://localhost:8000/scrape/status
```

## Data Export

### Export to CSV

```python
import pandas as pd
from database.connection import SessionLocal
from database.models import Medicine

db = SessionLocal()
medicines = db.query(Medicine).all()

data = []
for med in medicines:
    data.append({
        'name': med.name,
        'generic_name': med.generic_name,
        'manufacturer': med.manufacturer,
        'price': med.price,
        'category': med.category
    })

df = pd.DataFrame(data)
df.to_csv('medicines_export.csv', index=False)
```

### Database Backup

```bash
# Create backup
docker-compose exec postgres pg_dump -U medeasy_user medeasy_db > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U medeasy_user medeasy_db < backup.sql
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and research purposes only. Please ensure you comply with the target website's terms of service and robots.txt file. Use responsibly and respect rate limits to avoid overwhelming the target server. 