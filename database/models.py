from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, Index, JSON, LargeBinary, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    slug = Column(String(200), unique=True, index=True)  # URL slug
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)  # For subcategories
    
    # Metadata
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    parent = relationship("Category", remote_side=[id], backref="subcategories")
    medicines = relationship("Medicine", foreign_keys="Medicine.category_id", back_populates="category_ref")
    
    # Indexes
    __table_args__ = (
        Index('idx_category_name_slug', 'name', 'slug'),
        Index('idx_category_parent', 'parent_id'),
    )

class Medicine(Base):
    __tablename__ = "medicines"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False, index=True)
    generic_name = Column(String(500), index=True)
    brand_name = Column(String(500), index=True)
    manufacturer = Column(String(500), index=True)
    strength = Column(String(200))
    dosage_form = Column(String(200))
    pack_size = Column(String(200))
    price = Column(Float)
    currency = Column(String(10), default="BDT")
    
    # Additional fields for comprehensive data
    description = Column(Text)
    indications = Column(Text)
    contraindications = Column(Text)
    side_effects = Column(Text)
    dosage_instructions = Column(Text)
    storage_conditions = Column(Text)
    
    # Product details
    product_code = Column(String(200), unique=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), index=True)  # Reference to category
    subcategory_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)  # Reference to subcategory
    
    # Image URL (your server's URL)
    image_url = Column(String(1000), index=True)  # Your server's image URL
    
    # Raw data storage for flexibility
    raw_data = Column(JSON)
    
    # Metadata
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_scraped = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    category_ref = relationship("Category", foreign_keys=[category_id], back_populates="medicines")
    subcategory_ref = relationship("Category", foreign_keys=[subcategory_id])
    images = relationship("MedicineImage", back_populates="medicine", cascade="all, delete-orphan")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_medicine_name_manufacturer', 'name', 'manufacturer'),
        Index('idx_medicine_category', 'category_id', 'subcategory_id'),
        Index('idx_medicine_price', 'price'),
        Index('idx_medicine_created', 'created_at'),
    )

class MedicineImage(Base):
    __tablename__ = "medicine_images"
    
    id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False, index=True)
    
    # Image data
    image_data = Column(LargeBinary, nullable=False)  # WebP image data
    original_url = Column(String(1000))  # Original image URL for reference
    file_size = Column(Integer)  # Size in bytes
    width = Column(Integer)  # Image width
    height = Column(Integer)  # Image height
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship to medicine
    medicine = relationship("Medicine", back_populates="images")
    
    # Indexes
    __table_args__ = (
        Index('idx_medicine_image_medicine_id', 'medicine_id'),
        Index('idx_medicine_image_created', 'created_at'),
    )

class ScrapingProgress(Base):
    __tablename__ = "scraping_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(200), nullable=False, index=True)
    current_page = Column(Integer, default=1)
    total_pages = Column(Integer, default=0)
    processed_items = Column(Integer, default=0)
    total_items = Column(Integer, default=0)
    status = Column(String(50), default="running")  # running, completed, failed, paused
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Resume data
    resume_data = Column(JSON)  # Store any data needed for resuming

class ScrapingLog(Base):
    __tablename__ = "scraping_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(200), nullable=False, index=True)
    level = Column(String(20), nullable=False)  # INFO, WARNING, ERROR, DEBUG
    message = Column(Text, nullable=False)
    url = Column(String(1000))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_log_task_level', 'task_name', 'level'),
        Index('idx_log_created', 'created_at'),
    ) 