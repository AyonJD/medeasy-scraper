# MedEasy Data Extractor - Local Setup Guide

This guide will help you run the MedEasy data extractor on your local machine without Docker or PostgreSQL.

## Prerequisites

- **Python 3.11 or higher**
- **Git** (to clone the repository)
- **Chrome browser** (for Selenium web scraping)

## Quick Start (Local Setup)

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd data_extractor
```

### 2. Install Dependencies

```bash
# Install Python dependencies for local development
pip install -r requirements_local.txt
```

### 3. Test the Setup

```bash
# Run the local setup test
python scripts/test_setup_local.py
```

### 4. Run the Scraper

You have two options:

#### Option A: Run Scraper Directly (Recommended for testing)

```bash
# Run the scraper directly
python scripts/run_scraper_local.py
```

#### Option B: Run with API (Recommended for monitoring)

```bash
# Start the API server
uvicorn api.main_local:app --host 127.0.0.1 --port 8000 --reload

# In another terminal, start scraping
curl -X POST "http://127.0.0.1:8000/scrape/start?resume=true"
```

### 5. Monitor Progress

If using the API option, you can monitor progress:

```bash
# Check scraping status
curl http://127.0.0.1:8000/scrape/status

# Get statistics
curl http://127.0.0.1:8000/statistics

# View recent logs
curl http://127.0.0.1:8000/logs
```

## Local Configuration

The local setup uses:

- **SQLite database** (stored as `medeasy_local.db` in your project directory)
- **Local configuration** (`config_local.py`)
- **Simplified requirements** (`requirements_local.txt`)

### Key Differences from Production:

1. **Database**: SQLite instead of PostgreSQL
2. **No Redis**: Simplified without caching/queue
3. **Smaller batch sizes**: Optimized for local resources
4. **Local host**: API runs on `127.0.0.1` instead of `0.0.0.0`

## API Endpoints (Local)

Once the API is running, you can access:

- **API Documentation**: http://127.0.0.1:8000/docs
- **Health Check**: http://127.0.0.1:8000/health
- **Root**: http://127.0.0.1:8000/

### Scraping Management

- `POST /scrape/start?resume=true` - Start scraping
- `POST /scrape/stop` - Stop scraping
- `GET /scrape/status` - Check progress

### Data Access

- `GET /medicines` - Get medicines with filtering
- `GET /medicines/{id}` - Get specific medicine
- `GET /statistics` - Get data statistics
- `GET /logs` - View scraping logs

## Troubleshooting

### Common Issues

1. **Python Version**
   ```bash
   python --version  # Should be 3.11+
   ```

2. **Missing Dependencies**
   ```bash
   pip install -r requirements_local.txt
   ```

3. **Chrome/Selenium Issues**
   - Make sure Chrome is installed
   - The webdriver will be automatically downloaded

4. **Database Issues**
   ```bash
   # Delete the database file and restart
   rm medeasy_local.db
   python scripts/run_scraper_local.py
   ```

5. **Port Already in Use**
   ```bash
   # Use a different port
   uvicorn api.main_local:app --host 127.0.0.1 --port 8001
   ```

### Testing Your Setup

```bash
# Run comprehensive tests
python scripts/test_setup_local.py

# Test individual components
python -c "from database.connection_local import init_db; init_db()"
python -c "from scrapers.medeasy_scraper_local import MedEasyScraperLocal; print('Scraper ready')"
```

## Data Storage

### SQLite Database

The data is stored in `medeasy_local.db` in your project directory. You can:

- **View the database**: Use any SQLite browser (like DB Browser for SQLite)
- **Export data**: Use the API endpoints or direct SQL queries
- **Backup**: Simply copy the `.db` file

### Example SQL Queries

```sql
-- Connect to the database
sqlite3 medeasy_local.db

-- View all medicines
SELECT name, manufacturer, price FROM medicines LIMIT 10;

-- Count total medicines
SELECT COUNT(*) FROM medicines;

-- Get medicines by manufacturer
SELECT name, price FROM medicines WHERE manufacturer LIKE '%Square%';

-- Get recent medicines
SELECT name, created_at FROM medicines ORDER BY created_at DESC LIMIT 10;
```

## Performance Tips for Local

1. **Reduce batch size**: Already configured for local use
2. **Monitor memory**: Check system resources during scraping
3. **Use SSD**: Faster database operations
4. **Close other applications**: Free up resources

## Migration to Production

When you're ready to deploy to your VPS:

1. **Use the production files**:
   - `requirements.txt` (instead of `requirements_local.txt`)
   - `config.py` (instead of `config_local.py`)
   - `api/main.py` (instead of `api/main_local.py`)

2. **Set up PostgreSQL and Redis** on your VPS

3. **Use Docker Compose** for easy deployment

## File Structure (Local)

```
data_extractor/
├── api/
│   ├── main.py              # Production API
│   └── main_local.py        # Local API (SQLite)
├── database/
│   ├── connection.py        # Production DB (PostgreSQL)
│   ├── connection_local.py  # Local DB (SQLite)
│   └── models.py            # Database models
├── scrapers/
│   ├── base_scraper.py      # Base scraping functionality
│   ├── medeasy_scraper.py   # Production scraper
│   └── medeasy_scraper_local.py  # Local scraper
├── scripts/
│   ├── run_scraper.py       # Production scraper script
│   ├── run_scraper_local.py # Local scraper script
│   ├── test_setup.py        # Production tests
│   └── test_setup_local.py  # Local tests
├── config.py                # Production config
├── config_local.py          # Local config
├── requirements.txt         # Production dependencies
├── requirements_local.txt   # Local dependencies
├── medeasy_local.db         # SQLite database (created automatically)
└── README_LOCAL.md          # This file
```

## Next Steps

1. **Test the setup**: Run `python scripts/test_setup_local.py`
2. **Start scraping**: Run `python scripts/run_scraper_local.py`
3. **Monitor progress**: Use the API endpoints
4. **Export data**: Use the API or direct database access
5. **Deploy to VPS**: When ready, use the production setup

Happy scraping! 🚀 