from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Any
import asyncio
from datetime import datetime

from database.connection import get_db, init_db, check_db_connection
from database.models import Medicine, MedicineImage, ScrapingProgress, ScrapingLog, Category
from scrapers.medeasy_scraper import MedEasyScraper
from config import Config
from loguru import logger

# Initialize FastAPI app
app = FastAPI(
    title="MedEasy Data Extractor API",
    description="API for extracting medicine data from MedEasy website",
    version="1.0.0"
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

@app.on_event("startup")
async def startup_event():
    """Initialize database and check connections on startup"""
    try:
        # Initialize database
        init_db()
        
        # Check database connection
        if not check_db_connection():
            logger.error("Database connection failed on startup")
            raise Exception("Database connection failed")
        
        logger.info("API started successfully")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global scraper
    if scraper:
        await scraper.close()
    logger.info("API shutdown complete")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "MedEasy Data Extractor API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = check_db_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/scrape/start")
async def start_scraping(background_tasks: BackgroundTasks, resume: bool = True):
    """Start the scraping process"""
    global scraper
    
    try:
        # Check if scraping is already running
        db = next(get_db())
        progress = db.query(ScrapingProgress).filter_by(task_name="medeasy_scraper").first()
        
        if progress and progress.status == "running":
            raise HTTPException(status_code=400, detail="Scraping is already running")
        
        # Create new scraper instance
        scraper = MedEasyScraper()
        
        # Start scraping in background
        background_tasks.add_task(scraper.scrape_all_medicines, resume)
        
        logger.info("Scraping started in background")
        return {
            "message": "Scraping started successfully",
            "resume": resume,
            "status": "started"
        }
        
    except Exception as e:
        logger.error(f"Error starting scraping: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape/stop")
async def stop_scraping():
    """Stop the scraping process"""
    global scraper
    
    try:
        if scraper:
            await scraper.close()
            scraper = None
        
        # Update progress status
        db = next(get_db())
        progress = db.query(ScrapingProgress).filter_by(task_name="medeasy_scraper").first()
        if progress:
            progress.status = "stopped"
            db.commit()
        
        logger.info("Scraping stopped")
        return {"message": "Scraping stopped successfully"}
        
    except Exception as e:
        logger.error(f"Error stopping scraping: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scrape/status")
async def get_scraping_status():
    """Get current scraping status and progress"""
    try:
        db = next(get_db())
        progress = db.query(ScrapingProgress).filter_by(task_name="medeasy_scraper").first()
        
        if not progress:
            return {
                "status": "not_started",
                "message": "No scraping task found"
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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/medicines")
async def get_medicines(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    category: str = None,
    manufacturer: str = None,
    db: Session = Depends(get_db)
):
    """Get medicines with pagination and filtering"""
    try:
        query = db.query(Medicine)
        
        # Apply filters
        if search:
            query = query.filter(
                Medicine.name.ilike(f"%{search}%") |
                Medicine.generic_name.ilike(f"%{search}%") |
                Medicine.brand_name.ilike(f"%{search}%")
            )
        
        if category:
            # Filter by category ID directly
            try:
                category_id = int(category)
                query = query.filter(Medicine.category_id == category_id)
            except ValueError:
                # If category is not a number, try to filter by category name through relationship
                query = query.join(Medicine.category_ref).filter(Category.name.ilike(f"%{category}%"))
        
        if manufacturer:
            query = query.filter(Medicine.manufacturer.ilike(f"%{manufacturer}%"))
        
        # Get total count
        total = query.count()
        
        # Apply pagination and load relationships
        medicines = query.options(
            joinedload(Medicine.subcategory_ref),
            joinedload(Medicine.images)
        ).offset(skip).limit(limit).all()
        
        return {
            "medicines": [
                {
                    "id": med.id,
                    "name": med.name,
                    "generic_name": med.generic_name,
                    "brand_name": med.brand_name,
                    "manufacturer": med.manufacturer,
                    "strength": med.strength,
                    "dosage_form": med.dosage_form,
                    "pack_size": med.pack_size,
                    "price": med.price,
                    "currency": med.currency,
                    "category": med.category_id,  # Use the category_id field directly (which contains the ID)
                    "subcategory": med.subcategory_ref.name if med.subcategory_ref else None,
                    "subcategory_id": med.subcategory_ref.id if med.subcategory_ref else None,
                    "subcategory_slug": med.subcategory_ref.slug if med.subcategory_ref else None,
                    "product_code": med.product_code,
                    "image_url": med.image_url,
                    "has_image": len(med.images) > 0,
                    "created_at": med.created_at.isoformat() if med.created_at else None
                }
                for med in medicines
            ],
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting medicines: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/medicines/{medicine_id}")
async def get_medicine(medicine_id: int, db: Session = Depends(get_db)):
    """Get a specific medicine by ID"""
    try:
        medicine = db.query(Medicine).options(
            joinedload(Medicine.subcategory_ref),
            joinedload(Medicine.images)
        ).filter(Medicine.id == medicine_id).first()
        
        if not medicine:
            raise HTTPException(status_code=404, detail="Medicine not found")
        
        return {
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
            "category": medicine.category_id,  # Use the category_id field directly (which contains the ID)
            "subcategory": medicine.subcategory_ref.name if medicine.subcategory_ref else None,
            "subcategory_id": medicine.subcategory_ref.id if medicine.subcategory_ref else None,
            "subcategory_slug": medicine.subcategory_ref.slug if medicine.subcategory_ref else None,
            "product_code": medicine.product_code,
            "image_url": medicine.image_url,
            "has_image": len(medicine.images) > 0,
            "is_active": medicine.is_active,
            "created_at": medicine.created_at.isoformat() if medicine.created_at else None,
            "updated_at": medicine.updated_at.isoformat() if medicine.updated_at else None,
            "last_scraped": medicine.last_scraped.isoformat() if medicine.last_scraped else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting medicine {medicine_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """Get scraping and data statistics"""
    try:
        # Medicine statistics
        total_medicines = db.query(Medicine).count()
        active_medicines = db.query(Medicine).filter(Medicine.is_active == True).count()
        
        # Category statistics
        categories = db.query(Medicine.category).distinct().count()
        
        # Manufacturer statistics
        manufacturers = db.query(Medicine.manufacturer).distinct().count()
        
        # Price statistics
        price_stats = db.query(
            db.func.min(Medicine.price).label('min_price'),
            db.func.max(Medicine.price).label('max_price'),
            db.func.avg(Medicine.price).label('avg_price')
        ).filter(Medicine.price.isnot(None)).first()
        
        # Recent activity
        recent_medicines = db.query(Medicine).order_by(Medicine.created_at.desc()).limit(10).count()
        
        return {
            "total_medicines": total_medicines,
            "active_medicines": active_medicines,
            "categories": categories,
            "manufacturers": manufacturers,
            "price_statistics": {
                "min_price": float(price_stats.min_price) if price_stats.min_price else None,
                "max_price": float(price_stats.max_price) if price_stats.max_price else None,
                "avg_price": float(price_stats.avg_price) if price_stats.avg_price else None
            },
            "recent_medicines": recent_medicines
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs")
async def get_logs(
    skip: int = 0,
    limit: int = 100,
    level: str = None,
    task_name: str = None,
    db: Session = Depends(get_db)
):
    """Get scraping logs"""
    try:
        query = db.query(ScrapingLog)
        
        if level:
            query = query.filter(ScrapingLog.level == level)
        
        if task_name:
            query = query.filter(ScrapingLog.task_name == task_name)
        
        total = query.count()
        logs = query.order_by(ScrapingLog.created_at.desc()).offset(skip).limit(limit).all()
        
        return {
            "logs": [
                {
                    "id": log.id,
                    "task_name": log.task_name,
                    "level": log.level,
                    "message": log.message,
                    "url": log.url,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                }
                for log in logs
            ],
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=True
    ) 