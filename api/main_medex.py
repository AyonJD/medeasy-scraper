from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import threading
from datetime import datetime
from loguru import logger
from sqlalchemy.orm import Session
from database.connection_local import SessionLocal
from database.models import Medicine, MedicineImage, ScrapingProgress, ScrapingLog
from scrapers.medex_scraper import MedExScraper
from utils.html_storage import HtmlStorage
from utils.image_storage import ImageStorage
from sqlalchemy import func, desc
import os

app = FastAPI(
    title="MedEx Scraper API",
    description="API for controlling and monitoring the MedEx medicine scraper",
    version="1.0.0"
)

# Global scraper instance
scraper_instance = None
scraper_thread = None
scraper_running = False

class ScraperConfig(BaseModel):
    headless: bool = True
    test_pages: Optional[int] = None
    no_resume: bool = False

class ScraperStatus(BaseModel):
    running: bool
    current_page: Optional[int] = None
    total_pages: Optional[int] = None
    processed_items: Optional[int] = None
    total_items: Optional[int] = None
    status: Optional[str] = None
    start_time: Optional[datetime] = None

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "MedEx Scraper API",
        "version": "1.0.0",
        "endpoints": {
            "start": "/scraper/start",
            "stop": "/scraper/stop",
            "status": "/scraper/status",
            "progress": "/scraper/progress",
            "logs": "/scraper/logs",
            "medicines": "/medicines",
            "stats": "/stats"
        }
    }

@app.post("/scraper/start")
async def start_scraper(config: ScraperConfig, background_tasks: BackgroundTasks):
    """Start the MedEx scraper"""
    global scraper_instance, scraper_thread, scraper_running
    
    if scraper_running:
        raise HTTPException(status_code=400, detail="Scraper is already running")
    
    try:
        # Create scraper instance
        scraper_instance = MedExScraper()
        
        # Apply configuration
        if config.test_pages:
            scraper_instance.total_pages = config.test_pages
        
        # Start scraper in background thread
        def run_scraper():
            global scraper_running
            scraper_running = True
            try:
                scraper_instance.scrape_all_medicines(resume=not config.no_resume)
            except Exception as e:
                logger.error(f"Scraper error: {e}")
            finally:
                scraper_running = False
        
        scraper_thread = threading.Thread(target=run_scraper)
        scraper_thread.daemon = True
        scraper_thread.start()
        
        return {
            "message": "Scraper started successfully",
            "config": config.dict(),
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scraper: {str(e)}")

@app.post("/scraper/stop")
async def stop_scraper():
    """Stop the MedEx scraper"""
    global scraper_running, scraper_instance
    
    if not scraper_running:
        raise HTTPException(status_code=400, detail="Scraper is not running")
    
    try:
        scraper_running = False
        # Note: This is a graceful stop indication, the actual stopping depends on the scraper's implementation
        
        return {
            "message": "Stop signal sent to scraper",
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop scraper: {str(e)}")

@app.get("/scraper/status")
async def get_scraper_status() -> ScraperStatus:
    """Get current scraper status"""
    global scraper_running
    
    db = SessionLocal()
    try:
        progress = db.query(ScrapingProgress).filter_by(task_name="medex_scraper").first()
        
        status = ScraperStatus(
            running=scraper_running,
            current_page=progress.current_page if progress else None,
            total_pages=progress.total_pages if progress else None,
            processed_items=progress.processed_items if progress else None,
            total_items=progress.total_items if progress else None,
            status=progress.status if progress else None,
            start_time=progress.created_at if progress else None
        )
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")
    finally:
        db.close()

@app.get("/scraper/progress")
async def get_scraper_progress():
    """Get detailed scraper progress"""
    db = SessionLocal()
    try:
        progress = db.query(ScrapingProgress).filter_by(task_name="medex_scraper").first()
        
        if not progress:
            return {"message": "No progress data found"}
        
        # Calculate percentages
        page_percentage = 0
        item_percentage = 0
        
        if progress.total_pages and progress.total_pages > 0:
            page_percentage = (progress.current_page / progress.total_pages) * 100
            
        if progress.total_items and progress.total_items > 0:
            item_percentage = (progress.processed_items / progress.total_items) * 100
        
        return {
            "current_page": progress.current_page,
            "total_pages": progress.total_pages,
            "page_percentage": round(page_percentage, 2),
            "processed_items": progress.processed_items,
            "total_items": progress.total_items,
            "item_percentage": round(item_percentage, 2),
            "status": progress.status,
            "created_at": progress.created_at,
            "updated_at": progress.updated_at,
            "resume_data": progress.resume_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get progress: {str(e)}")
    finally:
        db.close()

@app.get("/scraper/logs")
async def get_scraper_logs(
    limit: int = Query(50, description="Number of log entries to return"),
    level: Optional[str] = Query(None, description="Filter by log level (INFO, ERROR, WARNING)")
):
    """Get recent scraper logs"""
    db = SessionLocal()
    try:
        query = db.query(ScrapingLog).filter_by(task_name="medex_scraper")
        
        if level:
            query = query.filter(ScrapingLog.level == level.upper())
        
        logs = query.order_by(desc(ScrapingLog.created_at)).limit(limit).all()
        
        return {
            "logs": [
                {
                    "id": log.id,
                    "level": log.level,
                    "message": log.message,
                    "url": log.url,
                    "created_at": log.created_at
                }
                for log in logs
            ],
            "total": len(logs)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")
    finally:
        db.close()

@app.get("/medicines")
async def get_medicines(
    limit: int = Query(20, description="Number of medicines to return"),
    offset: int = Query(0, description="Number of medicines to skip"),
    search: Optional[str] = Query(None, description="Search in medicine names")
):
    """Get medicines from database with comprehensive data"""
    db = SessionLocal()
    try:
        query = db.query(Medicine)
        
        if search:
            query = query.filter(Medicine.name.ilike(f"%{search}%"))
        
        total = query.count()
        medicines = query.offset(offset).limit(limit).all()
        
        medicine_list = []
        for med in medicines:
            # Basic medicine data
            medicine_data = {
                "id": med.id,
                "name": med.name,
                "generic_name": med.generic_name,
                "manufacturer": med.manufacturer,
                "price": med.price,
                "currency": med.currency,
                "strength": med.strength,
                "dosage_form": med.dosage_form,
                "product_code": med.product_code,
                "description": med.description,
                "image_url": med.image_url,
                "created_at": med.created_at,
                "last_scraped": med.last_scraped
            }
            
            # Extract additional data from raw_data if available
            if med.raw_data:
                raw_data = med.raw_data
                extracted_fields = raw_data.get('extracted_fields', {})
                
                # Add comprehensive pricing information
                medicine_data['unit_price'] = extracted_fields.get('unit_price')
                medicine_data['strip_price'] = extracted_fields.get('strip_price')
                medicine_data['pack_info'] = extracted_fields.get('pack_info')
                
                # Add metadata
                medicine_data['page_title'] = extracted_fields.get('page_title')
                medicine_data['meta_description'] = extracted_fields.get('meta_description')
                
                # Add common questions
                medicine_data['common_questions'] = extracted_fields.get('common_questions')
                
                # Add detailed section data
                medicine_data['detailed_info'] = extracted_fields.get('detailed_info')
                
                # Add price details
                medicine_data['price_details'] = raw_data.get('price_details', {})
            
            medicine_list.append(medicine_data)
        
        return {
            "medicines": medicine_list,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get medicines: {str(e)}")
    finally:
        db.close()

@app.get("/medicines/{medicine_id}")
async def get_medicine_detail(medicine_id: int):
    """Get detailed information about a specific medicine with comprehensive data"""
    db = SessionLocal()
    try:
        medicine = db.query(Medicine).filter_by(id=medicine_id).first()
        
        if not medicine:
            raise HTTPException(status_code=404, detail="Medicine not found")
        
        # Get associated image
        image = db.query(MedicineImage).filter_by(medicine_id=medicine_id).first()
        
        # Basic medicine data
        result = {
            "id": medicine.id,
            "name": medicine.name,
            "generic_name": medicine.generic_name,
            "manufacturer": medicine.manufacturer,
            "price": medicine.price,
            "currency": medicine.currency,
            "strength": medicine.strength,
            "dosage_form": medicine.dosage_form,
            "description": medicine.description,
            "product_code": medicine.product_code,
            "image_url": medicine.image_url,
            "created_at": medicine.created_at,
            "last_scraped": medicine.last_scraped,
            "image": None
        }
        
        # Extract additional comprehensive data from raw_data if available
        if medicine.raw_data:
            raw_data = medicine.raw_data
            extracted_fields = raw_data.get('extracted_fields', {})
            
            # Add comprehensive pricing information
            result['unit_price'] = extracted_fields.get('unit_price')
            result['strip_price'] = extracted_fields.get('strip_price')
            result['pack_info'] = extracted_fields.get('pack_info')
            
            # Add metadata
            result['page_title'] = extracted_fields.get('page_title')
            result['meta_description'] = extracted_fields.get('meta_description')
            
            # Add common questions
            result['common_questions'] = extracted_fields.get('common_questions')
            
            # Add detailed section data (all 12+ sections)
            result['detailed_info'] = extracted_fields.get('detailed_info')
            
            # Add price details
            result['price_details'] = raw_data.get('price_details', {})
            
            # Add product URL if available
            result['product_url'] = extracted_fields.get('product_url')
        
        if image:
            result["image"] = {
                "id": image.id,
                "original_url": image.original_url,
                "file_size": image.file_size,
                "width": image.width,
                "height": image.height,
                "created_at": image.created_at
            }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get medicine: {str(e)}")
    finally:
        db.close()

@app.get("/stats")
async def get_stats():
    """Get overall scraping statistics"""
    db = SessionLocal()
    html_storage = HtmlStorage()
    image_storage = ImageStorage()
    
    try:
        # Database stats
        total_medicines = db.query(Medicine).count()
        total_images = db.query(MedicineImage).count()
        
        # Recent medicines (last 24 hours)
        from datetime import timedelta
        yesterday = datetime.now() - timedelta(days=1)
        recent_medicines = db.query(Medicine).filter(Medicine.created_at >= yesterday).count()
        
        # Manufacturers count
        manufacturers_count = db.query(func.count(func.distinct(Medicine.manufacturer))).scalar()
        
        # Get file storage stats
        html_stats = html_storage.get_storage_stats()
        image_stats = image_storage.get_storage_stats()
        
        # Log file size
        log_file_size = 0
        if os.path.exists("logs/medex_scraper.log"):
            log_file_size = os.path.getsize("logs/medex_scraper.log")
        
        return {
            "database": {
                "total_medicines": total_medicines,
                "total_images": total_images,
                "recent_medicines_24h": recent_medicines,
                "unique_manufacturers": manufacturers_count
            },
            "storage": {
                "html_files": html_stats.get("total_files", 0),
                "html_size_mb": html_stats.get("total_size_mb", 0),
                "image_files": image_stats.get("total_files", 0),
                "image_size_mb": image_stats.get("total_size_mb", 0),
                "log_size_mb": round(log_file_size / (1024 * 1024), 2)
            },
            "scraper": {
                "running": scraper_running,
                "task_name": "medex_scraper",
                "base_url": "https://medex.com.bd"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
    finally:
        db.close()

@app.delete("/scraper/cleanup")
async def cleanup_old_files(days: int = Query(30, description="Delete files older than this many days")):
    """Clean up old HTML and image files"""
    try:
        html_storage = HtmlStorage()
        image_storage = ImageStorage()
        
        deleted_html = html_storage.cleanup_old_html(days)
        deleted_images = image_storage.cleanup_old_images(days)
        
        return {
            "message": "Cleanup completed",
            "deleted_html_files": deleted_html,
            "deleted_image_files": deleted_images,
            "days_threshold": days
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 