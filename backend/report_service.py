from backend.db_connection import DatabaseConnection
from typing import Optional, List, Dict
import pandas as pd
from datetime import datetime
import logging
import io

logger = logging.getLogger(__name__)


class ReportService:
    """Service for generating reports"""
    
    @staticmethod
    def generate_appointments_report(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        doctor_id: Optional[int] = None,
        specialization: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Generate appointments report with filters
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            doctor_id: Filter by specific doctor
            specialization: Filter by specialization
        
        Returns:
            DataFrame with appointment data
        """
        try:
            query = """
                SELECT 
                    a.appointment_id,
                    a.appointment_date,
                    a.appointment_time,
                    a.patient_name,
                    a.patient_contact,
                    a.symptoms,
                    a.status,
                    d.full_name as doctor_name,
                    d.specialization,
                    d.consultation_fee,
                    a.created_at
                FROM appointments a
                JOIN doctors d ON a.doctor_id = d.doctor_id
                WHERE 1=1
            """
            
            params = []
            
            if start_date:
                query += " AND a.appointment_date >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND a.appointment_date <= %s"
                params.append(end_date)
            
            if doctor_id:
                query += " AND a.doctor_id = %s"
                params.append(doctor_id)
            
            if specialization:
                query += " AND d.specialization ILIKE %s"
                params.append(f"%{specialization}%")
            
            query += " ORDER BY a.appointment_date DESC, a.appointment_time DESC"
            
            with DatabaseConnection.get_cursor() as cursor:
                cursor.execute(query, params)
                data = cursor.fetchall()
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame([dict(row) for row in data])
            return df
            
        except Exception as e:
            logger.error(f"Error generating appointments report: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def generate_inventory_report(filter_type: str = 'full') -> pd.DataFrame:
        """
        Generate inventory report
        
        Args:
            filter_type: 'low_stock', 'expiring', or 'full'
        
        Returns:
            DataFrame with inventory data
        """
        try:
            if filter_type == 'low_stock':
                query = """
                    SELECT * FROM medicines
                    WHERE stock_quantity <= reorder_level
                    ORDER BY stock_quantity ASC
                """
            elif filter_type == 'expiring':
                query = """
                    SELECT * FROM medicines
                    WHERE expiry_date IS NOT NULL 
                      AND expiry_date <= CURRENT_DATE + INTERVAL '30 days'
                      AND expiry_date >= CURRENT_DATE
                    ORDER BY expiry_date ASC
                """
            else:  # full
                query = """
                    SELECT * FROM medicines
                    ORDER BY medicine_name ASC
                """
            
            with DatabaseConnection.get_cursor() as cursor:
                cursor.execute(query)
                data = cursor.fetchall()
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame([dict(row) for row in data])
            return df
            
        except Exception as e:
            logger.error(f"Error generating inventory report: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def generate_bank_report(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Generate bank statement report
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            DataFrame with bank transactions
        """
        try:
            query = """
                SELECT 
                    statement_id,
                    statement_date,
                    transaction_type,
                    amount,
                    balance,
                    description,
                    created_at
                FROM bank_statements
                WHERE 1=1
            """
            
            params = []
            
            if start_date:
                query += " AND statement_date >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND statement_date <= %s"
                params.append(end_date)
            
            query += " ORDER BY statement_date DESC, created_at DESC"
            
            with DatabaseConnection.get_cursor() as cursor:
                cursor.execute(query, params)
                data = cursor.fetchall()
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame([dict(row) for row in data])
            return df
            
        except Exception as e:
            logger.error(f"Error generating bank report: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def generate_pos_report(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        report_type: str = 'summary'
    ) -> pd.DataFrame:
        """
        Generate POS report
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            report_type: 'summary' or 'details'
        
        Returns:
            DataFrame with POS data
        """
        try:
            if report_type == 'summary':
                query = """
                    SELECT 
                        DATE(transaction_date) as date,
                        COUNT(*) as total_transactions,
                        SUM(total_amount) as total_sales,
                        AVG(total_amount) as average_sale,
                        payment_method
                    FROM pos_transactions
                    WHERE 1=1
                """
                
                params = []
                
                if start_date:
                    query += " AND DATE(transaction_date) >= %s"
                    params.append(start_date)
                
                if end_date:
                    query += " AND DATE(transaction_date) <= %s"
                    params.append(end_date)
                
                query += " GROUP BY DATE(transaction_date), payment_method"
                query += " ORDER BY date DESC"
                
            else:  # details
                query = """
                    SELECT 
                        transaction_id,
                        transaction_date,
                        total_amount,
                        payment_method,
                        items,
                        created_at
                    FROM pos_transactions
                    WHERE 1=1
                """
                
                params = []
                
                if start_date:
                    query += " AND DATE(transaction_date) >= %s"
                    params.append(start_date)
                
                if end_date:
                    query += " AND DATE(transaction_date) <= %s"
                    params.append(end_date)
                
                query += " ORDER BY transaction_date DESC"
            
            with DatabaseConnection.get_cursor() as cursor:
                cursor.execute(query, params)
                data = cursor.fetchall()
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame([dict(row) for row in data])
            return df
            
        except Exception as e:
            logger.error(f"Error generating POS report: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def dataframe_to_excel(df: pd.DataFrame, filename: str = 'report.xlsx') -> bytes:
        """
        Convert DataFrame to Excel bytes for download
        
        Args:
            df: DataFrame to convert
            filename: Name for the file
        
        Returns:
            Excel file as bytes
        """
        try:
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Report')
            
            output.seek(0)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error creating Excel file: {e}")
            return b''


# Global instance
report_service = ReportService()
