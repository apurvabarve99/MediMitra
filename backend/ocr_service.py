import logging
import os
from PIL import Image
import pandas as pd
from surya.foundation import FoundationPredictor
from surya.recognition import RecognitionPredictor
from surya.detection import DetectionPredictor
from typing import Optional, List, Union
import io
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)8s] %(filename)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

class OCRService:
    """Service for extracting text from images using SuryaOCR"""
    
    def __init__(self):
        """Initialize SuryaOCR predictors"""
        try:
            # Set low-memory mode for 4GB RAM
            os.environ['RECOGNITION_BATCH_SIZE'] = '8'
            os.environ['DETECTOR_BATCH_SIZE'] = '1'
            
            logger.info("Initializing SuryaOCR predictors...")
            
            # Initialize predictors (latest API)
            self.foundation_predictor = FoundationPredictor()
            self.recognition_predictor = RecognitionPredictor(self.foundation_predictor)
            self.detection_predictor = DetectionPredictor()
            
            self._ready = True
            logger.info("✅ SuryaOCR initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize SuryaOCR: {e}")
            self._ready = False
            raise
    
    def is_ready(self) -> bool:
        """Check if OCR service is ready"""
        return self._ready
    
    def extract_text_from_image(self, image_file) -> Optional[str]:
        """
        Extract text from an image using SuryaOCR
        
        Args:
            image_file: Image file (bytes, file-like object, path, or PIL Image)
        
        Returns:
            Extracted text as string, or None if extraction fails
        """
        try:
            logger.info("Starting SuryaOCR text extraction...")
            
            # Load and convert image
            if isinstance(image_file, bytes):
                image = Image.open(io.BytesIO(image_file))
            elif isinstance(image_file, str):
                image = Image.open(image_file)
            elif hasattr(image_file, 'read'):
                image = Image.open(image_file)
            else:
                image = image_file
            
            # Convert RGBA to RGB if necessary
            if image.mode == 'RGBA':
                logger.info("Converting image from RGBA to RGB")
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            logger.info(f"Image size: {image.size}, mode: {image.mode}")
            
            # Run OCR using latest API
            predictions = self.recognition_predictor([image], det_predictor=self.detection_predictor)
            
            # Extract text from predictions
            if not predictions or len(predictions) == 0:
                logger.warning("No text detected in image")
                return None
            
            # Get the first prediction (for single image)
            prediction = predictions[0]
            
            # Combine all text lines
            text_lines = []
            for text_line in prediction.text_lines:
                text_lines.append(text_line.text)
            
            extracted_text = '\n'.join(text_lines)
            
            logger.info(f"✅ Successfully extracted {len(text_lines)} text lines")
            logger.info(f"Preview: {extracted_text[:200]}...")
            
            return extracted_text.strip()
            
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
            logger.error(f"Traceback: ", exc_info=True)
            return None
    
    def extract_with_layout(self, image_file) -> Optional[dict]:
        """
        Extract text with layout information (bounding boxes, confidence)
        
        Returns:
            Dictionary with structured OCR results
        """
        try:
            # Load image
            if isinstance(image_file, bytes):
                image = Image.open(io.BytesIO(image_file))
            elif isinstance(image_file, str):
                image = Image.open(image_file)
            elif hasattr(image_file, 'read'):
                image = Image.open(image_file)
            else:
                image = image_file
            
            # Convert to RGB
            if image.mode != 'RGB':
                if image.mode == 'RGBA':
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[3])
                    image = background
                else:
                    image = image.convert('RGB')
            
            # Run OCR
            predictions = self.recognition_predictor([image], det_predictor=self.detection_predictor)
            
            if not predictions:
                return None
            
            prediction = predictions[0]
            
            # Structure the results
            result = {
                'text_lines': [],
                'full_text': ''
            }
            
            text_parts = []
            for text_line in prediction.text_lines:
                line_data = {
                    'text': text_line.text,
                    'confidence': text_line.confidence,
                    'bbox': text_line.bbox
                }
                result['text_lines'].append(line_data)
                text_parts.append(text_line.text)
            
            result['full_text'] = '\n'.join(text_parts)
            
            return result
            
        except Exception as e:
            logger.error(f"Layout extraction error: {e}")
            return None
    
    def extract_table_from_image(self, image_bytes: bytes) -> Optional[pd.DataFrame]:
        """Extract table data row-by-row using bounding boxes"""
        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB
            if image.mode != 'RGB':
                if image.mode == 'RGBA':
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[3])
                    image = background
                else:
                    image = image.convert('RGB')
            
            # Run OCR using existing predictor
            predictions = self.recognition_predictor([image], det_predictor=self.detection_predictor)
            
            if not predictions or len(predictions) == 0:
                return None
            
            prediction = predictions[0]
            
            # Group lines by rows using Y-coordinates
            rows = self._group_lines_into_rows(prediction.text_lines)
            
            # Convert to table data
            table_data = self._process_rows_to_table(rows)
            
            # Create DataFrame
            df = pd.DataFrame(table_data)
            
            logger.info(f"Extracted table with {len(df)} rows and {len(df.columns)} columns")
            return df
            
        except Exception as e:
            logger.error(f"Table extraction error: {e}", exc_info=True)
            return None
    
    def _group_lines_into_rows(self, lines, y_threshold=10):
        """Groups OCR lines into rows based on vertical proximity"""
        if not lines:
            return []
        
        # Sort lines by their top Y-coordinate
        lines.sort(key=lambda line: line.bbox[1])
        
        rows = []
        current_row = []
        for line in lines:
            if not current_row:
                current_row.append(line)
            else:
                # Check if current line is close to previous line in row
                if abs(line.bbox[1] - current_row[-1].bbox[1]) < y_threshold:
                    current_row.append(line)
                else:
                    rows.append(current_row)
                    current_row = [line]
        if current_row:
            rows.append(current_row)
        return rows
    
    def _process_rows_to_table(self, rows):
        """Sorts lines within each row by X-coordinate and extracts text"""
        table_data = []
        for row in rows:
            # Sort lines in row by left X-coordinate
            row.sort(key=lambda line: line.bbox[0])
            # Extract text in order
            text_row = [line.text for line in row]
            table_data.append(text_row)
        return table_data
    
    def extract_prescription_items(self, text: str) -> List[str]:
        """
        Extract medicine items from prescription text
        
        Args:
            text: Extracted text from prescription
        
        Returns:
            List of medicine strings (simple format for LLM)
        """
        try:
            if not text:
                return []
            
            lines = text.split('\n')
            medicines = []
            
            # Patterns to identify medicines and dosages
            dosage_pattern = r'\d+\s*(mg|ml|g|tablet|cap|capsule|syrup|injection|drops)'
            frequency_pattern = r'(\d+\s*times?|\d+x|once|twice|thrice|morning|evening|night|daily|weekly|BD|TDS|QID|OD)'
            
            # Look for "Medicines" section
            in_medicine_section = False
            
            for line in lines:
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                
                # Check if we're entering medicine section
                if re.search(r'(medicines?|prescription|drugs?|medications?)', line_stripped, re.IGNORECASE):
                    in_medicine_section = True
                    continue
                
                # Skip headers and common non-medicine lines
                if re.search(r'^(date|address|ph\s*no|symptoms|lab\s*tests?|tests?|patient)', line_stripped, re.IGNORECASE):
                    continue
                
                # Check if line contains dosage information (likely a medicine)
                if re.search(dosage_pattern, line_stripped, re.IGNORECASE):
                    medicines.append(line_stripped)
                    continue
                
                # If in medicine section and line has reasonable length, might be medicine
                if in_medicine_section and 3 < len(line_stripped) < 100:
                    # Check if it's not a common non-medicine keyword
                    if not re.search(r'^(test|result|advice|follow|consult)', line_stripped, re.IGNORECASE):
                        medicines.append(line_stripped)
            
            logger.info(f"Extracted {len(medicines)} medicine items")
            return medicines
            
        except Exception as e:
            logger.error(f"Error extracting prescription items: {e}")
            return []
    
    def extract_prescription_items_detailed(self, text: str) -> List[dict]:
        """
        Extract medicine items with detailed parsing (for advanced use)
        
        Args:
            text: Extracted text from prescription
        
        Returns:
            List of medicine dictionaries with name, dosage, frequency
        """
        try:
            if not text:
                return []
            
            lines = text.split('\n')
            medicines = []
            
            # Patterns to identify medicines and dosages
            dosage_pattern = r'\d+\s*(mg|ml|g|tablet|cap|capsule|syrup|injection|drops)'
            frequency_pattern = r'(\d+\s*times?|\d+x|once|twice|thrice|morning|evening|night|daily|weekly|BD|TDS|QID|OD)'
            
            in_medicine_section = False
            
            for line in lines:
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                
                # Check if we're entering medicine section
                if re.search(r'(medicines?|prescription|drugs?)', line_stripped, re.IGNORECASE):
                    in_medicine_section = True
                    continue
                
                # Skip headers
                if re.search(r'^(date|address|ph\s*no|symptoms|lab\s*tests?)', line_stripped, re.IGNORECASE):
                    continue
                
                # Check if line contains dosage information (likely a medicine)
                if re.search(dosage_pattern, line_stripped, re.IGNORECASE):
                    medicine = {
                        'raw_text': line_stripped,
                        'name': '',
                        'dosage': '',
                        'frequency': ''
                    }
                    
                    # Extract dosage
                    dosage_match = re.search(dosage_pattern, line_stripped, re.IGNORECASE)
                    if dosage_match:
                        medicine['dosage'] = dosage_match.group()
                    
                    # Extract frequency
                    freq_match = re.search(frequency_pattern, line_stripped, re.IGNORECASE)
                    if freq_match:
                        medicine['frequency'] = freq_match.group()
                    
                    # Medicine name is typically at the start
                    # Remove dosage and frequency to get name
                    name = line_stripped
                    if dosage_match:
                        name = name.replace(dosage_match.group(), '')
                    if freq_match:
                        name = name.replace(freq_match.group(), '')
                    
                    medicine['name'] = name.strip()
                    
                    medicines.append(medicine)
            
            logger.info(f"Extracted {len(medicines)} detailed medicine items")
            return medicines
            
        except Exception as e:
            logger.error(f"Error extracting detailed prescription items: {e}")
            return []

# Global instance
ocr_service = OCRService()
