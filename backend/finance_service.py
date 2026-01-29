from backend.db_connection import DatabaseConnection
from backend.ocr_service import ocr_service
from typing import Optional, List, Dict, Tuple, Any
import re
import logging
from datetime import datetime
import pandas as pd


logger = logging.getLogger(__name__)


class FinanceService:
    """Service for handling bank statements, POS receipts, and supplier invoices"""
    
    def classify_document_type(self, image_bytes: bytes) -> Tuple[str, float]:
        """
        Classify document type: 'bank', 'pos', or 'supplier'
        
        Returns:
            (document_type, confidence_score)
        """
        try:
            extracted_text = ocr_service.extract_text_from_image(image_bytes)
            
            if not extracted_text:
                return 'unknown', 0.0
            
            text_lower = extracted_text.lower()
            
            bank_score = 0
            bank_keywords = ['tran id', 'transaction id', 'txn date', 'balance', 'cr/dr', 
                           'bank statement', 'account statement', 'opening balance', 'closing balance']
            for keyword in bank_keywords:
                if keyword in text_lower:
                    bank_score += 1
            
            pos_score = 0
            pos_keywords = ['receipt', 'pos', 'medicare pharmacy', 'medicarepharmacy', 
                          'pharmacist dr', 'payment mode', 'cgst', 'sgst', 'thank you']
            for keyword in pos_keywords:
                if keyword in text_lower:
                    pos_score += 1
            
            supplier_score = 0
            supplier_keywords = ['invoice', 'pharmasupply', 'gstin', 'bill to', 'supplier', 
                               'po ref', 'delivery date', 'vehicle', 'manufacturer', 'batch']
            for keyword in supplier_keywords:
                if keyword in text_lower:
                    supplier_score += 1
            
            max_score = max(bank_score, pos_score, supplier_score)
            
            if max_score == 0:
                return 'unknown', 0.0
            
            if bank_score == max_score:
                return 'bank', bank_score / len(bank_keywords)
            elif supplier_score == max_score:
                return 'supplier', supplier_score / len(supplier_keywords)
            else:
                return 'pos', pos_score / len(pos_keywords)
        
        except Exception as e:
            logger.error(f"Error classifying document: {e}")
            return 'unknown', 0.0
    
    def extract_document(self, image_bytes: bytes, doc_type: Optional[str] = None) -> Tuple[bool, str, str, Any]:
        """
        Universal document extraction with auto-classification
        
        Returns:
            (success, message, document_type, extracted_data)
        """
        try:
            if not doc_type:
                doc_type, confidence = self.classify_document_type(image_bytes)
                
                if doc_type == 'unknown':
                    return False, "Could not determine document type. Please specify manually.", 'unknown', None
                
                logger.info(f"Classified as {doc_type} with confidence {confidence:.2f}")
            
            if doc_type == 'bank':
                success, message, data = self.extract_bank_statement_table(image_bytes)
                return success, message, 'bank', data
            
            elif doc_type == 'pos':
                success, message, data = self.extract_pos_statement(image_bytes)
                return success, message, 'pos', data
            
            elif doc_type == 'supplier':
                success, message, data = self.extract_supplier_invoice(image_bytes)
                return success, message, 'supplier', data
            
            else:
                return False, f"Unsupported document type: {doc_type}", 'unknown', None
        
        except Exception as e:
            logger.error(f"Document extraction error: {e}", exc_info=True)
            return False, f"Extraction failed: {str(e)}", 'unknown', None
    
    def extract_bank_statement_table(self, image_bytes: bytes) -> Tuple[bool, str, List[Dict]]:
        """Extract bank statement transactions using DataFrame"""
        try:
            df = ocr_service.extract_table_from_image(image_bytes)
            
            if df is None or len(df) == 0:
                return False, "Failed to extract table from image", []
            
            logger.info(f"Extracted table: {df.shape[0]} rows x {df.shape[1]} columns")
            
            transactions = self._parse_bank_from_dataframe(df)
            
            if not transactions:
                return False, "No valid transactions found", []
            
            return True, f"Successfully extracted {len(transactions)} transactions", transactions
            
        except Exception as e:
            logger.error(f"Error extracting bank statement: {str(e)}", exc_info=True)
            return False, f"Extraction failed: {str(e)}", []
    
    def _parse_bank_from_dataframe(self, df: pd.DataFrame) -> List[Dict]:
        """Parse bank statement from DataFrame (FIXED - follows POS/Supplier logic)"""
        transactions = []
        
        # Convert all rows to list of lists
        all_rows = []
        for i, row in df.iterrows():
            row_data = [str(cell).strip() for cell in row.values]
            all_rows.append(row_data)
        
        # Find header row
        header_idx = None
        for i, row in enumerate(all_rows):
            row_text = ' '.join(row).lower()
            if 'tran id' in row_text or 'transaction id' in row_text:
                header_idx = i
                logger.info(f"Found header at row {i}")
                break
        
        if header_idx is None:
            logger.warning("Could not find transaction table header")
            return []
        
        logger.info(f"📝 Processing {len(all_rows) - header_idx - 1} rows after header")
        
        # Parse transactions (rows after header)
        for i in range(header_idx + 1, len(all_rows)):
            row = all_rows[i]
            row_text = ' '.join(row).lower()
            
            # STOP at footer keywords (same as POS/Supplier)
            if any(kw in row_text for kw in ['opening balance', 'closing balance', 'total', 'summary', 'page']):
                logger.info(f"⏸️ Stopped at footer keyword at row {i}")
                continue
            
            # Validate row has minimum 6 columns
            if len(row) < 6:
                continue
            
            # First column should be transaction ID (S followed by 7 digits)
            if not row[0] or not re.match(r'^S\d{7}$', row[0].replace('$', 'S')):
                continue
            
            tran_id = row[0].replace('$', 'S')
            
            # Second column should be date (DD/MM/YYYY or DD-MM-YYYY)
            txn_date = self._parse_date(row[1])
            if not txn_date:
                logger.warning(f"⚠️ Invalid date '{row[1]}' for {tran_id}")
                continue
            
            # Third column is CR/DR
            cr_dr = row[2].strip().upper()
            if cr_dr not in ['CR', 'DR']:
                logger.warning(f"⚠️ Invalid CR/DR '{row[2]}' for {tran_id}, defaulting to DR")
                cr_dr = 'DR'
            
            # Fourth column is amount (must be numeric)
            if not row[3] or not re.match(r'^[\d\.,]+$', row[3].strip()):
                logger.warning(f"⚠️ Invalid amount '{row[3]}' for {tran_id}")
                continue
            amount = self._parse_amount(row[3])
            
            # Fifth column is balance (must be numeric)
            if not row[4] or not re.match(r'^[\d\.,]+$', row[4].strip()):
                logger.warning(f"⚠️ Invalid balance '{row[4]}' for {tran_id}")
                continue
            balance = self._parse_amount(row[4])
            
            # Sixth column is description
            description = row[5] if len(row) > 5 and row[5] else 'N/A'
            
            # Truncate description to fit DB column (250 chars)
            if len(description) > 250:
                description = description[:247] + '...'
            
            transactions.append({
                'tran_id': tran_id,
                'txn_date': txn_date,
                'cr_dr': cr_dr,
                'amount': amount,
                'balance': balance,
                'description': description
            })
            
            logger.info(f"✅ Parsed: {tran_id} | {txn_date} | {cr_dr} | {amount:.2f} | {balance:.2f}")
        
        logger.info(f"✅ Successfully parsed {len(transactions)} bank transactions")
        return transactions
    
    def _parse_date(self, date_str: str) -> str:
        """Parse date string to YYYY-MM-DD format"""
        try:
            if '/' in date_str:
                dt = datetime.strptime(date_str, '%d/%m/%Y')
                return dt.strftime('%Y-%m-%d')
            elif '-' in date_str:
                dt = datetime.strptime(date_str, '%d-%m-%Y')
                return dt.strftime('%Y-%m-%d')
            
            return date_str
        except Exception as e:
            logger.warning(f"Error parsing date {date_str}: {str(e)}")
            return None
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float"""
        if not amount_str:
            return 0.0
        
        try:
            amount_str = amount_str.replace(' ', '')
            
            if ',' in amount_str:
                parts = amount_str.split(',')
                if len(parts[-1]) == 2 and '.' not in amount_str:
                    amount_str = ''.join(parts[:-1]) + '.' + parts[-1]
                else:
                    amount_str = amount_str.replace(',', '')
            
            if '.' in amount_str:
                parts = amount_str.split('.')
                if len(parts) > 2:
                    amount_str = ''.join(parts[:-1]) + '.' + parts[-1]
            
            return float(amount_str)
            
        except Exception as e:
            logger.error(f"Error parsing amount '{amount_str}': {e}")
            return 0.0
    
    def save_bank_transactions(self, transactions: List[Dict], approved_by: int) -> Tuple[bool, str, int]:
        """Save bank transactions to database"""
        try:
            with DatabaseConnection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
                
                saved_count = 0
                errors = []
                
                for idx, trans in enumerate(transactions):
                    try:
                        if not trans.get('tran_id'):
                            errors.append(f"Row {idx+1}: Missing transaction ID")
                            continue
                        
                        if not trans.get('txn_date'):
                            errors.append(f"Row {idx+1}: Missing transaction date")
                            continue
                        
                        cursor.execute("""
                            INSERT INTO bank_transactions 
                            (tran_id, txn_date, cr_dr, amount, balance, description, approved_by, approved_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                            ON CONFLICT (tran_id) DO UPDATE SET
                                txn_date = EXCLUDED.txn_date,
                                cr_dr = EXCLUDED.cr_dr,
                                amount = EXCLUDED.amount,
                                balance = EXCLUDED.balance,
                                description = EXCLUDED.description,
                                approved_by = EXCLUDED.approved_by,
                                approved_at = NOW()
                        """, (
                            trans['tran_id'],
                            trans['txn_date'],
                            trans.get('cr_dr', 'DR'),
                            trans.get('amount', 0.0),
                            trans.get('balance', 0.0),
                            trans.get('description', ''),
                            approved_by
                        ))
                        saved_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error saving transaction {trans.get('tran_id')}: {str(e)}")
                        errors.append(f"Row {idx+1} ({trans.get('tran_id')}): {str(e)}")
                        continue
                
                
                
                message = f"Successfully saved {saved_count} transaction(s)"
                if errors:
                    message += f". {len(errors)} error(s): " + "; ".join(errors[:3])
                
                return True, message, saved_count
                
        except Exception as e:
            logger.error(f"Database error: {str(e)}", exc_info=True)
            return False, f"Database error: {str(e)}", 0
    
    def extract_pos_statement(self, image_bytes: bytes) -> Tuple[bool, str, Optional[Dict]]:
        """Extract POS receipt using table extraction"""
        try:
            df = ocr_service.extract_table_from_image(image_bytes)
            
            if df is None or len(df) == 0:
                return False, "Failed to extract table from image", None
            
            logger.info(f"Extracted table: {df.shape[0]} rows x {df.shape[1]} columns")
            
            transaction = self._parse_pos_from_dataframe(df)
            
            if not transaction or not transaction.get('items'):
                return False, "No valid POS transaction found", None
            
            return True, f"Extracted POS transaction with {len(transaction['items'])} item(s)", transaction
            
        except Exception as e:
            logger.error(f"POS extraction error: {e}", exc_info=True)
            return False, f"Extraction failed: {str(e)}", None
    
    def _parse_pos_from_dataframe(self, df: pd.DataFrame) -> Optional[Dict]:
        """Parse POS receipt from DataFrame"""
        
        receipt_number = None
        transaction_date = None
        pharmacist_name = None
        payment_method = 'cash'
        subtotal = 0.0
        cgst = 0.0
        sgst = 0.0
        total_amount = 0.0
        items = []
        
        all_rows = []
        for i, row in df.iterrows():
            row_data = [str(cell).strip() for cell in row.values]
            all_rows.append(row_data)
        
        for i, row in enumerate(all_rows):
            row_text = ' '.join(row).lower()
            
            if 'receipt' in row_text or 'pos-' in row_text:
                for cell in row:
                    receipt_match = re.search(r'POS[-\s]*\d+[-/]?\d*', cell, re.IGNORECASE)
                    if receipt_match:
                        receipt_number = receipt_match.group().replace(' ', '')
            
            if 'date' in row_text and ':' in row_text:
                for cell in row:
                    date_match = re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', cell)
                    if date_match:
                        transaction_date = self._parse_date(date_match.group())
                        break
        
        header_idx = None
        for i, row in enumerate(all_rows):
            row_text = ' '.join(row).lower()
            if 'medicine' in row_text and 'batch' in row_text:
                header_idx = i
                break
        
        if header_idx is None:
            logger.warning("Could not find medicine table header")
            return None
        
        for i in range(header_idx + 1, len(all_rows)):
            row = all_rows[i]
            row_text = ' '.join(row).lower()
            
            if any(kw in row_text for kw in ['subtotal', 'cgst', 'sgst', 'total', 'pharmacist', 'payment', 'thank']):
                if 'pharmacist' in row_text:
                    for cell in row:
                        if 'dr' in cell.lower() or len(cell) > 5:
                            pharmacist_name = re.sub(r'(pharmacist|dr\.?|:)', '', cell, flags=re.IGNORECASE).strip()
                            if pharmacist_name and pharmacist_name.lower() not in ['none', 'pharmacist']:
                                break
                
                if 'payment' in row_text:
                    if 'insurance' in row_text:
                        payment_method = 'insurance'
                    elif 'card' in row_text:
                        payment_method = 'card'
                    elif 'upi' in row_text:
                        payment_method = 'upi'
                
                if 'subtotal' in row_text:
                    for cell in row:
                        if re.match(r'^[\d\.,]+$', cell):
                            subtotal = self._parse_amount(cell)
                            break
                
                if 'cgst' in row_text:
                    for cell in row:
                        if re.match(r'^[\d\.,]+$', cell):
                            cgst = self._parse_amount(cell)
                            break
                
                if 'sgst' in row_text:
                    for cell in row:
                        if re.match(r'^[\d\.,]+$', cell):
                            sgst = self._parse_amount(cell)
                            break
                
                if 'total amount' in row_text:
                    for cell in row:
                        if re.match(r'^[\d\.,]+$', cell):
                            total_amount = self._parse_amount(cell)
                            break
                
                continue
            
            if len(row) >= 5 and row[0] and row[0].lower() not in ['none', 'nan', '']:
                if re.match(r'^[\d\.,]+$', row[0]):
                    continue
                
                medicine_name = row[0]
                batch_number = row[1] if row[1] and row[1].lower() not in ['none', 'nan'] else None
                
                if batch_number and not re.match(r'^[A-Z]{2}\d+$', batch_number, re.IGNORECASE):
                    batch_number = None
                
                quantity = 1
                if row[2] and re.match(r'^[\d\.,]+$', row[2]):
                    try:
                        qty_val = self._parse_amount(row[2])
                        if qty_val < 1000:
                            quantity = int(qty_val)
                    except:
                        pass
                
                unit_price = 0.0
                if row[3] and re.match(r'^[\d\.,]+$', row[3]):
                    try:
                        unit_price = self._parse_amount(row[3])
                    except:
                        pass
                
                total_price = 0.0
                if row[4] and re.match(r'^[\d\.,]+$', row[4]):
                    try:
                        total_price = self._parse_amount(row[4])
                    except:
                        pass
                
                items.append({
                    'medicine_name': medicine_name,
                    'batch_number': batch_number,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_price': total_price
                })
        
        if not receipt_number:
            receipt_number = f"POS-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        if not transaction_date:
            transaction_date = datetime.now().strftime('%Y-%m-%d')
        
        if not subtotal and items:
            subtotal = sum(item['total_price'] for item in items)
        
        if not total_amount:
            total_amount = subtotal + cgst + sgst
        
        logger.info(f"Parsed POS: {len(items)} items, subtotal: {subtotal}, total: {total_amount}")
        
        return {
            'receipt_number': receipt_number,
            'sale_date': transaction_date,
            'pharmacist_name': pharmacist_name,
            'subtotal': subtotal,
            'cgst_amount': cgst,
            'sgst_amount': sgst,
            'total_amount': total_amount,
            'payment_mode': payment_method,
            'items': items
        }
    
    def save_pos_transaction(self, transaction: Dict, approved_by: Optional[int] = None) -> Tuple[bool, str, Optional[int]]:
        """Save POS transaction to database"""
        try:
            with DatabaseConnection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
                
                cursor.execute("""
                    INSERT INTO pos_sales (
                        receipt_number, sale_date, pharmacist_name,
                        subtotal, cgst_amount, sgst_amount, total_amount,
                        payment_mode
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING sale_id
                """, (
                    transaction['receipt_number'],
                    transaction['sale_date'],
                    transaction.get('pharmacist_name'),
                    transaction.get('subtotal', 0.0),
                    transaction.get('cgst_amount', 0.0),
                    transaction.get('sgst_amount', 0.0),
                    transaction['total_amount'],
                    transaction.get('payment_mode', 'cash')
                ))
                
                sale_id = cursor.fetchone()[0]
                
                for item in transaction.get('items', []):
                    cursor.execute("""
                        INSERT INTO pos_sale_items (
                            sale_id, medicine_name, batch_number,
                            quantity, unit_price, total_price
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        sale_id,
                        item['medicine_name'],
                        item.get('batch_number'),
                        item['quantity'],
                        item['unit_price'],
                        item['total_price']
                    ))
                
                return True, f"Successfully saved POS transaction (Receipt: {transaction['receipt_number']})", sale_id
                
        except Exception as e:
            logger.error(f"Error saving POS transaction: {e}", exc_info=True)
            return False, f"Failed to save: {str(e)}", None


    
    def extract_supplier_invoice(self, image_bytes: bytes) -> Tuple[bool, str, Optional[Dict]]:
        """Extract supplier invoice using table extraction"""
        try:
            df = ocr_service.extract_table_from_image(image_bytes)
            
            if df is None or len(df) == 0:
                return False, "Failed to extract table from image", None
            
            logger.info(f"Extracted table: {df.shape[0]} rows x {df.shape[1]} columns")
            
            invoice = self._parse_supplier_from_dataframe(df)
            
            if not invoice or not invoice.get('items'):
                return False, "No valid supplier invoice found", None
            
            return True, f"Extracted supplier invoice with {len(invoice['items'])} item(s)", invoice
            
        except Exception as e:
            logger.error(f"Supplier invoice extraction error: {e}", exc_info=True)
            return False, f"Extraction failed: {str(e)}", None
    
    def _parse_supplier_from_dataframe(self, df: pd.DataFrame) -> Optional[Dict]:
        """Parse supplier invoice from DataFrame"""
        
        invoice_number = None
        invoice_date = None
        supplier_name = None
        supplier_gstin = None
        po_reference = None
        delivery_date = None
        vehicle_number = None
        subtotal = 0.0
        cgst = 0.0
        sgst = 0.0
        total_amount = 0.0
        items = []
        
        all_rows = []
        for i, row in df.iterrows():
            row_data = [str(cell).strip() for cell in row.values]
            all_rows.append(row_data)
        
        for i, row in enumerate(all_rows):
            row_text = ' '.join(row).lower()
            
            if 'pharmasupply' in row_text or ('pvt' in row_text and 'ltd' in row_text):
                supplier_name = ' '.join(row)
            
            for cell in row:
                if not supplier_gstin:
                    gstin_match = re.search(r'\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d[Z]{1}[A-Z\d]{1}', cell)
                    if gstin_match:
                        supplier_gstin = gstin_match.group()
            
            if 'invoice no' in row_text or 'inv' in row_text:
                for cell in row:
                    inv_match = re.search(r'INV[-\s:]*\d+[-/]?\d*', cell, re.IGNORECASE)
                    if inv_match:
                        invoice_number = inv_match.group().replace(' ', '')
                        break
            
            if 'date' in row_text and not invoice_date:
                for cell in row:
                    date_match = re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', cell)
                    if date_match:
                        invoice_date = self._parse_date(date_match.group())
                        break
            
            if 'po ref' in row_text:
                for cell in row:
                    po_match = re.search(r'PO[-\s:]*([A-Z0-9\-]+)', cell, re.IGNORECASE)
                    if po_match:
                        po_reference = po_match.group(1)
            
            if 'delivery' in row_text and not delivery_date:
                for cell in row:
                    date_match = re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', cell)
                    if date_match:
                        delivery_date = self._parse_date(date_match.group())
                        break
            
            if 'vehicle' in row_text:
                for cell in row:
                    vehicle_match = re.search(r'[A-Z]{2}\d{1,2}[A-Z]{1,2}\d{4}', cell)
                    if vehicle_match:
                        vehicle_number = vehicle_match.group()
        
        header_idx = None
        for i, row in enumerate(all_rows):
            row_text = ' '.join(row).lower()
            if 'medicine name' in row_text and 'batch' in row_text:
                header_idx = i
                break
        
        if header_idx is None:
            logger.warning("Could not find medicine table header")
            return None
        
        for i in range(header_idx + 1, len(all_rows)):
            row = all_rows[i]
            row_text = ' '.join(row).lower()
            
            # STOP at footer keywords and extract totals
            if any(kw in row_text for kw in ['subtotal', 'cgst', 'sgst', 'total', 'terms', 'payment', 'authorized', 'delivery date', 'vehicle']):
                if 'subtotal' in row_text:
                    for cell in row:
                        if re.match(r'^[\d\.,]+$', cell):
                            subtotal = self._parse_amount(cell)
                            break
                
                if 'cgst' in row_text:
                    for cell in row:
                        if re.match(r'^[\d\.,]+$', cell):
                            cgst = self._parse_amount(cell)
                            break
                
                if 'sgst' in row_text:
                    for cell in row:
                        if re.match(r'^[\d\.,]+$', cell):
                            sgst = self._parse_amount(cell)
                            break
                
                if 'total amount' in row_text:
                    for cell in row:
                        if re.match(r'^[\d\.,]+$', cell):
                            total_amount = self._parse_amount(cell)
                            break
                
                continue  # Don't parse footer as items
            
            if len(row) >= 7 and row[0] and row[0].lower() not in ['none', 'nan', '']:
                if re.match(r'^[\d\.,]+$', row[0]):
                    continue
                
                medicine_name = row[0]
                batch_number = row[1] if row[1] and row[1].lower() not in ['none', 'nan'] else None
                
                if batch_number and not re.match(r'^[A-Z]{2}\d+$', batch_number, re.IGNORECASE):
                    batch_number = None
                
                manufacturer = row[2] if row[2] and row[2].lower() not in ['none', 'nan'] else None
                
                expiry_date = None
                if row[3]:
                    expiry_match = re.search(r'\d{2}/\d{4}', row[3])
                    if expiry_match:
                        try:
                            expiry_date = datetime.strptime(expiry_match.group(), '%m/%Y').strftime('%Y-%m-%d')
                        except:
                            pass
                
                quantity = 1
                if len(row) > 4 and row[4] and re.match(r'^[\d\.,]+$', row[4]):
                    try:
                        qty_val = self._parse_amount(row[4])
                        if qty_val < 10000:
                            quantity = int(qty_val)
                    except:
                        pass
                
                unit_price = 0.0
                if len(row) > 5 and row[5] and re.match(r'^[\d\.,]+$', row[5]):
                    try:
                        unit_price = self._parse_amount(row[5])
                    except:
                        pass
                
                total_price = 0.0
                if len(row) > 6 and row[6] and re.match(r'^[\d\.,]+$', row[6]):
                    try:
                        total_price = self._parse_amount(row[6])
                    except:
                        pass
                
                items.append({
                    'medicine_name': medicine_name,
                    'batch_number': batch_number,
                    'manufacturer': manufacturer,
                    'expiry_date': expiry_date,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_price': total_price
                })
        
        if not invoice_number:
            invoice_number = f"INV-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        if not invoice_date:
            invoice_date = datetime.now().strftime('%Y-%m-%d')
        
        if not subtotal and items:
            subtotal = sum(item['total_price'] for item in items)
        
        if not total_amount:
            total_amount = subtotal + cgst + sgst
        
        logger.info(f"Parsed supplier invoice: {len(items)} items, subtotal: {subtotal}, total: {total_amount}")
        
        return {
            'invoice_number': invoice_number,
            'invoice_date': invoice_date,
            'supplier_name': supplier_name or 'Unknown Supplier',
            'supplier_gstin': supplier_gstin,
            'po_reference': po_reference,
            'delivery_date': delivery_date,
            'vehicle_number': vehicle_number,
            'subtotal': subtotal,
            'cgst_amount': cgst,
            'sgst_amount': sgst,
            'total_amount': total_amount,
            'items': items
        }

    
    def save_supplier_invoice(self, invoice: Dict, approved_by: Optional[int] = None) -> Tuple[bool, str, Optional[int]]:
        """Save supplier invoice to database"""
        try:
            with DatabaseConnection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
                
                cursor.execute("""
                    INSERT INTO supplier_invoices (
                        invoice_number, invoice_date, supplier_name, supplier_gstin,
                        po_reference, delivery_date, vehicle_number,
                        subtotal, cgst_amount, sgst_amount, total_amount
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING invoice_id
                """, (
                    invoice['invoice_number'],
                    invoice['invoice_date'],
                    invoice['supplier_name'],
                    invoice.get('supplier_gstin'),
                    invoice.get('po_reference'),
                    invoice.get('delivery_date'),
                    invoice.get('vehicle_number'),
                    invoice.get('subtotal', 0.0),
                    invoice.get('cgst_amount', 0.0),
                    invoice.get('sgst_amount', 0.0),
                    invoice['total_amount']
                ))
                
                invoice_id = cursor.fetchone()[0]
                
                for item in invoice.get('items', []):
                    cursor.execute("""
                        INSERT INTO supplier_invoice_items (
                            invoice_id, medicine_name, batch_number, manufacturer,
                            expiry_date, quantity, unit_price, total_price
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        invoice_id,
                        item['medicine_name'],
                        item.get('batch_number'),
                        item.get('manufacturer'),
                        item.get('expiry_date'),
                        item['quantity'],
                        item['unit_price'],
                        item['total_price']
                    ))
                
                
                
                return True, f"Successfully saved supplier invoice (Invoice: {invoice['invoice_number']})", invoice_id
                
        except Exception as e:
            logger.error(f"Error saving supplier invoice: {e}", exc_info=True)
            return False, f"Failed to save: {str(e)}", None


# Global instance
finance_service = FinanceService()
