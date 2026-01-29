import qrcode
from io import BytesIO
from PIL import Image
import base64

def generate_qr_code(data: str, size: int = 300) -> str:
    """
    Generate QR code and return as base64 encoded string
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Resize
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    
    # Convert to base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"
