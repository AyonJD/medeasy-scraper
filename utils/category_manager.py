from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from database.models import Category
from database.connection_local import SessionLocal
from loguru import logger
import re

class CategoryManager:
    """Utility class for managing categories in the database"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def get_or_create_category(self, category_name: str, slug: str = None) -> Optional[Category]:
        """
        Get existing category or create new one
        
        Args:
            category_name: Name of the category
            slug: URL slug (auto-generated if not provided)
            
        Returns:
            Category object or None if failed
        """
        try:
            # Generate slug if not provided
            if not slug:
                slug = self.generate_slug(category_name)
            
            # Check if category exists
            category = self.db.query(Category).filter_by(name=category_name).first()
            
            if category:
                logger.debug(f"Found existing category: {category_name} (ID: {category.id})")
                return category
            
            # Create new category
            category = Category(
                name=category_name,
                slug=slug,
                is_active=True
            )
            
            self.db.add(category)
            self.db.flush()  # Get the ID
            
            logger.info(f"Created new category: {category_name} (ID: {category.id})")
            return category
            
        except Exception as e:
            logger.error(f"Error getting/creating category {category_name}: {e}")
            self.db.rollback()
            return None
    
    def get_or_create_subcategory(self, parent_category_name: str, subcategory_name: str) -> Optional[Category]:
        """
        Get existing subcategory or create new one
        
        Args:
            parent_category_name: Name of the parent category
            subcategory_name: Name of the subcategory
            
        Returns:
            Category object or None if failed
        """
        try:
            # Get or create parent category
            parent_category = self.get_or_create_category(parent_category_name)
            if not parent_category:
                return None
            
            # Generate slug for subcategory
            subcategory_slug = f"{parent_category.slug}-{self.generate_slug(subcategory_name)}"
            
            # Check if subcategory exists
            subcategory = self.db.query(Category).filter_by(
                name=subcategory_name,
                parent_id=parent_category.id
            ).first()
            
            if subcategory:
                logger.debug(f"Found existing subcategory: {subcategory_name} (ID: {subcategory.id})")
                return subcategory
            
            # Create new subcategory
            subcategory = Category(
                name=subcategory_name,
                slug=subcategory_slug,
                parent_id=parent_category.id,
                is_active=True
            )
            
            self.db.add(subcategory)
            self.db.flush()  # Get the ID
            
            logger.info(f"Created new subcategory: {subcategory_name} (ID: {subcategory.id}) under {parent_category_name}")
            return subcategory
            
        except Exception as e:
            logger.error(f"Error getting/creating subcategory {subcategory_name}: {e}")
            self.db.rollback()
            return None
    
    def get_category_by_name(self, category_name: str) -> Optional[Category]:
        """Get category by name"""
        try:
            return self.db.query(Category).filter_by(name=category_name).first()
        except Exception as e:
            logger.error(f"Error getting category {category_name}: {e}")
            return None
    
    def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """Get category by ID"""
        try:
            return self.db.query(Category).filter_by(id=category_id).first()
        except Exception as e:
            logger.error(f"Error getting category ID {category_id}: {e}")
            return None
    
    def get_all_categories(self) -> List[Category]:
        """Get all categories"""
        try:
            return self.db.query(Category).filter_by(parent_id=None).all()
        except Exception as e:
            logger.error(f"Error getting all categories: {e}")
            return []
    
    def get_subcategories(self, parent_category_id: int) -> List[Category]:
        """Get subcategories of a parent category"""
        try:
            return self.db.query(Category).filter_by(parent_id=parent_category_id).all()
        except Exception as e:
            logger.error(f"Error getting subcategories for {parent_category_id}: {e}")
            return []
    
    def generate_slug(self, text: str) -> str:
        """
        Generate URL slug from text
        
        Args:
            text: Text to convert to slug
            
        Returns:
            URL slug
        """
        # Convert to lowercase and replace spaces with hyphens
        slug = text.lower().strip()
        
        # Remove special characters except hyphens
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        
        # Replace multiple spaces/hyphens with single hyphen
        slug = re.sub(r'[\s-]+', '-', slug)
        
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        
        return slug
    
    def commit(self):
        """Commit database changes"""
        try:
            self.db.commit()
        except Exception as e:
            logger.error(f"Error committing changes: {e}")
            self.db.rollback()
    
    def close(self):
        """Close database connection"""
        self.db.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 