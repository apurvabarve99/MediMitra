import os
import random
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

def create_supplier_invoice(invoice_num, output_filename):
    """Generate a realistic supplier invoice"""

    width, height = 700, 950
    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font_header = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
        font_normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)
    except:
        font_header = font_title = font_normal = font_small = ImageFont.load_default()

    # Random date in last 30 days
    base_date = datetime(2026, 1, 25)
    random_days = random.randint(0, 30)
    invoice_date = base_date - timedelta(days=random_days)
    delivery_date = invoice_date + timedelta(days=1)

    # Random supplier
    suppliers = [
        ("PharmaSupply Co. Ltd.", "Bangalore", "29AABCP1234F1Z5", "080-12345678"),
        ("MediDistributors Pvt Ltd", "Mumbai", "27AABCD5678G1Z9", "022-87654321"),
        ("HealthCare Traders", "Chennai", "33AABCH9012H1Z3", "044-23456789"),
        ("LifeLine Pharma Dist.", "Hyderabad", "36AABCL3456I1Z7", "040-34567890"),
    ]

    supplier = random.choice(suppliers)

    y = 30

    # Company header with colored background
    draw.rectangle([0, 0, width, 80], fill=(41, 128, 185))
    draw.text((width//2 - 100, 15), supplier[0], fill=(255, 255, 255), font=font_header)
    draw.text((width//2 - 130, 45), "Wholesale Pharmaceutical Distributor", fill=(255, 255, 255), font=font_normal)

    y = 100

    # Company details
    draw.text((30, y), supplier[0], fill=(0, 0, 0), font=font_title)
    y += 15
    draw.text((30, y), f"Medical Plaza, {supplier[1]}", fill=(0, 0, 0), font=font_small)
    y += 12
    draw.text((30, y), "Karnataka 560001" if "Bangalore" in supplier[1] else "India", fill=(0, 0, 0), font=font_small)
    y += 12
    draw.text((30, y), f"GSTIN: {supplier[2]}", fill=(0, 0, 0), font=font_small)
    y += 12
    draw.text((30, y), f"Ph: {supplier[3]}", fill=(0, 0, 0), font=font_small)

    # Invoice details box
    y = 100
    draw.rectangle([450, y, 670, y+80], outline=(41, 128, 185), width=2)
    draw.text((460, y+5), "INVOICE", fill=(41, 128, 185), font=font_header)
    y += 30
    draw.text((460, y), f"Invoice No: INV-2026-{invoice_num:04d}", fill=(0, 0, 0), font=font_normal)
    y += 15
    draw.text((460, y), f"Date: {invoice_date.strftime('%d/%m/%Y')}", fill=(0, 0, 0), font=font_normal)
    y += 15
    draw.text((460, y), f"PO Ref: PO-2026-{random.randint(1000, 2000)}", fill=(0, 0, 0), font=font_normal)

    y = 200

    # Bill to
    draw.text((30, y), "BILL TO:", fill=(0, 0, 0), font=font_title)
    y += 18
    draw.text((30, y), "MediCare Pharmacy", fill=(0, 0, 0), font=font_normal)
    y += 15
    draw.text((30, y), "123 Hospital Road, Mangaluru", fill=(0, 0, 0), font=font_small)
    y += 12
    draw.text((30, y), "Karnataka 575001", fill=(0, 0, 0), font=font_small)
    y += 12
    draw.text((30, y), "GSTIN: 29AABCM5678K1Z9", fill=(0, 0, 0), font=font_small)

    y = 290
    draw.line([(30, y), (670, y)], fill=(0, 0, 0), width=2)
    y += 15

    # Table header
    draw.rectangle([30, y, 670, y+30], fill=(230, 230, 230))
    draw.text((35, y+8), "Medicine Name", fill=(0, 0, 0), font=font_title)
    draw.text((250, y+8), "Batch", fill=(0, 0, 0), font=font_title)
    draw.text((330, y+8), "Mfg", fill=(0, 0, 0), font=font_title)
    draw.text((400, y+8), "Expiry", fill=(0, 0, 0), font=font_title)
    draw.text((480, y+8), "Qty", fill=(0, 0, 0), font=font_title)
    draw.text((540, y+8), "Rate", fill=(0, 0, 0), font=font_title)
    draw.text((610, y+8), "Amount", fill=(0, 0, 0), font=font_title)
    y += 30

    # Medicine pool
    medicines = [
        ("Paracetamol 500mg Tab", "Cipla", 2.00),
        ("Amoxicillin 250mg Cap", "SunPharma", 7.50),
        ("Cetirizine 10mg Tab", "Dr.Reddy", 1.20),
        ("Ibuprofen 400mg Tab", "Lupin", 3.00),
        ("Azithromycin 500mg", "Cipla", 10.50),
        ("Metformin 500mg Tab", "USV", 1.80),
        ("Omeprazole 20mg Cap", "Torrent", 4.50),
        ("Ciprofloxacin 500mg", "Ranbaxy", 6.00),
        ("Atorvastatin 10mg", "Cipla", 4.80),
        ("Amlodipine 5mg Tab", "Lupin", 2.00),
        ("Pantoprazole 40mg", "Alkem", 5.50),
        ("Losartan 50mg Tab", "Dr.Reddy", 3.20),
    ]

    # Random 5-8 items
    num_items = random.randint(5, 8)
    selected_medicines = random.sample(medicines, num_items)

    items = []
    subtotal = 0

    for med_name, mfg, rate in selected_medicines:
        qty = random.randint(200, 2000)
        batch = f"BT{random.randint(240101, 240999)}"

        # Expiry 6-24 months from now
        expiry_months = random.randint(6, 24)
        expiry = datetime.now() + timedelta(days=expiry_months*30)

        amount = qty * rate
        subtotal += amount

        items.append((
            med_name, batch, mfg, 
            expiry.strftime('%m/%Y'),
            str(qty), f"{rate:.2f}", f"{amount:.2f}"
        ))

    for item in items:
        draw.rectangle([30, y, 670, y+25], outline=(200, 200, 200), width=1)
        draw.text((35, y+5), item[0], fill=(0, 0, 0), font=font_small)
        draw.text((250, y+5), item[1], fill=(0, 0, 0), font=font_small)
        draw.text((330, y+5), item[2], fill=(0, 0, 0), font=font_small)
        draw.text((400, y+5), item[3], fill=(0, 0, 0), font=font_small)
        draw.text((480, y+5), item[4], fill=(0, 0, 0), font=font_small)
        draw.text((540, y+5), item[5], fill=(0, 0, 0), font=font_small)
        draw.text((600, y+5), item[6], fill=(0, 0, 0), font=font_small)
        y += 25

    y += 10
    draw.line([(30, y), (670, y)], fill=(0, 0, 0), width=2)
    y += 15

    # Totals section
    cgst = subtotal * 0.06
    sgst = subtotal * 0.06
    total = subtotal + cgst + sgst

    draw.text((450, y), "Subtotal:", fill=(0, 0, 0), font=font_normal)
    draw.text((590, y), f"{subtotal:,.2f}", fill=(0, 0, 0), font=font_normal)
    y += 18
    draw.text((450, y), "CGST @ 6%:", fill=(0, 0, 0), font=font_small)
    draw.text((590, y), f"{cgst:,.2f}", fill=(0, 0, 0), font=font_small)
    y += 15
    draw.text((450, y), "SGST @ 6%:", fill=(0, 0, 0), font=font_small)
    draw.text((590, y), f"{sgst:,.2f}", fill=(0, 0, 0), font=font_small)
    y += 15
    draw.line([(450, y), (670, y)], fill=(0, 0, 0), width=2)
    y += 15
    draw.text((450, y), "Total Amount:", fill=(0, 0, 0), font=font_title)
    draw.text((590, y), f"₹{total:,.2f}", fill=(0, 0, 0), font=font_title)
    y += 25
    draw.line([(30, y), (670, y)], fill=(0, 0, 0), width=1)
    y += 15

    # Footer
    payment_terms = ["Net 30 days", "Net 15 days", "Net 45 days", "Advance Payment"]
    vehicles = ["KA-19-MN-1234", "MH-01-AB-5678", "TN-09-CD-9012", "TS-07-EF-3456"]

    draw.text((30, y), f"Payment Terms: {random.choice(payment_terms)}", fill=(0, 0, 0), font=font_small)
    y += 15
    draw.text((30, y), f"Delivery Date: {delivery_date.strftime('%d/%m/%Y')}", fill=(0, 0, 0), font=font_small)
    y += 15
    draw.text((30, y), f"Vehicle No: {random.choice(vehicles)}", fill=(0, 0, 0), font=font_small)
    y += 25
    draw.text((450, y), "Authorized Signature", fill=(0, 0, 0), font=font_small)

    img.save(output_filename)
    print(f"✅ Created: {output_filename}")
    return img


if __name__ == "__main__":
    os.makedirs('synthetic_data', exist_ok=True)

    for i in range(1, 11):
        invoice_num = 5670 + i
        output_file = f'synthetic_data/supplier_invoice_{i:02d}.png'
        create_supplier_invoice(invoice_num, output_file)

    print("\n✅ Successfully generated 10 supplier invoices!")
