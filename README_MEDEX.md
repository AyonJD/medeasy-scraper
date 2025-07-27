# MedEx Scraper

This scraper is designed to extract medicine data from [MedEx.com.bd](https://medex.com.bd/), a Bangladeshi medicine database website.

## Features

- **Selenium-based scraping**: Uses Selenium WebDriver for JavaScript-heavy pages
- **Anti-blocking measures**: Includes user agent rotation and human-like behavior simulation
- **HTML storage**: Saves original HTML content alongside extracted data
- **Image processing**: Downloads and converts images to WebP format
- **Resume capability**: Can resume from previous scraping sessions
- **Progress tracking**: Tracks scraping progress in the database

## MedEx Website Structure

- **Main brands page**: `https://medex.com.bd/brands?page=1` (822 pages total)
- **Medicine details page**: `https://medex.com.bd/brands/{id}/{medicine-name}`

## Usage

### 1. Test Single Medicine Page

Test the scraper on a single medicine page first:

```bash
python test_medex_single.py
```

This will test scraping the 3 Bion tablet page with visible browser window for debugging.

### 2. Run Full Scraper

Run the full scraper to process all 822 pages:

```bash
# Run with default settings (headless mode, with resume)
python run_medex_scraper.py

# Run in visible browser mode (for debugging)
python run_medex_scraper.py --no-headless

# Start fresh without resuming
python run_medex_scraper.py --no-resume

# Test with limited pages
python run_medex_scraper.py --test-pages 5

# Run in headless mode explicitly
python run_medex_scraper.py --headless
```

### 3. Available Options

- `--no-resume`: Start fresh without resuming from previous session
- `--headless`: Run in headless mode (no browser window)
- `--test-pages N`: Limit scraping to N pages for testing

## File Storage

### Images
Images are stored in `static/images/YYYY/MM/` with format:
```
medicine_{id}_{timestamp}_{hash}.webp
```

### HTML Files
HTML files are stored in `static/html/YYYY/MM/` with format:
```
medicine_{id}_{timestamp}_{hash}.html
```

## Anti-Blocking Features

1. **User Agent Rotation**: Rotates between 8 modern user agents
2. **Random Delays**: 2-5 seconds between page loads, 3-7 seconds between medicine pages
3. **Anti-Detection**: Removes webdriver properties and automation markers
4. **Human-like Behavior**: Random sleep intervals and realistic browsing patterns

## Configuration

Key settings in `config.py`:

```python
BASE_URL = "https://medex.com.bd"
DELAY_BETWEEN_REQUESTS = 2  # seconds
SELENIUM_HEADLESS = True
SELENIUM_TIMEOUT = 30
```

## Database Schema

The scraper saves data to the existing medicine database schema with these key fields:

- `name`: Medicine name
- `generic_name`: Generic/chemical name
- `manufacturer`: Manufacturing company
- `price`: Price in BDT
- `strength`: Dosage strength (e.g., "100mg")
- `dosage_form`: Form (Tablet, Capsule, etc.)
- `description`: Indications and usage
- `product_code`: Unique code (format: MX_{id})
- `product_url`: Original MedEx URL

## Logging

Logs are saved to:
- Console: INFO level with colored output
- File: `logs/medex_scraper.log` with DEBUG level and rotation

## Resume Functionality

The scraper can resume from interruptions:
- Progress is saved after each medicine
- Resume data includes current position and processed count
- Use `--no-resume` to start fresh

## Error Handling

- Retries failed pages up to 3 times
- Continues scraping even if individual pages fail
- Logs all errors to database and file
- Graceful handling of missing images or data

## Performance

- Processes approximately 10-15 medicines per minute
- Full scrape of 822 pages may take several hours
- Memory usage optimized with per-page processing
- Database transactions are batched for efficiency

## Troubleshooting

### Chrome Driver Issues
```bash
# If ChromeDriver fails to install automatically
pip install --upgrade webdriver-manager
```

### Permission Issues
```bash
# Ensure directories are writable
chmod 755 static/html static/images logs
```

### Memory Issues
- Run with `--test-pages` for smaller batches
- Monitor system resources during full scrape
- Consider running during off-peak hours 