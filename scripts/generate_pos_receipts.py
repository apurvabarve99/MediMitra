import os
import random
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

def create_pos_receipt(receipt_num, output_filename):
    """Generate a realistic pharmacy POS receipt"""

    width, height = 400, 650
    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font_header = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        font_normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)
    except:
        font_header = font_normal = font_small = ImageFont.load_default()

    # Random date in last 30 days
    base_date = datetime(2026, 1, 26)
    random_days = random.randint(0, 30)
    sale_date = base_date - timedelta(days=random_days)

    y = 20

    # Header
    draw.text((width//2 - 80, y), "MediCare Pharmacy", fill=(0, 0, 0), font=font_header)
    y += 25
    draw.text((width//2 - 100, y), "123 Hospital Road, Mangaluru", fill=(0, 0, 0), font=font_small)
    y += 15
    draw.text((width//2 - 70, y), "Karnataka 575001", fill=(0, 0, 0), font=font_small)
    y += 15
    draw.text((width//2 - 60, y), "Ph: 0824-2234567", fill=(0, 0, 0), font=font_small)
    y += 20
    draw.line([(20, y), (380, y)], fill=(0, 0, 0), width=2)
    y += 15

    # Receipt details
    draw.text((20, y), f"Receipt No: POS-2026-{receipt_num:06d}", fill=(0, 0, 0), font=font_normal)
    y += 15
    draw.text((20, y), f"Date: {sale_date.strftime('%d/%m/%Y %H:%M')}", fill=(0, 0, 0), font=font_normal)
    y += 20
    draw.line([(20, y), (380, y)], fill=(0, 0, 0), width=1)
    y += 15

    # Column headers
    draw.text((20, y), "Medicine", fill=(0, 0, 0), font=font_normal)
    draw.text((200, y), "Batch", fill=(0, 0, 0), font=font_normal)
    draw.text((260, y), "Qty", fill=(0, 0, 0), font=font_normal)
    draw.text((300, y), "Price", fill=(0, 0, 0), font=font_normal)
    draw.text((350, y), "Amt", fill=(0, 0, 0), font=font_normal)
    y += 15
    draw.line([(20, y), (380, y)], fill=(0, 0, 0), width=1)
    y += 10

    # Medicine pool
    medicines = [
        ("Paracetamol 500mg", 2.50),
        ("Amoxicillin 250mg", 8.00),
        ("Cetirizine 10mg", 1.50),
        ("Ibuprofen 400mg", 3.50),
        ("Azithromycin 500mg", 12.00),
        ("Metformin 500mg", 1.80),
        ("Omeprazole 20mg", 4.50),
        ("Ciprofloxacin 500mg", 6.50),
        ("Atorvastatin 10mg", 5.00),
        ("Amlodipine 5mg", 2.20),
    ]

    # Random 4-7 items
    num_items = random.randint(4, 7)
    selected_medicines = random.sample(medicines, num_items)

    items = []
    subtotal = 0

    for med_name, price in selected_medicines:
        qty = random.randint(5, 25)
        batch = f"BT240{random.randint(10, 99)}"
        amount = qty * price
        subtotal += amount
        items.append((med_name, batch, str(qty), f"{price:.2f}", f"{amount:.2f}"))

    for item in items:
        draw.text((20, y), item[0], fill=(0, 0, 0), font=font_small)
        draw.text((200, y), item[1], fill=(0, 0, 0), font=font_small)
        draw.text((260, y), item[2], fill=(0, 0, 0), font=font_small)
        draw.text((300, y), item[3], fill=(0, 0, 0), font=font_small)
        draw.text((350, y), item[4], fill=(0, 0, 0), font=font_small)
        y += 15

    y += 5
    draw.line([(20, y), (380, y)], fill=(0, 0, 0), width=1)
    y += 15

    # Totals
    cgst = subtotal * 0.06
    sgst = subtotal * 0.06
    total = subtotal + cgst + sgst

    draw.text((240, y), "Subtotal:", fill=(0, 0, 0), font=font_normal)
    draw.text((340, y), f"{subtotal:.2f}", fill=(0, 0, 0), font=font_normal)
    y += 15
    draw.text((240, y), "CGST (6%):", fill=(0, 0, 0), font=font_small)
    draw.text((340, y), f"{cgst:.2f}", fill=(0, 0, 0), font=font_small)
    y += 15
    draw.text((240, y), "SGST (6%):", fill=(0, 0, 0), font=font_small)
    draw.text((340, y), f"{sgst:.2f}", fill=(0, 0, 0), font=font_small)
    y += 15
    draw.line([(240, y), (380, y)], fill=(0, 0, 0), width=2)
    y += 15
    draw.text((240, y), "Total Amount:", fill=(0, 0, 0), font=font_header)
    draw.text((340, y), f"{total:.2f}", fill=(0, 0, 0), font=font_header)
    y += 25
    draw.line([(20, y), (380, y)], fill=(0, 0, 0), width=2)
    y += 15

    # Footer
    pharmacists = ["Dr. Ramesh Kumar", "Dr. Priya Singh", "Dr. Suresh Patel", "Dr. Anita Desai"]
    payment_modes = ["Cash", "Card", "UPI", "Insurance"]

    draw.text((20, y), f"Pharmacist: {random.choice(pharmacists)}", fill=(0, 0, 0), font=font_small)
    y += 15
    draw.text((20, y), f"Payment Mode: {random.choice(payment_modes)}", fill=(0, 0, 0), font=font_small)
    y += 20
    draw.text((width//2 - 80, y), "Thank you for your purchase!", fill=(0, 0, 0), font=font_normal)

    img.save(output_filename)
    print(f"✅ Created: {output_filename}")
    return img


if __name__ == "__main__":
    os.makedirs('synthetic_data', exist_ok=True)

    for i in range(1, 11):
        receipt_num = 1230 + i
        output_file = f'synthetic_data/pos_receipt_{i:02d}.png'
        create_pos_receipt(receipt_num, output_file)

    print("\n✅ Successfully generated 10 POS receipts!")
