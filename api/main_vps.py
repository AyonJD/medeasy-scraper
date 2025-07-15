from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import asyncio
from loguru import logger
import json
import time

from database.connection_vps import SessionLocal, init_db, check_db_connection
from database.models import Medicine, MedicineImage, ScrapingProgress, ScrapingLog
from scrapers.medeasy_scraper_vps import MedEasyScraperVPS
from config_vps import Config

# Initialize FastAPI app
app = FastAPI(
    title="MedEasy Scraper API (VPS)",
    description="API for scraping MedEasy medicine data - VPS Production Version",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global scraper instance
scraper = None
scraping_task = None

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    global scraper
    
    try:
        # Initialize database
        if not init_db():
            logger.error("Failed to initialize database")
            return
        
        if not check_db_connection():
            logger.error("Failed to connect to database")
            return
        
        # Initialize scraper
        scraper = MedEasyScraperVPS()
        
        logger.info("VPS API started successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "MedEasy Scraper API (VPS)",
        "version": "2.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        
        # Check Redis connection
        redis_ok = False
        if scraper and scraper.redis_client:
            try:
                scraper.redis_client.ping()
                redis_ok = True
            except:
                pass
        
        return {
            "status": "healthy",
            "database": "connected",
            "redis": "connected" if redis_ok else "disconnected",
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {e}")

@app.post("/scrape/start")
async def start_scraping(background_tasks: BackgroundTasks, resume: bool = True):
    """Start scraping process"""
    global scraping_task
    
    try:
        if scraping_task and not scraping_task.done():
            return {"message": "Scraping already in progress", "status": "running"}
        
        # Start scraping in background
        scraping_task = asyncio.create_task(scraper.scrape_all_medicines(resume=resume))
        background_tasks.add_task(scraping_task)
        
        logger.info("VPS scraping started in background")
        return {
            "message": "VPS scraping started successfully",
            "resume": resume,
            "status": "started"
        }
        
    except Exception as e:
        logger.error(f"Error starting scraping: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start scraping: {e}")

@app.get("/scrape/status")
async def get_scraping_status():
    """Get current scraping status"""
    try:
        db = SessionLocal()
        progress = db.query(ScrapingProgress).filter_by(task_name="medeasy_scraper_vps").first()
        db.close()
        
        if not progress:
            return {
                "status": "not_started",
                "current_page": 0,
                "total_pages": 0,
                "processed_items": 0,
                "total_items": 0,
                "started_at": None,
                "last_updated": None,
                "error_message": None
            }
        
        return {
            "status": progress.status,
            "current_page": progress.current_page,
            "total_pages": progress.total_pages,
            "processed_items": progress.processed_items,
            "total_items": progress.total_items,
            "started_at": progress.started_at.isoformat() if progress.started_at else None,
            "last_updated": progress.last_updated.isoformat() if progress.last_updated else None,
            "error_message": progress.error_message
        }
        
    except Exception as e:
        logger.error(f"Error getting scraping status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {e}")

@app.get("/medicines")
async def get_medicines(
    skip: int = 0,
    limit: int = 100,
    category: str = None,
    search: str = None,
    db: Session = Depends(get_db)
):
    """Get medicines with pagination and filtering"""
    try:
        query = db.query(Medicine)
        
        # Apply filters
        if category:
            query = query.filter(Medicine.category.ilike(f"%{category}%"))
        
        if search:
            query = query.filter(
                Medicine.name.ilike(f"%{search}%") |
                Medicine.description.ilike(f"%{search}%") |
                Medicine.manufacturer.ilike(f"%{search}%")
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        medicines = query.offset(skip).limit(limit).all()
        
        # Convert to dict
        medicine_list = []
        for medicine in medicines:
            # Check if medicine has an image
            has_image = db.query(MedicineImage).filter(MedicineImage.medicine_id == medicine.id).first() is not None
            image_url = f"/medicines/{medicine.id}/image" if has_image else None
            
            medicine_dict = {
                "id": medicine.id,
                "name": medicine.name,
                "generic_name": medicine.generic_name,
                "brand_name": medicine.brand_name,
                "manufacturer": medicine.manufacturer,
                "strength": medicine.strength,
                "dosage_form": medicine.dosage_form,
                "pack_size": medicine.pack_size,
                "price": medicine.price,
                "currency": medicine.currency,
                "description": medicine.description,
                "category": medicine.category,
                "product_url": medicine.product_url,
                "image_url": image_url,  # Our server's image URL
                "has_image": has_image,
                "created_at": medicine.created_at.isoformat() if medicine.created_at else None,
                "last_scraped": medicine.last_scraped.isoformat() if medicine.last_scraped else None
            }
            medicine_list.append(medicine_dict)
        
        return {
            "medicines": medicine_list,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting medicines: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get medicines: {e}")

@app.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """Get scraping statistics"""
    try:
        # Get total medicines
        total_medicines = db.query(Medicine).count()
        
        # Get medicines by category
        category_stats = db.query(
            Medicine.category,
            db.func.count(Medicine.id).label('count')
        ).filter(Medicine.category.isnot(None)).group_by(Medicine.category).all()
        
        # Get price statistics
        price_stats = db.query(
            db.func.avg(Medicine.price).label('avg_price'),
            db.func.min(Medicine.price).label('min_price'),
            db.func.max(Medicine.price).label('max_price')
        ).filter(Medicine.price.isnot(None)).first()
        
        # Get recent activity
        recent_medicines = db.query(Medicine).order_by(Medicine.last_scraped.desc()).limit(5).all()
        
        return {
            "total_medicines": total_medicines,
            "categories": [
                {"category": cat, "count": count} 
                for cat, count in category_stats
            ],
            "price_statistics": {
                "average_price": float(price_stats.avg_price) if price_stats.avg_price else 0,
                "min_price": float(price_stats.min_price) if price_stats.min_price else 0,
                "max_price": float(price_stats.max_price) if price_stats.max_price else 0
            },
            "recent_medicines": [
                {
                    "name": med.name,
                    "price": med.price,
                    "category": med.category,
                    "last_scraped": med.last_scraped.isoformat() if med.last_scraped else None
                }
                for med in recent_medicines
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {e}")

@app.get("/logs")
async def get_logs(limit: int = 100, level: str = None, db: Session = Depends(get_db)):
    """Get scraping logs"""
    try:
        query = db.query(ScrapingLog).filter_by(task_name="medeasy_scraper_vps")
        
        if level:
            query = query.filter(ScrapingLog.level == level.upper())
        
        logs = query.order_by(ScrapingLog.created_at.desc()).limit(limit).all()
        
        log_list = []
        for log in logs:
            log_dict = {
                "id": log.id,
                "level": log.level,
                "message": log.message,
                "url": log.url,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            log_list.append(log_dict)
        
        return {"logs": log_list}
        
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {e}")

@app.get("/categories")
async def get_categories():
    """Get all available categories"""
    try:
        categories = []
        for category_name, category_info in Config.CATEGORIES.items():
            categories.append({
                "name": category_name,
                "url": category_info['url'],
                "pages": category_info['pages'],
                "description": category_info['description']
            })
        
        return {"categories": categories}
        
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {e}")

@app.get("/export")
async def export_data(format: str = "json", db: Session = Depends(get_db)):
    """Export all medicine data"""
    try:
        medicines = db.query(Medicine).all()
        
        if format.lower() == "json":
            medicine_list = []
            for medicine in medicines:
                medicine_dict = {
                    "id": medicine.id,
                    "name": medicine.name,
                    "generic_name": medicine.generic_name,
                    "brand_name": medicine.brand_name,
                    "manufacturer": medicine.manufacturer,
                    "strength": medicine.strength,
                    "dosage_form": medicine.dosage_form,
                    "pack_size": medicine.pack_size,
                    "price": medicine.price,
                    "currency": medicine.currency,
                    "description": medicine.description,
                    "indications": medicine.indications,
                    "contraindications": medicine.contraindications,
                    "side_effects": medicine.side_effects,
                    "dosage_instructions": medicine.dosage_instructions,
                    "storage_conditions": medicine.storage_conditions,
                    "product_code": medicine.product_code,
                    "category": medicine.category,
                    "subcategory": medicine.subcategory,
                    "product_url": medicine.product_url,
                    "image_url": medicine.image_url,
                    "is_active": medicine.is_active,
                    "created_at": medicine.created_at.isoformat() if medicine.created_at else None,
                    "updated_at": medicine.updated_at.isoformat() if medicine.updated_at else None,
                    "last_scraped": medicine.last_scraped.isoformat() if medicine.last_scraped else None
                }
                medicine_list.append(medicine_dict)
            
            return {"medicines": medicine_list, "total": len(medicine_list)}
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use 'json'")
            
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export data: {e}")

@app.get("/medicines/{medicine_id}/image")
async def get_medicine_image(medicine_id: int, db: Session = Depends(get_db)):
    """Get medicine image by medicine ID"""
    try:
        medicine_image = db.query(MedicineImage).filter(MedicineImage.medicine_id == medicine_id).first()
        
        if not medicine_image:
            raise HTTPException(status_code=404, detail="Medicine image not found")
        
        from fastapi.responses import Response
        return Response(
            content=medicine_image.image_data,
            media_type="image/webp",
            headers={
                "Content-Length": str(medicine_image.file_size),
                "Cache-Control": "public, max-age=31536000"  # Cache for 1 year
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting medicine image {medicine_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/medicines/{medicine_id}/image/info")
async def get_medicine_image_info(medicine_id: int, db: Session = Depends(get_db)):
    """Get medicine image metadata by medicine ID"""
    try:
        medicine_image = db.query(MedicineImage).filter(MedicineImage.medicine_id == medicine_id).first()
        
        if not medicine_image:
            raise HTTPException(status_code=404, detail="Medicine image not found")
        
        return {
            "medicine_id": medicine_image.medicine_id,
            "original_url": medicine_image.original_url,
            "file_size": medicine_image.file_size,
            "width": medicine_image.width,
            "height": medicine_image.height,
            "format": "WEBP",
            "created_at": medicine_image.created_at.isoformat() if medicine_image.created_at else None,
            "updated_at": medicine_image.updated_at.isoformat() if medicine_image.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting medicine image info {medicine_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/images/statistics")
async def get_image_statistics(db: Session = Depends(get_db)):
    """Get image statistics"""
    try:
        total_images = db.query(MedicineImage).count()
        total_medicines = db.query(Medicine).count()
        medicines_with_images = db.query(Medicine).join(MedicineImage).distinct().count()
        
        # Size statistics
        size_stats = db.query(
            db.func.min(MedicineImage.file_size).label('min_size'),
            db.func.max(MedicineImage.file_size).label('max_size'),
            db.func.avg(MedicineImage.file_size).label('avg_size'),
            db.func.sum(MedicineImage.file_size).label('total_size')
        ).first()
        
        # Dimension statistics
        dimension_stats = db.query(
            db.func.min(MedicineImage.width).label('min_width'),
            db.func.max(MedicineImage.width).label('max_width'),
            db.func.avg(MedicineImage.width).label('avg_width'),
            db.func.min(MedicineImage.height).label('min_height'),
            db.func.max(MedicineImage.height).label('max_height'),
            db.func.avg(MedicineImage.height).label('avg_height')
        ).first()
        
        return {
            "total_images": total_images,
            "total_medicines": total_medicines,
            "medicines_with_images": medicines_with_images,
            "coverage_percentage": (medicines_with_images / total_medicines * 100) if total_medicines > 0 else 0,
            "size_statistics": {
                "min_size_bytes": size_stats.min_size,
                "max_size_bytes": size_stats.max_size,
                "avg_size_bytes": float(size_stats.avg_size) if size_stats.avg_size else None,
                "total_size_bytes": size_stats.total_size,
                "total_size_mb": (size_stats.total_size / (1024 * 1024)) if size_stats.total_size else 0
            },
            "dimension_statistics": {
                "min_width": dimension_stats.min_width,
                "max_width": dimension_stats.max_width,
                "avg_width": float(dimension_stats.avg_width) if dimension_stats.avg_width else None,
                "min_height": dimension_stats.min_height,
                "max_height": dimension_stats.max_height,
                "avg_height": float(dimension_stats.avg_height) if dimension_stats.avg_height else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting image statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/data/clear")
async def clear_all_data(db: Session = Depends(get_db)):
    """Clear all data from database and image storage"""
    try:
        # Stop any running scraping task
        global scraping_task
        if scraping_task and not scraping_task.done():
            scraping_task.cancel()
            scraping_task = None
        
        # Clear all data from database
        deleted_images = db.query(MedicineImage).delete()
        deleted_medicines = db.query(Medicine).delete()
        deleted_progress = db.query(ScrapingProgress).delete()
        deleted_logs = db.query(ScrapingLog).delete()
        
        # Commit changes
        db.commit()
        
        # Clear Redis cache if available
        if scraper and scraper.redis_client:
            try:
                scraper.redis_client.flushdb()
                logger.info("Redis cache cleared")
            except Exception as e:
                logger.warning(f"Failed to clear Redis cache: {e}")
        
        logger.info(f"Cleared all data: {deleted_medicines} medicines, {deleted_images} images, {deleted_progress} progress records, {deleted_logs} logs")
        
        return {
            "message": "All data cleared successfully",
            "deleted_medicines": deleted_medicines,
            "deleted_images": deleted_images,
            "deleted_progress_records": deleted_progress,
            "deleted_logs": deleted_logs,
            "redis_cache_cleared": scraper and scraper.redis_client is not None
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error clearing data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {e}")

@app.delete("/data/clear-medicines")
async def clear_medicines_only(db: Session = Depends(get_db)):
    """Clear only medicines and images, keep logs and progress"""
    try:
        # Clear medicines and images
        deleted_images = db.query(MedicineImage).delete()
        deleted_medicines = db.query(Medicine).delete()
        
        # Commit changes
        db.commit()
        
        logger.info(f"Cleared medicines data: {deleted_medicines} medicines, {deleted_images} images")
        
        return {
            "message": "Medicines and images cleared successfully",
            "deleted_medicines": deleted_medicines,
            "deleted_images": deleted_images
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error clearing medicines: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear medicines: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main_vps:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=False
    ) 