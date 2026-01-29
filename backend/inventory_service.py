from backend.db_connection import DatabaseConnection
from typing import Optional, List, Dict, Tuple
from fuzzywuzzy import fuzz, process
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class InventoryService:
    """Service for managing pharmacy inventory"""
    
    @staticmethod
    def search_medicine(medicine_name: str, threshold: int = 70) -> Optional[Dict]:
        """
        Search for medicine with fuzzy matching
        
        Args:
            medicine_name: Name to search for
            threshold: Minimum fuzzy match score (0-100)
        
        Returns:
            Best matching medicine or None
        """
        try:
            with DatabaseConnection.get_cursor() as cursor:
                # Get all medicine names
                cursor.execute("SELECT medicine_id, medicine_name FROM medicines")
                all_medicines = cursor.fetchall()
                
                if not all_medicines:
                    return None
                
                # Create list of names for fuzzy matching
                medicine_names = {m['medicine_name']: m['medicine_id'] for m in all_medicines}
                
                # Find best match
                best_match = process.extractOne(
                    medicine_name, 
                    medicine_names.keys(),
                    scorer=fuzz.token_sort_ratio
                )
                
                if best_match and best_match[1] >= threshold:
                    matched_name = best_match[0]
                    medicine_id = medicine_names[matched_name]
                    
                    # Get full details
                    cursor.execute(
                        """
                        SELECT medicine_id, medicine_name, generic_name, manufacturer,
                               category, unit_price, stock_quantity, reorder_level,
                               expiry_date, instructions
                        FROM medicines
                        WHERE medicine_id = %s
                        """,
                        (medicine_id,)
                    )
                    
                    medicine = cursor.fetchone()
                    if medicine:
                        medicine['match_score'] = best_match[1]
                        medicine['searched_term'] = medicine_name
                        return dict(medicine)
                
                return None
                
        except Exception as e:
            logger.error(f"Error searching medicine: {e}")
            return None
    
    @staticmethod
    def check_medicine_stock(medicine_name: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Check stock availability for a medicine
        
        Returns:
            (success, message, medicine_data)
        """
        try:
            medicine = InventoryService.search_medicine(medicine_name)
            
            if not medicine:
                return False, f"Medicine '{medicine_name}' not found in inventory", None
            
            # Check if different name was matched
            if medicine['searched_term'].lower() != medicine['medicine_name'].lower():
                message = f"Found '{medicine['medicine_name']}' (you searched: '{medicine_name}')"
            else:
                message = f"Found '{medicine['medicine_name']}'"
            
            return True, message, medicine
            
        except Exception as e:
            logger.error(f"Error checking stock: {e}")
            return False, "Failed to check stock", None
    
    @staticmethod
    def check_prescription_availability(medicine_list: List[str]) -> List[Dict]:
        """
        Check availability of multiple medicines from prescription
        
        Args:
            medicine_list: List of medicine names
        
        Returns:
            List of dicts with medicine info and availability
        """
        results = []
        
        for medicine_name in medicine_list:
            success, message, medicine_data = InventoryService.check_medicine_stock(medicine_name)
            
            result = {
                'searched_name': medicine_name,
                'found': success,
                'message': message
            }
            
            if success and medicine_data:
                result.update({
                    'medicine_name': medicine_data['medicine_name'],
                    'stock_quantity': medicine_data['stock_quantity'],
                    'in_stock': medicine_data['stock_quantity'] > 0,
                    'expiry_date': medicine_data['expiry_date'],
                    'unit_price': medicine_data['unit_price']
                })
            else:
                result.update({
                    'medicine_name': None,
                    'stock_quantity': 0,
                    'in_stock': False,
                    'expiry_date': None,
                    'unit_price': None
                })
            
            results.append(result)
        
        return results
    
    @staticmethod
    def update_medicine_stock(
        medicine_name: str,
        quantity: Optional[int] = None,
        expiry_date: Optional[str] = None,
        manufacturer: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Update medicine stock information
        
        Args:
            medicine_name: Name of medicine
            quantity: New stock quantity (optional)
            expiry_date: New expiry date in YYYY-MM-DD (optional)
            manufacturer: Manufacturer/supplier info (optional)
        
        Returns:
            (success, message)
        """
        try:
            # Find medicine
            medicine = InventoryService.search_medicine(medicine_name)
            
            if not medicine:
                return False, f"Medicine '{medicine_name}' not found"
            
            medicine_id = medicine['medicine_id']
            update_fields = []
            params = []
            
            if quantity is not None:
                update_fields.append("stock_quantity = %s")
                params.append(quantity)
            
            if expiry_date is not None:
                update_fields.append("expiry_date = %s")
                params.append(expiry_date)
            
            if manufacturer is not None:
                update_fields.append("manufacturer = %s")
                params.append(manufacturer)
            
            if not update_fields:
                return False, "No fields to update"
            
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            params.append(medicine_id)
            
            with DatabaseConnection.get_cursor() as cursor:
                query = f"""
                    UPDATE medicines
                    SET {', '.join(update_fields)}
                    WHERE medicine_id = %s
                """
                cursor.execute(query, params)
                
                if cursor.rowcount > 0:
                    return True, f"Successfully updated '{medicine['medicine_name']}'"
                else:
                    return False, "Failed to update medicine"
                    
        except Exception as e:
            logger.error(f"Error updating medicine: {e}")
            return False, f"Update failed: {str(e)}"
    
    @staticmethod
    def add_new_medicine(
        medicine_name: str,
        generic_name: Optional[str] = None,
        manufacturer: Optional[str] = None,
        category: Optional[str] = None,
        unit_price: Optional[float] = None,
        stock_quantity: int = 0,
        reorder_level: int = 10,
        expiry_date: Optional[str] = None,
        instructions: Optional[str] = None
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Add a new medicine to inventory
        
        Returns:
            (success, message, medicine_id)
        """
        try:
            # Check if medicine already exists
            existing = InventoryService.search_medicine(medicine_name, threshold=90)
            
            if existing and existing['match_score'] > 90:
                return False, f"Medicine '{existing['medicine_name']}' already exists", None
            
            with DatabaseConnection.get_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO medicines (
                        medicine_name, generic_name, manufacturer, category,
                        unit_price, stock_quantity, reorder_level, expiry_date, instructions
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING medicine_id
                    """,
                    (medicine_name, generic_name, manufacturer, category,
                     unit_price, stock_quantity, reorder_level, expiry_date, instructions)
                )
                
                medicine_id = cursor.fetchone()['medicine_id']
                return True, f"Successfully added '{medicine_name}' to inventory", medicine_id
                
        except Exception as e:
            logger.error(f"Error adding medicine: {e}")
            return False, f"Failed to add medicine: {str(e)}", None
    
    @staticmethod
    def get_low_stock_medicines(threshold: Optional[int] = None) -> List[Dict]:
        """Get medicines below reorder level"""
        try:
            with DatabaseConnection.get_cursor() as cursor:
                if threshold:
                    query = """
                        SELECT * FROM medicines
                        WHERE stock_quantity <= %s
                        ORDER BY stock_quantity ASC
                    """
                    cursor.execute(query, (threshold,))
                else:
                    query = """
                        SELECT * FROM medicines
                        WHERE stock_quantity <= reorder_level
                        ORDER BY stock_quantity ASC
                    """
                    cursor.execute(query)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting low stock: {e}")
            return []
    
    @staticmethod
    def get_expiring_medicines(days: int = 30) -> List[Dict]:
        """Get medicines expiring within specified days"""
        try:
            with DatabaseConnection.get_cursor() as cursor:
                expiry_threshold = datetime.now().date() + timedelta(days=days)
                
                cursor.execute(
                    """
                    SELECT * FROM medicines
                    WHERE expiry_date IS NOT NULL 
                      AND expiry_date <= %s
                      AND expiry_date >= CURRENT_DATE
                    ORDER BY expiry_date ASC
                    """,
                    (expiry_threshold,)
                )
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting expiring medicines: {e}")
            return []
    
    @staticmethod
    def get_full_inventory() -> List[Dict]:
        """Get complete inventory list"""
        try:
            with DatabaseConnection.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT * FROM medicines
                    ORDER BY medicine_name ASC
                    """
                )
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting full inventory: {e}")
            return []


# Global instance
inventory_service = InventoryService()
