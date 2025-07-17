#!/usr/bin/env python3
"""
Category Initialization Script for MedEasy Scraper
Creates all categories in the database before starting data extraction.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from database.models import Category, Base
from database.connection_local import engine as local_engine
from database.connection_vps import get_engine as get_vps_engine
from config_local import Config as LocalConfig
from config_vps import Config as VPSConfig
from loguru import logger

def create_slug(name: str) -> str:
    """Create a URL-friendly slug from category name"""
    import re
    
    # Map category names to their proper slugs
    slug_mapping = {
        "Women's health and hygiene products": "womens-choice",
        "Sexual wellness and contraceptive products": "sexual-wellness",
        "Skincare and beauty products": "skin-care",
        "Diabetes management products": "diabetic-care",
        "Medical devices and equipment": "devices",
        "Nutritional supplements": "supplement",
        "Baby diapers and related products": "diapers",
        "Baby care products": "baby-care",
        "Personal care and hygiene products": "personal-care",
        "Hygiene and freshness products": "hygiene-and-freshness",
        "Dental care products": "dental-care",
        "Herbal and natural medicines": "herbal-medicine",
        "Prescription medicines": "prescription-medicine",
        "Over-the-counter medicines": "otc-medicine"
    }
    
    # Return mapped slug if available, otherwise create from name
    if name in slug_mapping:
        return slug_mapping[name]
    
    # Fallback: Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
    slug = re.sub(r'\s+', '-', slug.strip())
    return slug

def init_categories_local():
    """Initialize categories for local environment"""
    logger.info("Initializing categories for LOCAL environment...")
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=local_engine)
    
    db = Session(local_engine)
    try:
        # Clear existing categories to start fresh
        db.query(Category).delete()
        db.commit()
        logger.info("Cleared existing categories")
        
        # Create categories from config
        for category_key, category_info in LocalConfig.CATEGORIES.items():
            name = category_info['description']
            slug = create_slug(name)
            url = category_info['url']
            
            # Create category
            category = Category(
                name=name,
                slug=slug,
                description=f"Products from {name} category",
                is_active=True
            )
            
            db.add(category)
            logger.info(f"Added category: {name} (slug: {slug})")
        
        db.commit()
        logger.success(f"Successfully created {len(LocalConfig.CATEGORIES)} categories in LOCAL database")
        
        # Display created categories
        categories = db.query(Category).all()
        logger.info("Created categories:")
        for cat in categories:
            logger.info(f"  ID: {cat.id}, Name: {cat.name}, Slug: {cat.slug}")
            
    except Exception as e:
        logger.error(f"Error initializing local categories: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_categories_vps():
    """Initialize categories for VPS environment"""
    logger.info("Initializing categories for VPS environment...")
    
    try:
        # Get VPS engine with lazy loading
        vps_engine = get_vps_engine()
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=vps_engine)
        
        db = Session(vps_engine)
        try:
            # Clear existing categories to start fresh
            db.query(Category).delete()
            db.commit()
            logger.info("Cleared existing categories")
            
            # Create categories from config
            for category_key, category_info in VPSConfig.CATEGORIES.items():
                name = category_info['description']
                slug = create_slug(name)
                url = category_info['url']
                
                # Create category
                category = Category(
                    name=name,
                    slug=slug,
                    description=f"Products from {name} category",
                    is_active=True
                )
                
                db.add(category)
                logger.info(f"Added category: {name} (slug: {slug})")
            
            db.commit()
            logger.success(f"Successfully created {len(VPSConfig.CATEGORIES)} categories in VPS database")
            
            # Display created categories
            categories = db.query(Category).all()
            logger.info("Created categories:")
            for cat in categories:
                logger.info(f"  ID: {cat.id}, Name: {cat.name}, Slug: {cat.slug}")
                
        except Exception as e:
            logger.error(f"Error initializing VPS categories: {e}")
            if 'db' in locals():
                db.rollback()
            raise
        finally:
            if 'db' in locals():
                db.close()
                
    except ImportError as e:
        logger.warning(f"VPS database dependencies not available: {e}")
        logger.info("Skipping VPS category initialization. Install psycopg2 for PostgreSQL support.")
    except Exception as e:
        logger.error(f"Error initializing VPS categories: {e}")
        raise

def main():
    """Main function to run category initialization"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize categories for MedEasy scraper")
    parser.add_argument("--env", choices=["local", "vps", "both"], default="both", 
                       help="Environment to initialize categories for")
    
    args = parser.parse_args()
    
    logger.info("Starting category initialization...")
    
    try:
        if args.env in ["local", "both"]:
            init_categories_local()
            
        if args.env in ["vps", "both"]:
            init_categories_vps()
            
        logger.success("Category initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Category initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 