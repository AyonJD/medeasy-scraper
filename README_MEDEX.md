# MedEx Scraper - Complete Medicine Data Extraction

This scraper extracts **comprehensive medicine data** from [MedEx.com.bd](https://medex.com.bd/), Bangladesh's largest medicine database, with **all medical sections** and **anti-blocking protection**.

## 🎯 **Features**

### **📊 Comprehensive Data Extraction**
- **✅ All 12+ Medical Sections**: Indications, Composition, Pharmacology, Dosage & Administration, Interaction, Contraindications, Side Effects, Pregnancy & Lactation, Precautions & Warnings, Overdose Effects, Therapeutic Class, Storage Conditions
- **✅ Complete Pricing**: Unit price, strip price, pack information
- **✅ Q&A Data**: Common questions and answers
- **✅ Metadata**: Page titles, descriptions, product codes

### **🛡️ Anti-Blocking Protection**
- **Selenium WebDriver**: Handles dynamic content
- **User Agent Rotation**: Prevents detection
- **Human-like Delays**: Random timing between requests
- **IP Protection**: No blocking during extensive scraping

### **💾 Advanced Storage**
- **WebP Images**: High-quality, optimized image storage
- **Raw HTML**: Complete page source saved for reference
- **PostgreSQL Database**: Structured data with JSON fields
- **Resume Capability**: Continue from interruptions

### **🚀 FastAPI Integration**
- **REST API**: Full control and monitoring via HTTP endpoints
- **Real-time Progress**: Live scraping statistics
- **Background Processing**: Non-blocking scraper execution

## 📋 **Quick Start**

### **1. Start the API Server**

```bash
# Method 1: Direct command
python -m uvicorn api.main_medex:app --host 0.0.0.0 --port 8000 --reload

# Method 2: Auto-setup script
python start_medex_api.py
```

Server will be available at: `http://localhost:8000`

### **2. Access API Documentation**

Visit `http://localhost:8000/docs` for interactive API documentation

### **3. Start Scraping**

#### **🔬 Test Mode (Recommended First)**
```bash
# Ultra-fast test (1 page = ~30 medicines, ~3-5 minutes)
curl -X POST -H "Content-Type: application/json" -d '{"headless": true, "test_pages": 1, "no_resume": true}' http://localhost:8000/scraper/start

# Quick test (5 pages = ~150 medicines, ~15-20 minutes)
curl -X POST -H "Content-Type: application/json" -d '{"headless": true, "test_pages": 5, "no_resume": true}' http://localhost:8000/scraper/start
```

#### **🚀 Full Production Run**
```bash
# Complete scraping (all 822 pages = ~24,660 medicines, ~8-12 hours)
curl -X POST -H "Content-Type: application/json" -d '{"headless": true, "no_resume": true}' http://localhost:8000/scraper/start
```

### **4. Monitor Progress**

```bash
# Check medicine count
curl http://localhost:8000/medicines

# View statistics
curl http://localhost:8000/stats

# Check scraper status
curl http://localhost:8000/scraper/status
```

## 📊 **Two-Phase Process**

### **Phase 1: URL Discovery**
- Collects medicine URLs from all pages
- **Progress**: 0 medicines in database (normal!)
- **Duration**: 15-30% of total time

### **Phase 2: Medicine Scraping** 
- Extracts comprehensive data from each medicine
- **Progress**: Medicines appear in database
- **Duration**: 70-85% of total time

## 🔧 **API Endpoints**

### **Scraper Control**
```bash
POST /scraper/start     # Start scraper
POST /scraper/stop      # Stop scraper
GET  /scraper/status    # Current status
GET  /scraper/progress  # Detailed progress
GET  /scraper/logs      # Recent logs
```

### **Data Access**
```bash
GET /medicines                  # List all medicines
GET /medicines/{id}            # Specific medicine details
GET /stats                     # Overall statistics
DELETE /scraper/cleanup        # Clean old files
```

### **Medicine Data Structure**
```json
{
  "id": 1,
  "name": "3 Bion",
  "generic_name": "Vitamin B1, B6 & B12",
  "manufacturer": "Jenphar Bangladesh Ltd.",
  "price": 12.0,
  "unit_price": "৳ 12.00",
  "strip_price": "৳ 120.00",
  "pack_info": "(6 x 10: ৳ 720.00)",
  "strength": "100 mg+200 mg+200 mcg",
  "dosage_form": "Tablet",
  "image_url": "/images/2025/07/medicine_xxx.webp",
  "detailed_info": {
    "indications": "Complete indications text...",
    "composition": "Detailed composition...",
    "pharmacology": "Pharmacology information...",
    "dosage_administration": "Dosage instructions...",
    "interaction": "Drug interactions...",
    "contraindications": "Contraindications...",
    "side_effects": "Side effects...",
    "pregnancy_lactation": "Pregnancy info...",
    "precautions_warnings": "Precautions...",
    "overdose_effects": "Overdose information...",
    "therapeutic_class": "Drug classification...",
    "storage_conditions": "Storage requirements..."
  },
  "common_questions": [
    {
      "question": "What is this medicine used for?",
      "answer": "Detailed answer..."
    }
  ],
  "price_details": {
    "unit_price": "৳ 12.00",
    "strip_price": "৳ 120.00",
    "pack_info": "(6 x 10: ৳ 720.00)"
  }
}
```

## 🧹 **Data Management**

### **Clear All Data**
```bash
# Complete cleanup (HTML, images, database)
python clean_medex_data.py

# Files only (keep database)
powershell .\clean_medex_files.ps1
```

### **Storage Structure**
```
static/
├── images/2025/07/     # WebP images by date
├── html/2025/07/       # Raw HTML files by date
└── logs/               # Scraper logs
```

## ⚡ **Performance & Timeline**

### **Test Modes**
- **1 page**: ~30 medicines in 3-5 minutes
- **5 pages**: ~150 medicines in 15-20 minutes
- **10 pages**: ~300 medicines in 30-40 minutes

### **Full Production**
- **All 822 pages**: ~24,660 medicines in 8-12 hours
- **Average rate**: ~30-40 medicines per minute
- **Storage**: ~2-3 GB (images + HTML + database)

## 🔍 **Monitoring & Troubleshooting**

### **Check if Working**
```bash
# Quick status check
curl http://localhost:8000/stats

# Recent activity
curl http://localhost:8000/scraper/logs?limit=5

# Medicine count over time
watch -n 30 'curl -s http://localhost:8000/medicines | grep total'
```

### **Common Issues**

**Issue**: "total": 0 medicines
**Solution**: Normal during Phase 1 (URL Discovery). Wait for Phase 2.

**Issue**: PowerShell command errors
**Solution**: Use the Python requests method or curl instead.

**Issue**: ChromeDriver errors
**Solution**: Update webdriver-manager: `pip install --upgrade webdriver-manager`

## 🚀 **Advanced Usage**

### **Custom Configuration**
```python
# In your script
import requests

# Start with custom settings
config = {
    "headless": True,
    "test_pages": 10,  # Custom page limit
    "no_resume": True
}

response = requests.post(
    "http://localhost:8000/scraper/start", 
    json=config
)
```

### **Data Processing**
```python
# Access comprehensive data
import requests

# Get medicines with all sections
medicines = requests.get("http://localhost:8000/medicines").json()

for medicine in medicines["medicines"]:
    print(f"Medicine: {medicine['name']}")
    
    # Access detailed medical information
    if medicine.get('detailed_info'):
        print(f"Indications: {medicine['detailed_info']['indications']}")
        print(f"Dosage: {medicine['detailed_info']['dosage_administration']}")
        print(f"Side Effects: {medicine['detailed_info']['side_effects']}")
    
    # Access pricing information
    if medicine.get('price_details'):
        print(f"Pricing: {medicine['price_details']}")
```

## 📈 **Success Indicators**

✅ **API Server**: `http://localhost:8000` responds  
✅ **Scraper Active**: `/scraper/status` shows "running": true  
✅ **Progress**: `/stats` shows increasing file counts  
✅ **Phase 2 Started**: `/medicines` total > 0  
✅ **Comprehensive Data**: Medicines have all `detailed_info` sections  

## 🎉 **Final Result**

After completion, you'll have:
- **~24,660 medicines** with complete medical information
- **All 12+ sections** per medicine (Dosage, Side Effects, etc.)
- **High-quality images** in WebP format
- **Raw HTML** for each medicine page
- **REST API** for easy data access
- **Complete pricing** and Q&A data

**Ready to scrape the complete MedEx database with comprehensive medical information! 🚀** 