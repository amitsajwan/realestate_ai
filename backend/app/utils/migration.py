"""
Property Migration Utilities
============================

This module provides utilities for migrating between old and new property schemas
and handling backward compatibility during the consolidation process.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.schemas.unified_property import PropertyDocument, PropertyCreate, PropertyUpdate
from app.schemas.property import PropertyResponse as OldPropertyResponse
from app.schemas.smart_property import SmartPropertyDocument

logger = logging.getLogger(__name__)

class PropertyMigration:
    """Handles migration between different property schemas"""
    
    @staticmethod
    def migrate_old_to_new(old_property: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate old property format to new unified format.
        
        Args:
            old_property: Property data in old format
            
        Returns:
            Property data in new unified format
        """
        try:
            # Map old fields to new fields
            new_property = {
                # Basic fields (direct mapping)
                "title": old_property.get("title", ""),
                "description": old_property.get("description", ""),
                "property_type": old_property.get("property_type", ""),
                "price": float(old_property.get("price", 0)),
                "location": old_property.get("location", ""),
                "bedrooms": old_property.get("bedrooms", 1),
                "bathrooms": float(old_property.get("bathrooms", 1)),
                "area_sqft": old_property.get("area", 0),
                "address": old_property.get("address", ""),
                "amenities": old_property.get("amenities", ""),
                "agent_id": old_property.get("agent_id", ""),
                "status": old_property.get("status", "active"),
                
                # Images
                "images": old_property.get("images", []),
                
                # Features
                "features": old_property.get("features", []),
                
                # Timestamps
                "created_at": old_property.get("created_at", datetime.utcnow()),
                "updated_at": old_property.get("updated_at", datetime.utcnow()),
                
                # AI features (default to disabled)
                "ai_generate": False,
                "template": None,
                "language": "en",
                "ai_content": None,
                
                # Smart features (default to empty)
                "smart_features": {},
                "ai_insights": {},
                "market_analysis": {},
                "recommendations": [],
                "automation_rules": []
            }
            
            # Handle special cases
            if "id" in old_property:
                new_property["_id"] = old_property["id"]
            
            # Convert price to float if it's a string
            if isinstance(new_property["price"], str):
                try:
                    # Remove currency symbols and commas
                    price_str = new_property["price"].replace("₹", "").replace(",", "").replace(" ", "")
                    new_property["price"] = float(price_str)
                except (ValueError, TypeError):
                    new_property["price"] = 0.0
            
            # Ensure numeric fields are properly typed
            for field in ["bedrooms", "bathrooms", "area_sqft"]:
                if isinstance(new_property[field], str):
                    try:
                        new_property[field] = float(new_property[field])
                    except (ValueError, TypeError):
                        new_property[field] = 1 if field in ["bedrooms", "bathrooms"] else 0
            
            logger.info(f"Successfully migrated property: {old_property.get('title', 'Unknown')}")
            return new_property
            
        except Exception as e:
            logger.error(f"Error migrating property: {e}")
            raise ValueError(f"Failed to migrate property: {str(e)}")
    
    @staticmethod
    def migrate_smart_to_new(smart_property: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate smart property format to new unified format.
        
        Args:
            smart_property: Smart property data
            
        Returns:
            Property data in new unified format
        """
        try:
            # Get the base property data
            base_property = smart_property.get("property_data", {})
            
            # Map smart property fields to new format
            new_property = {
                # Basic fields from base property
                "title": base_property.get("title", ""),
                "description": base_property.get("description", ""),
                "property_type": base_property.get("property_type", ""),
                "price": float(base_property.get("price", 0)),
                "location": base_property.get("location", ""),
                "bedrooms": base_property.get("bedrooms", 1),
                "bathrooms": float(base_property.get("bathrooms", 1)),
                "area_sqft": base_property.get("area", 0),
                "address": base_property.get("address", ""),
                "amenities": base_property.get("amenities", ""),
                "agent_id": smart_property.get("user_id", ""),
                "status": "active",
                
                # Images
                "images": base_property.get("images", []),
                
                # Features
                "features": base_property.get("features", []),
                
                # Timestamps
                "created_at": smart_property.get("created_at", datetime.utcnow()),
                "updated_at": smart_property.get("updated_at", datetime.utcnow()),
                
                # AI features (enabled for smart properties)
                "ai_generate": True,
                "template": smart_property.get("template", "smart"),
                "language": smart_property.get("language", "en"),
                "ai_content": smart_property.get("ai_content"),
                
                # Smart features (migrate from smart property)
                "smart_features": smart_property.get("smart_features", {}),
                "ai_insights": smart_property.get("ai_insights", {}),
                "market_analysis": smart_property.get("market_analysis", {}),
                "recommendations": smart_property.get("recommendations", []),
                "automation_rules": smart_property.get("automation_rules", [])
            }
            
            # Handle special cases
            if "id" in smart_property:
                new_property["_id"] = smart_property["id"]
            
            logger.info(f"Successfully migrated smart property: {base_property.get('title', 'Unknown')}")
            return new_property
            
        except Exception as e:
            logger.error(f"Error migrating smart property: {e}")
            raise ValueError(f"Failed to migrate smart property: {str(e)}")
    
    @staticmethod
    def migrate_new_to_old(new_property: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate new unified format back to old format for backward compatibility.
        
        Args:
            new_property: Property data in new unified format
            
        Returns:
            Property data in old format
        """
        try:
            old_property = {
                "id": str(new_property.get("_id", "")),
                "title": new_property.get("title", ""),
                "description": new_property.get("description", ""),
                "property_type": new_property.get("property_type", ""),
                "price": new_property.get("price", 0),
                "location": new_property.get("location", ""),
                "bedrooms": new_property.get("bedrooms", 1),
                "bathrooms": new_property.get("bathrooms", 1),
                "area": new_property.get("area_sqft", 0),
                "address": new_property.get("address", ""),
                "amenities": new_property.get("amenities", ""),
                "agent_id": new_property.get("agent_id", ""),
                "status": new_property.get("status", "active"),
                "images": new_property.get("images", []),
                "features": new_property.get("features", []),
                "created_at": new_property.get("created_at", datetime.utcnow()),
                "updated_at": new_property.get("updated_at", datetime.utcnow())
            }
            
            logger.info(f"Successfully migrated property back to old format: {new_property.get('title', 'Unknown')}")
            return old_property
            
        except Exception as e:
            logger.error(f"Error migrating property back to old format: {e}")
            raise ValueError(f"Failed to migrate property back to old format: {str(e)}")
    
    @staticmethod
    def validate_migration(old_property: Dict[str, Any], new_property: Dict[str, Any]) -> bool:
        """
        Validate that migration was successful by comparing key fields.
        
        Args:
            old_property: Original property data
            new_property: Migrated property data
            
        Returns:
            True if migration is valid, False otherwise
        """
        try:
            # Check key fields
            key_fields = ["title", "description", "property_type", "price", "location", "bedrooms", "bathrooms"]
            
            for field in key_fields:
                old_value = old_property.get(field)
                new_value = new_property.get(field)
                
                # Handle special cases
                if field == "price":
                    # Convert both to float for comparison
                    try:
                        old_float = float(str(old_value).replace("₹", "").replace(",", "").replace(" ", ""))
                        new_float = float(new_value)
                        if abs(old_float - new_float) > 0.01:  # Allow small floating point differences
                            logger.warning(f"Price mismatch: {old_float} vs {new_float}")
                            return False
                    except (ValueError, TypeError):
                        logger.warning(f"Could not compare prices: {old_value} vs {new_value}")
                        return False
                elif field == "bathrooms":
                    # Allow float comparison for bathrooms
                    if abs(float(old_value) - float(new_value)) > 0.01:
                        logger.warning(f"Bathrooms mismatch: {old_value} vs {new_value}")
                        return False
                else:
                    # String comparison for other fields
                    if str(old_value) != str(new_value):
                        logger.warning(f"Field mismatch for {field}: {old_value} vs {new_value}")
                        return False
            
            logger.info("Migration validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Error validating migration: {e}")
            return False

class BatchMigration:
    """Handles batch migration of multiple properties"""
    
    def __init__(self, db):
        self.db = db
        self.old_collection = db.properties_old
        self.new_collection = db.properties
        self.logger = logging.getLogger(__name__)
    
    async def migrate_all_properties(self, batch_size: int = 100) -> Dict[str, Any]:
        """
        Migrate all properties from old collection to new collection.
        
        Args:
            batch_size: Number of properties to process in each batch
            
        Returns:
            Migration results summary
        """
        try:
            results = {
                "total_processed": 0,
                "successful": 0,
                "failed": 0,
                "errors": []
            }
            
            # Get total count
            total_count = await self.old_collection.count_documents({})
            self.logger.info(f"Starting migration of {total_count} properties")
            
            # Process in batches
            skip = 0
            while skip < total_count:
                # Get batch of old properties
                cursor = self.old_collection.find({}).skip(skip).limit(batch_size)
                batch = await cursor.to_list(length=batch_size)
                
                for old_property in batch:
                    try:
                        # Migrate property
                        new_property = PropertyMigration.migrate_old_to_new(old_property)
                        
                        # Validate migration
                        if PropertyMigration.validate_migration(old_property, new_property):
                            # Insert into new collection
                            await self.new_collection.insert_one(new_property)
                            results["successful"] += 1
                        else:
                            results["failed"] += 1
                            results["errors"].append(f"Validation failed for property: {old_property.get('title', 'Unknown')}")
                        
                        results["total_processed"] += 1
                        
                    except Exception as e:
                        results["failed"] += 1
                        error_msg = f"Failed to migrate property {old_property.get('title', 'Unknown')}: {str(e)}"
                        results["errors"].append(error_msg)
                        self.logger.error(error_msg)
                
                skip += batch_size
                self.logger.info(f"Processed {skip}/{total_count} properties")
            
            self.logger.info(f"Migration completed: {results['successful']} successful, {results['failed']} failed")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in batch migration: {e}")
            raise
    
    async def rollback_migration(self, batch_size: int = 100) -> Dict[str, Any]:
        """
        Rollback migration by removing migrated properties from new collection.
        
        Args:
            batch_size: Number of properties to process in each batch
            
        Returns:
            Rollback results summary
        """
        try:
            results = {
                "total_processed": 0,
                "successful": 0,
                "failed": 0,
                "errors": []
            }
            
            # Get total count
            total_count = await self.new_collection.count_documents({})
            self.logger.info(f"Starting rollback of {total_count} properties")
            
            # Process in batches
            skip = 0
            while skip < total_count:
                # Get batch of new properties
                cursor = self.new_collection.find({}).skip(skip).limit(batch_size)
                batch = await cursor.to_list(length=batch_size)
                
                for new_property in batch:
                    try:
                        # Remove from new collection
                        result = await self.new_collection.delete_one({"_id": new_property["_id"]})
                        
                        if result.deleted_count == 1:
                            results["successful"] += 1
                        else:
                            results["failed"] += 1
                            results["errors"].append(f"Failed to delete property: {new_property.get('title', 'Unknown')}")
                        
                        results["total_processed"] += 1
                        
                    except Exception as e:
                        results["failed"] += 1
                        error_msg = f"Failed to rollback property {new_property.get('title', 'Unknown')}: {str(e)}"
                        results["errors"].append(error_msg)
                        self.logger.error(error_msg)
                
                skip += batch_size
                self.logger.info(f"Processed {skip}/{total_count} properties")
            
            self.logger.info(f"Rollback completed: {results['successful']} successful, {results['failed']} failed")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in rollback: {e}")
            raise

class MigrationValidator:
    """Validates migration results and data integrity"""
    
    @staticmethod
    async def validate_data_integrity(db) -> Dict[str, Any]:
        """
        Validate data integrity after migration.
        
        Args:
            db: Database connection
            
        Returns:
            Validation results
        """
        try:
            results = {
                "total_old": 0,
                "total_new": 0,
                "missing_properties": [],
                "data_mismatches": [],
                "integrity_score": 0
            }
            
            # Count properties in both collections
            old_count = await db.properties_old.count_documents({})
            new_count = await db.properties.count_documents({})
            
            results["total_old"] = old_count
            results["total_new"] = new_count
            
            # Check for missing properties
            if old_count != new_count:
                results["missing_properties"].append(f"Count mismatch: {old_count} old vs {new_count} new")
            
            # Sample validation of migrated data
            sample_size = min(100, old_count)
            old_cursor = db.properties_old.find({}).limit(sample_size)
            old_sample = await old_cursor.to_list(length=sample_size)
            
            for old_property in old_sample:
                try:
                    # Find corresponding new property
                    new_property = await db.properties.find_one({
                        "title": old_property.get("title"),
                        "agent_id": old_property.get("agent_id")
                    })
                    
                    if not new_property:
                        results["missing_properties"].append(f"Missing: {old_property.get('title', 'Unknown')}")
                    else:
                        # Validate key fields
                        if not PropertyMigration.validate_migration(old_property, new_property):
                            results["data_mismatches"].append(f"Mismatch: {old_property.get('title', 'Unknown')}")
                
                except Exception as e:
                    results["data_mismatches"].append(f"Validation error for {old_property.get('title', 'Unknown')}: {str(e)}")
            
            # Calculate integrity score
            total_checks = len(old_sample)
            successful_checks = total_checks - len(results["missing_properties"]) - len(results["data_mismatches"])
            results["integrity_score"] = (successful_checks / total_checks * 100) if total_checks > 0 else 0
            
            return results
            
        except Exception as e:
            logger.error(f"Error validating data integrity: {e}")
            raise