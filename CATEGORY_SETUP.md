# Category Setup for MedEasy Scraper

This document explains how to initialize categories in the database before starting data extraction.

## Overview

The MedEasy scraper now uses a proper category system with:
- **Category ID**: Unique identifier for each category
- **Category Name**: Human-readable name (e.g., "Women's health and hygiene products")
- **Category Slug**: URL-friendly identifier (e.g., "womens-choice")

## Available Categories

The scraper includes **14 categories** covering all product types on MedEasy.health:

1. **womens-choice** (4 pages) - Women's health and hygiene products
2. **sexual-wellness** (7 pages) - Sexual wellness and contraceptive products  
3. **skin-care** (7 pages) - Skincare and beauty products
4. **diabetic-care** (4 pages) - Diabetes management products
5. **devices** (2 pages) - Medical devices and equipment
6. **supplement** (1 page) - Nutritional supplements
7. **diapers** (1 page) - Baby diapers and related products
8. **baby-care** (1 page) - Baby care products
9. **personal-care** (1 page) - Personal care and hygiene products
10. **hygiene-and-freshness** (1 page) - Hygiene and freshness products
11. **dental-care** (1 page) - Dental care products
12. **herbal-medicine** (1 page) - Herbal and natural medicines
13. **prescription-medicine** (1 page) - Prescription medicines
14. **otc-medicine** (1 page) - Over-the-counter medicines

## How to Initialize Categories

### Option 1: Using the Simple Script (Recommended)

#### For Local Environment Only (Avoids VPS Dependencies):
```bash
# Windows - Double click or run in command prompt
init_categories.bat

# Windows PowerShell
.\init_categories.ps1

# Direct Python execution
python run_init_categories_local.py
py run_init_categories_local.py
```

#### For Both Environments (Requires psycopg2 for VPS):
```bash
# Initialize categories for both local and VPS environments
python run_init_categories.py

# Or specify environment
python run_init_categories.py --env local
python run_init_categories.py --env vps
```

### Option 2: Using SQL Script (No Python Required)

If Python is not available, you can use the SQL script directly:

```bash
# Windows - Double click or run in command prompt
init_categories_sql.bat

# Windows PowerShell
.\init_categories_sql.ps1

# Manual SQLite execution
sqlite3 medeasy_local.db < scripts/init_categories.sql
```

### Option 3: Using the Full Python Script

```bash
# Initialize categories for both environments
python scripts/init_categories.py

# Initialize for specific environment
python scripts/init_categories.py --env local
python scripts/init_categories.py --env vps
```

## What the Script Does

1. **Creates Database Tables**: Ensures the `categories` table exists
2. **Clears Existing Categories**: Removes any existing categories to start fresh
3. **Creates All Categories**: Adds all 14 categories with proper names, slugs, and IDs
4. **Displays Results**: Shows the created categories with their IDs

## Example Output

```
2024-01-15 10:30:00 | INFO | Starting category initialization...
2024-01-15 10:30:01 | INFO | Initializing categories for LOCAL environment...
2024-01-15 10:30:01 | INFO | Cleared existing categories
2024-01-15 10:30:01 | INFO | Added category: Women's health and hygiene products (slug: womens-choice)
2024-01-15 10:30:01 | INFO | Added category: Sexual wellness and contraceptive products (slug: sexual-wellness)
...
2024-01-15 10:30:01 | SUCCESS | Successfully created 14 categories in LOCAL database
2024-01-15 10:30:01 | INFO | Created categories:
2024-01-15 10:30:01 | INFO |   ID: 1, Name: Women's health and hygiene products, Slug: womens-choice
2024-01-15 10:30:01 | INFO |   ID: 2, Name: Sexual wellness and contraceptive products, Slug: sexual-wellness
...
```

## Category ID Mapping

When scraping medicines, the system automatically maps URLs to category IDs:

- `/womens-choice` → Category ID 1
- `/sexual-wellness` → Category ID 2
- `/skin-care` → Category ID 3
- And so on...

## Database Schema

The `categories` table structure:

```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    description TEXT,
    parent_id INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
```

## Next Steps

After running the category initialization:

1. **Start Data Extraction**: Run the scraper to extract medicines with proper category IDs
2. **Verify Categories**: Check that medicines are properly categorized in the database
3. **API Integration**: The API will now return category information with medicines

## Troubleshooting

### Database Connection Issues
- Ensure your database is running and accessible
- Check database credentials in config files
- For VPS: Verify PostgreSQL is running and accessible

### Python Not Found Issues
- **Windows**: Use `init_categories.bat` or `init_categories.ps1` which automatically find Python
- **Manual**: Try `python`, `py`, or `python3` commands
- **Installation**: Download Python from python.org and add to PATH
- **Alternative**: Use SQL script method (`init_categories_sql.bat`) which doesn't require Python

### SQLite Not Found Issues
- **Download**: Get SQLite from https://www.sqlite.org/download.html
- **Windows**: Download the precompiled binaries and add to PATH
- **Alternative**: Use Python method if SQLite is not available

### Permission Issues
- Ensure the script has write permissions to the database
- For VPS: Check PostgreSQL user permissions

### Category Already Exists
- The script automatically clears existing categories
- If you want to preserve existing data, modify the script to skip the clear step

## API Endpoints

After initialization, you can use these API endpoints:

- `GET /api/categories` - List all categories
- `GET /api/categories/{id}` - Get specific category
- `GET /api/medicines?category_id={id}` - Get medicines by category 