#!/usr/bin/env python3
"""
Initialize categories in a fresh database
"""

from database.connection_local import init_db, SessionLocal
from database.models import Category

def init_categories():
    """Initialize all categories"""
    try:
        # Initialize database
        print("Initializing database...")
        init_db()
        
        # Create database session
        db = SessionLocal()
        
        # Define categories
        categories = [
            Category(name="Women's health and hygiene products", slug="womens-choice"),
            Category(name="Sexual wellness and contraceptive products", slug="sexual-wellness"),
            Category(name="Skincare and beauty products", slug="skin-care"),
            Category(name="Diabetes management products", slug="diabetic-care"),
            Category(name="Medical devices and equipment", slug="devices"),
            Category(name="Nutritional supplements", slug="supplement"),
            Category(name="Baby diapers and related products", slug="diapers"),
            Category(name="Baby care products", slug="baby-care"),
            Category(name="Personal care and hygiene products", slug="personal-care"),
            Category(name="Hygiene and freshness products", slug="hygiene-and-freshness"),
            Category(name="Dental care products", slug="dental-care"),
            Category(name="Herbal and natural medicines", slug="herbal-medicine"),
            Category(name="Prescription medicines", slug="prescription-medicine"),
            Category(name="Over-the-counter medicines", slug="otc-medicine")
        ]
        
        # Add categories to database
        print("Creating categories...")
        for category in categories:
            db.add(category)
        
        # Commit changes
        db.commit()
        
        # Verify categories were created
        created_categories = db.query(Category).all()
        print(f"Successfully created {len(created_categories)} categories:")
        
        for cat in created_categories:
            print(f"  ID: {cat.id}, Name: {cat.name}, Slug: {cat.slug}")
        
        db.close()
        print("Category initialization completed successfully!")
        
    except Exception as e:
        print(f"Error initializing categories: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        raise

if __name__ == "__main__":
    init_categories() 