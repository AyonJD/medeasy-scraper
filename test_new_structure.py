#!/usr/bin/env python3
"""
Test script for the new database structure with image processing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection_local import SessionLocal, init_db
from database.models import Medicine, MedicineImage
from utils.image_processor import ImageProcessor
from loguru import logger

def test_database_structure():
    """Test the new database structure"""
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized successfully")
        
        # Test database connection
        db = SessionLocal()
        
        # Check if tables exist
        medicine_count = db.query(Medicine).count()
        image_count = db.query(MedicineImage).count()
        
        logger.info(f"Current database state:")
        logger.info(f"  Medicines: {medicine_count}")
        logger.info(f"  Images: {image_count}")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"Database structure test failed: {e}")
        return False

def test_image_processor():
    """Test the image processor"""
    try:
        processor = ImageProcessor()
        
        # Test with a sample image URL
        test_url = "https://via.placeholder.com/300x200/FF0000/FFFFFF?text=Test+Image"
        
        logger.info(f"Testing image processor with: {test_url}")
        
        image_data = processor.download_and_convert_to_webp(test_url)
        
        if image_data:
            logger.info(f"Image processing successful:")
            logger.info(f"  Size: {image_data['width']}x{image_data['height']}")
            logger.info(f"  File size: {image_data['file_size']} bytes")
            logger.info(f"  Format: {image_data['format']}")
            logger.info(f"  Hash: {image_data['hash']}")
            return True
        else:
            logger.error("Image processing failed")
            return False
            
    except Exception as e:
        logger.error(f"Image processor test failed: {e}")
        return False
    finally:
        processor.close()

def test_medicine_with_image():
    """Test creating a medicine with image"""
    try:
        db = SessionLocal()
        
        # Create a test medicine
        test_medicine = Medicine(
            name="Test Medicine",
            generic_name="Test Generic",
            brand_name="Test Brand",
            manufacturer="Test Manufacturer",
            strength="500mg",
            dosage_form="Tablet",
            pack_size="30 tablets",
            price=100.0,
            currency="BDT",
            category="Test Category",
            product_code="TEST001"
        )
        
        db.add(test_medicine)
        db.flush()  # Get the ID
        
        logger.info(f"Created test medicine with ID: {test_medicine.id}")
        
        # Process a test image
        processor = ImageProcessor()
        test_url = "https://via.placeholder.com/400x300/00FF00/FFFFFF?text=Medicine+Image"
        
        image_data = processor.download_and_convert_to_webp(test_url)
        
        if image_data:
            # Create image record
            medicine_image = MedicineImage(
                medicine_id=test_medicine.id,
                image_data=image_data['image_data'],
                original_url=image_data['original_url'],
                file_size=image_data['file_size'],
                width=image_data['width'],
                height=image_data['height']
            )
            
            db.add(medicine_image)
            db.commit()
            
            logger.info(f"Successfully created medicine with image:")
            logger.info(f"  Medicine ID: {test_medicine.id}")
            logger.info(f"  Image ID: {medicine_image.id}")
            logger.info(f"  Image size: {image_data['width']}x{image_data['height']}")
            logger.info(f"  File size: {image_data['file_size']} bytes")
            
            # Verify the relationship
            medicine_with_image = db.query(Medicine).filter(Medicine.id == test_medicine.id).first()
            logger.info(f"Medicine has {len(medicine_with_image.images)} images")
            
            # Clean up
            db.delete(medicine_image)
            db.delete(test_medicine)
            db.commit()
            
            logger.info("Test data cleaned up")
            return True
        else:
            logger.error("Failed to process test image")
            db.rollback()
            return False
            
    except Exception as e:
        logger.error(f"Medicine with image test failed: {e}")
        db.rollback()
        return False
    finally:
        processor.close()
        db.close()

def main():
    """Run all tests"""
    logger.info("Starting new structure tests...")
    
    tests = [
        ("Database Structure", test_database_structure),
        ("Image Processor", test_image_processor),
        ("Medicine with Image", test_medicine_with_image)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                logger.success(f"✓ {test_name} PASSED")
            else:
                logger.error(f"✗ {test_name} FAILED")
                
        except Exception as e:
            logger.error(f"✗ {test_name} FAILED with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.success("All tests passed! New structure is working correctly.")
        return True
    else:
        logger.error("Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 