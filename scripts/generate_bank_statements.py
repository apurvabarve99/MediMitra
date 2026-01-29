import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import random
import os


def generate_synthetic_bank_statement(num_transactions=15, output_filename='bank_statement.png'):
    """
    Creates a synthetic bank statement image
    Columns: Tran Id, Txn Date, Cr/Dr, Amount, Balance, Description
    """
    # Optimized dimensions for OCR speed
    width = 550
    row_height = 35
    header_height = 30
    margin = 10
    
    height = 60 + header_height + (num_transactions * row_height)
    bg_color = (255, 255, 255)
    
    # Create image
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    try:
        font_header = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 7)
    except:
        font_header = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Colors
    header_bg = (255, 204, 153)
    border_color = (0, 0, 0)
    
    # Table dimensions
    table_start_y = 50
    table_width = width - (2 * margin)
    table_end_x = width - margin
    
    # Column headers
    headers = ["Tran Id", "Txn Date", "Cr/Dr", "Amount", "Balance", "Description"]
    
    # Column positions (proportional to 550px width)
    col_positions = [15, 80, 145, 195, 260, 340]
    
    # Draw header row
    draw.rectangle(
        [margin, table_start_y, table_end_x, table_start_y + header_height],
        fill=header_bg, 
        outline=border_color, 
        width=2
    )
    
    # Draw column headers
    for i, header in enumerate(headers):
        draw.text(
            (col_positions[i], table_start_y + 8), 
            header,
            fill=border_color, 
            font=font_header
        )
    
    # Generate transaction data
    transactions = generate_transaction_data(num_transactions)
    
    # Draw transactions
    y_pos = table_start_y + header_height
    
    for idx, txn in transactions.iterrows():
        # Alternating row colors
        row_color = (255, 255, 240) if idx % 2 == 0 else (255, 255, 255)
        draw.rectangle(
            [margin, y_pos, table_end_x, y_pos + row_height],
            fill=row_color, 
            outline=border_color, 
            width=1
        )
        
        # Draw cell data
        draw.text((col_positions[0], y_pos + 8), str(txn['tran_id']), 
                 fill=border_color, font=font_small)
        draw.text((col_positions[1], y_pos + 8), txn['txn_date'], 
                 fill=border_color, font=font_small)
        draw.text((col_positions[2], y_pos + 8), txn['cr_dr'], 
                 fill=border_color, font=font_small)
        draw.text((col_positions[3], y_pos + 8), f"{txn['amount']:,.2f}", 
                 fill=border_color, font=font_small)
        draw.text((col_positions[4], y_pos + 8), f"{txn['balance']:,.2f}", 
                 fill=border_color, font=font_small)
        
        # Description - truncate if too long
        description = txn['description']
        max_desc_length = 28  # Characters that fit in column
        
        if len(description) > max_desc_length:
            description = description[:max_desc_length-2] + '..'
        
        # Draw description (single line, truncated)
        draw.text((col_positions[5], y_pos + 8), description, 
                 fill=border_color, font=font_small)
        
        y_pos += row_height
    
    # Calculate table end
    table_end_y = y_pos
    
    # Draw vertical lines between columns
    for i in range(1, len(col_positions)):
        x = col_positions[i] - 5
        draw.line([(x, table_start_y), (x, table_end_y)], 
                 fill=border_color, width=1)
    
    # Draw outer border
    draw.rectangle(
        [margin, table_start_y, table_end_x, table_end_y],
        outline=border_color, 
        width=2
    )
    
    # Crop to remove extra whitespace
    final_height = table_end_y + 20
    img = img.crop((0, 0, width, final_height))
    
    # Save image
    img.save(output_filename, 'PNG', dpi=(300, 300))
    print(f"✅ Generated: {output_filename}")
    return img


def generate_transaction_data(num_transactions):
    """Generate realistic transaction data with guaranteed positive balance"""
    
    descriptions = [
        "PEN. MAR-17 LESS TDS-0",
        "PEN. APR-17 LESS TDS-0",
        "NEFT-PREMLAL PANDEY",
        "NEFT-RAJESH KUMAR",
        "NEFT-AMIT SINGH",
        "SALARY CREDIT - MONTHLY",
        "ELECTRICITY BILL PAYMENT",
        "WATER BILL - MUNICIPAL",
        "UPI-PHONEPE-GROCERY",
        "UPI-GPAY-RESTAURANT",
        "ATM WITHDRAWAL - BRANCH 1234",
        "MEDICINE PURCHASE - APOLLO",
        "INSURANCE PREMIUM",
    ]
    
    # IMPSAR/IMPSAB templates
    impsar_template = "IMPSAR/{}/SBI/N0011666/35553540356"
    impsab_template = "IMPSAB/{}/UBI/N{}"
    numeric_long_template = "421368449810326{}/008719/34980203003234{}"
    
    data = []
    
    # Starting balance: 1.5L to 2.5L
    balance = random.uniform(150000, 250000)
    
    # Starting date
    start_date = datetime(2017, 4, 2)
    current_date = start_date
    
    for i in range(num_transactions):
        tran_id = f"S{9703097 + i}"
        
        # Increment date by 1-5 days
        current_date = current_date + timedelta(days=random.randint(1, 5))
        txn_date = current_date.strftime('%d/%m/%Y')
        
        # Random description type
        desc_type = random.choice(['simple', 'impsar', 'impsab', 'numeric'])
        
        if desc_type == 'simple':
            description = random.choice(descriptions)
        elif desc_type == 'impsar':
            description = impsar_template.format(random.randint(709590607490, 713198281063))
        elif desc_type == 'impsab':
            description = impsab_template.format(
                random.randint(716809103870, 716909208750),
                random.randint(534986922223422, 534986999999999)
            )
        else:
            description = numeric_long_template.format(
                random.randint(4713160, 4713199),
                random.randint(40, 49)
            )
        
        # Smart Cr/Dr to maintain positive balance
        if balance < 50000:
            cr_dr = random.choice(['CR', 'CR', 'CR', 'DR'])
        elif balance < 100000:
            cr_dr = random.choice(['CR', 'CR', 'DR', 'DR'])
        else:
            cr_dr = random.choice(['DR', 'DR', 'DR', 'CR'])
        
        # Amount calculation
        if cr_dr == 'DR':
            max_debit = min(balance * 0.3, 50000)
            amount = round(random.uniform(1000, max_debit), 2)
        else:
            amount = round(random.choice([5000, 10000, 25000, 50000, 
                                         random.uniform(5000, 60000)]), 2)
        
        # Update balance
        if cr_dr == 'DR':
            balance -= amount
        else:
            balance += amount
        
        # Safety check
        if balance < 0:
            emergency_credit = abs(balance) + random.uniform(50000, 100000)
            balance += emergency_credit
            data.append({
                'tran_id': f"S{9703097 + i}A",
                'txn_date': txn_date,
                'cr_dr': 'CR',
                'amount': round(emergency_credit, 2),
                'balance': round(balance, 2),
                'description': 'EMERGENCY FUND TRANSFER'
            })
        
        data.append({
            'tran_id': tran_id,
            'txn_date': txn_date,
            'cr_dr': cr_dr,
            'amount': amount,
            'balance': round(balance, 2),
            'description': description
        })
    
    return pd.DataFrame(data)


# Generate sample bank statement images
if __name__ == "__main__":
    os.makedirs('synthetic_data', exist_ok=True)
    
    for i in range(10):
        num_txns = random.randint(12, 18)
        output_file = f'synthetic_data/bank_statement_{i+1:02d}.png'
        generate_synthetic_bank_statement(num_transactions=num_txns, output_filename=output_file)
    
    print("\n✅ Successfully generated 10 synthetic bank statements!")
    print("✅ All balances are guaranteed to be POSITIVE!")
