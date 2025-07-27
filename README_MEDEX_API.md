# MedEx Scraper API

A FastAPI-based REST API for controlling and monitoring the MedEx medicine scraper from [MedEx.com.bd](https://medex.com.bd/).

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the API Server
```bash
# Using uvicorn directly
uvicorn api.main_medex:app --host 0.0.0.0 --port 8000 --reload

# Or using Python
python -m uvicorn api.main_medex:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Access the API
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **API Base URL**: http://localhost:8000

## 📋 API Endpoints

### 🎯 Scraper Control

#### Start Scraper
```http
POST /scraper/start
Content-Type: application/json

{
  "headless": true,
  "test_pages": null,
  "no_resume": false
}
```

**Parameters:**
- `headless` (bool): Run browser in headless mode (default: true)
- `test_pages` (int, optional): Limit scraping to N pages for testing
- `no_resume` (bool): Start fresh without resuming (default: false)

**Example:**
```bash
# Start full scraper in headless mode
curl -X POST "http://localhost:8000/scraper/start" \
  -H "Content-Type: application/json" \
  -d '{"headless": true}'

# Test with 5 pages only
curl -X POST "http://localhost:8000/scraper/start" \
  -H "Content-Type: application/json" \
  -d '{"headless": true, "test_pages": 5}'

# Start fresh (no resume)
curl -X POST "http://localhost:8000/scraper/start" \
  -H "Content-Type: application/json" \
  -d '{"headless": true, "no_resume": true}'
```

#### Stop Scraper
```http
POST /scraper/stop
```

```bash
curl -X POST "http://localhost:8000/scraper/stop"
```

#### Get Scraper Status
```http
GET /scraper/status
```

```bash
curl "http://localhost:8000/scraper/status"
```

**Response:**
```json
{
  "running": true,
  "current_page": 15,
  "total_pages": 822,
  "processed_items": 450,
  "total_items": 24660,
  "status": "running",
  "start_time": "2025-07-27T14:30:00"
}
```

#### Get Detailed Progress
```http
GET /scraper/progress
```

```bash
curl "http://localhost:8000/scraper/progress"
```

**Response:**
```json
{
  "current_page": 15,
  "total_pages": 822,
  "page_percentage": 1.82,
  "processed_items": 450,
  "total_items": 24660,
  "item_percentage": 1.83,
  "status": "running",
  "created_at": "2025-07-27T14:30:00",
  "updated_at": "2025-07-27T14:35:00"
}
```

### 📊 Monitoring

#### Get Logs
```http
GET /scraper/logs?limit=50&level=INFO
```

**Parameters:**
- `limit` (int): Number of log entries (default: 50)
- `level` (string): Filter by level (INFO, ERROR, WARNING)

```bash
# Get last 20 logs
curl "http://localhost:8000/scraper/logs?limit=20"

# Get only errors
curl "http://localhost:8000/scraper/logs?level=ERROR"
```

#### Get Statistics
```http
GET /stats
```

```bash
curl "http://localhost:8000/stats"
```

**Response:**
```json
{
  "database": {
    "total_medicines": 1250,
    "total_images": 980,
    "recent_medicines_24h": 450,
    "unique_manufacturers": 45
  },
  "storage": {
    "html_files": 1250,
    "html_size_mb": 125.5,
    "image_files": 980,
    "image_size_mb": 45.2,
    "log_size_mb": 2.1
  },
  "scraper": {
    "running": true,
    "task_name": "medex_scraper",
    "base_url": "https://medex.com.bd"
  }
}
```

### 💊 Medicine Data

#### Get Medicines List
```http
GET /medicines?limit=20&offset=0&search=paracetamol
```

**Parameters:**
- `limit` (int): Number of medicines (default: 20)
- `offset` (int): Skip N medicines (default: 0)
- `search` (string): Search in medicine names

```bash
# Get first 20 medicines
curl "http://localhost:8000/medicines"

# Search for specific medicines
curl "http://localhost:8000/medicines?search=bion&limit=10"

# Pagination
curl "http://localhost:8000/medicines?limit=50&offset=100"
```

#### Get Medicine Details
```http
GET /medicines/{medicine_id}
```

```bash
curl "http://localhost:8000/medicines/35"
```

**Response:**
```json
{
  "id": 35,
  "name": "3 Bion Tablet",
  "generic_name": "Vitamin B1, B6 & B12",
  "manufacturer": "Jenphar Bangladesh Ltd.",
  "price": 12.0,
  "currency": "BDT",
  "strength": "100mg+200mg+200mcg",
  "dosage_form": "Tablet",
  "description": "Vitamin B complex for neurological conditions",
  "product_code": "MX_13717",
  "product_url": "https://medex.com.bd/brands/13717/3-bion-100-mg-tablet",
  "image": {
    "id": 15,
    "original_url": "https://medex.com.bd/storage/images/...",
    "file_size": 55124,
    "width": 750,
    "height": 750
  }
}
```

### 🧹 Maintenance

#### Cleanup Old Files
```http
DELETE /scraper/cleanup?days=30
```

```bash
# Clean files older than 30 days
curl -X DELETE "http://localhost:8000/scraper/cleanup?days=30"

# Clean files older than 7 days
curl -X DELETE "http://localhost:8000/scraper/cleanup?days=7"
```

## 🛠️ Production Deployment

### Using Gunicorn (Recommended)
```bash
# Install gunicorn
pip install gunicorn[gthread]

# Run with multiple workers
gunicorn api.main_medex:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using Docker
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "api.main_medex:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

```bash
# Build and run
docker build -t medex-scraper .
docker run -p 8000:8000 -v $(pwd)/static:/app/static -v $(pwd)/logs:/app/logs medex-scraper
```

### Environment Configuration
Create `.env` file:
```env
DATABASE_URL=postgresql://user:password@localhost/medex_db
REDIS_URL=redis://localhost:6379/0
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
SELENIUM_HEADLESS=true
```

## 📱 Usage Examples

### Start Scraping with Monitoring
```bash
# 1. Start the scraper
curl -X POST "http://localhost:8000/scraper/start" \
  -H "Content-Type: application/json" \
  -d '{"headless": true, "test_pages": 10}'

# 2. Monitor progress
watch -n 30 'curl -s "http://localhost:8000/scraper/progress" | jq'

# 3. Check for errors
curl -s "http://localhost:8000/scraper/logs?level=ERROR" | jq

# 4. View statistics
curl -s "http://localhost:8000/stats" | jq
```

### Python Client Example
```python
import requests
import time

BASE_URL = "http://localhost:8000"

# Start scraper
response = requests.post(f"{BASE_URL}/scraper/start", json={
    "headless": True,
    "test_pages": 5
})
print("Scraper started:", response.json())

# Monitor progress
while True:
    status = requests.get(f"{BASE_URL}/scraper/status").json()
    if not status["running"]:
        break
    
    progress = requests.get(f"{BASE_URL}/scraper/progress").json()
    print(f"Progress: {progress['item_percentage']:.1f}% ({progress['processed_items']}/{progress['total_items']})")
    
    time.sleep(30)

print("Scraping completed!")

# Get results
medicines = requests.get(f"{BASE_URL}/medicines?limit=10").json()
print(f"Found {medicines['total']} medicines")
```

### JavaScript/Node.js Client Example
```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000';

async function startScraping() {
    try {
        // Start scraper
        const startResponse = await axios.post(`${BASE_URL}/scraper/start`, {
            headless: true,
            test_pages: 5
        });
        console.log('Scraper started:', startResponse.data);

        // Monitor progress
        const interval = setInterval(async () => {
            const status = await axios.get(`${BASE_URL}/scraper/status`);
            
            if (!status.data.running) {
                clearInterval(interval);
                console.log('Scraping completed!');
                return;
            }

            const progress = await axios.get(`${BASE_URL}/scraper/progress`);
            console.log(`Progress: ${progress.data.item_percentage}% (${progress.data.processed_items}/${progress.data.total_items})`);
        }, 30000);

    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
    }
}

startScraping();
```

## 🔧 Configuration Options

### Scraper Settings
```python
# In scrapers/medex_scraper.py
class MedExScraper:
    def __init__(self):
        self.total_pages = 822  # Total pages on MedEx
        self.base_url = "https://medex.com.bd"
        # Anti-blocking settings
        self.user_agents = [...]  # 8 rotating user agents
```

### API Settings
```python
# In api/main_medex.py
app = FastAPI(
    title="MedEx Scraper API",
    description="API for controlling MedEx scraper",
    version="1.0.0"
)
```

## 📈 Performance & Scaling

### Expected Performance
- **Speed**: ~10-15 medicines per minute
- **Full scrape**: 6-8 hours for all 822 pages (~24,660 medicines)
- **Memory usage**: ~200-500MB during operation
- **Storage**: ~1-2GB for HTML files, ~500MB for images

### Scaling Recommendations
- Use **Redis** for distributed task queuing
- Deploy with **multiple workers** using Gunicorn
- Use **nginx** as reverse proxy
- Monitor with **Prometheus/Grafana**
- Set up **log aggregation** (ELK stack)

## 🚨 Monitoring & Alerts

### Health Check Endpoint
```http
GET /
```

### Log Monitoring
```bash
# Real-time log monitoring
tail -f logs/medex_scraper.log

# Error monitoring
grep "ERROR" logs/medex_scraper.log | tail -20
```

### Database Monitoring
```sql
-- Check recent activity
SELECT COUNT(*) as new_medicines_today 
FROM medicines 
WHERE created_at >= CURRENT_DATE;

-- Storage usage
SELECT 
    COUNT(*) as total_medicines,
    COUNT(CASE WHEN last_scraped >= CURRENT_DATE - INTERVAL '1 day' THEN 1 END) as recent_updates
FROM medicines;
```

## 🔒 Security Considerations

### API Security
```python
# Add authentication (example)
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/scraper/start")
async def start_scraper(config: ScraperConfig, token: str = Depends(security)):
    # Validate token
    pass
```

### Rate Limiting
```python
# Add rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/scraper/start")
@limiter.limit("5/minute")
async def start_scraper(request: Request, config: ScraperConfig):
    pass
```

## 🐛 Troubleshooting

### Common Issues

1. **ChromeDriver Issues**
   ```bash
   pip install --upgrade webdriver-manager
   ```

2. **Database Connection**
   ```bash
   # Check database connection
   curl "http://localhost:8000/stats"
   ```

3. **Port Already in Use**
   ```bash
   # Use different port
   uvicorn api.main_medex:app --port 8001
   ```

4. **Memory Issues**
   - Limit concurrent operations
   - Use `--test-pages` for smaller batches
   - Monitor system resources

### Debug Mode
```bash
# Run with debug logging
LOG_LEVEL=DEBUG uvicorn api.main_medex:app --host 0.0.0.0 --port 8000 --reload
```

## 📞 Support

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Logs Location
- **API Logs**: `logs/medex_scraper.log`
- **Error Logs**: Filter by level in `/scraper/logs` endpoint

### Contact
For issues and feature requests, check the API logs and status endpoints first. 