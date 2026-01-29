import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db_connection import DatabaseConnection
from backend.rag_service import rag_service
import json


# Test Preparation Instructions
TEST_PREPARATIONS = [
    {
        "test_name": "Complete Blood Count (CBC)",
        "content": "No special preparation needed. You can eat and drink normally before the test. Wear comfortable clothing with sleeves that can be easily rolled up.",
        "fasting": "No",
        "water": "Normal intake allowed",
        "medications": "Continue all medications as prescribed",
        "requirements": "Valid ID and doctor's prescription"
    },
    {
        "test_name": "Fasting Blood Sugar (FBS)",
        "content": "Fast for 8-12 hours before the test. Only plain water is allowed during fasting. Schedule the test in the morning for convenience.",
        "fasting": "Yes - 8-12 hours",
        "water": "Plain water only",
        "medications": "Take diabetes medications only after the test",
        "requirements": "Valid ID, prescription, and fasting confirmation"
    },
    {
        "test_name": "Lipid Profile",
        "content": "Fast for 9-12 hours before the test. Avoid alcohol for 24 hours before the test. Take your regular medications with water unless advised otherwise.",
        "fasting": "Yes - 9-12 hours",
        "water": "Plain water allowed",
        "medications": "Continue medications with small sips of water",
        "requirements": "Valid ID and prescription"
    },
    {
        "test_name": "HbA1c (Glycated Hemoglobin)",
        "content": "No fasting required. This test can be done at any time of the day. Continue your normal diet and medications.",
        "fasting": "No",
        "water": "Normal intake",
        "medications": "Continue as prescribed",
        "requirements": "Valid ID and prescription"
    },
    {
        "test_name": "Thyroid Function Test (T3, T4, TSH)",
        "content": "No fasting required, but morning testing is preferred. If you're on thyroid medication, take it after the test for accurate results.",
        "fasting": "No",
        "water": "Normal intake",
        "medications": "Take thyroid medication after the test",
        "requirements": "Valid ID and prescription"
    },
    {
        "test_name": "Liver Function Test (LFT)",
        "content": "Fasting for 8-12 hours is recommended. Avoid alcohol for 24-48 hours before the test. Drink plenty of water.",
        "fasting": "Yes - 8-12 hours recommended",
        "water": "Drink plenty of water",
        "medications": "Inform lab about all medications",
        "requirements": "Valid ID and prescription"
    },
    {
        "test_name": "Kidney Function Test (KFT/RFT)",
        "content": "Fasting not mandatory but may be recommended. Maintain normal water intake unless advised otherwise. Avoid strenuous exercise before the test.",
        "fasting": "May be recommended - check with doctor",
        "water": "Normal intake (stay hydrated)",
        "medications": "Continue medications",
        "requirements": "Valid ID and prescription"
    },
    {
        "test_name": "Ultrasound Abdomen",
        "content": "Fast for 6-8 hours before the test. Drink 4-6 glasses of water 1 hour before and do NOT urinate (for full bladder). Wear loose, comfortable clothing.",
        "fasting": "Yes - 6-8 hours",
        "water": "Drink 4-6 glasses 1 hour before test (full bladder required)",
        "medications": "Continue as prescribed",
        "requirements": "Valid ID, prescription, previous reports if any"
    },
    {
        "test_name": "CT Scan",
        "content": "Fast for 4-6 hours if contrast dye will be used. Inform staff about allergies, kidney problems, or pregnancy. Remove metal objects and jewelry.",
        "fasting": "Yes - 4-6 hours (if contrast used)",
        "water": "Limited intake before test",
        "medications": "Inform doctor about all medications, especially diabetes drugs",
        "requirements": "Valid ID, prescription, kidney function reports if contrast used"
    },
    {
        "test_name": "MRI Scan",
        "content": "No special preparation for most MRI scans. Remove all metal objects (jewelry, watches, hairpins). Inform staff if you have pacemaker, metal implants, or claustrophobia.",
        "fasting": "Usually not required",
        "water": "Normal intake",
        "medications": "Continue as prescribed",
        "requirements": "Valid ID, prescription, inform about metal implants"
    },
    {
        "test_name": "ECG (Electrocardiogram)",
        "content": "No special preparation needed. Avoid caffeine 2-3 hours before test. Wear loose clothing for easy chest access. Rest for 5 minutes before the test.",
        "fasting": "No",
        "water": "Normal intake",
        "medications": "Continue all medications",
        "requirements": "Valid ID and prescription"
    },
    {
        "test_name": "Urine Routine Examination",
        "content": "Collect first-morning urine sample for best results. Use the sterile container provided. Clean the genital area before collection. Deliver sample within 1-2 hours.",
        "fasting": "No",
        "water": "Normal intake (avoid excessive water)",
        "medications": "Continue medications",
        "requirements": "Valid ID, prescription, sterile collection container"
    },
    {
        "test_name": "X-Ray Chest",
        "content": "No special preparation needed. Wear clothing without metal buttons or zippers. Remove jewelry, bra with metal, and metal objects from chest area.",
        "fasting": "No",
        "water": "Normal intake",
        "medications": "Continue medications",
        "requirements": "Valid ID and prescription"
    },
    {
        "test_name": "Colonoscopy",
        "content": "Follow bowel preparation instructions carefully (usually 1-2 days before). Liquid diet 24 hours before. Take prescribed laxatives. Arrange for someone to drive you home.",
        "fasting": "Yes - clear liquids only 24 hours before",
        "water": "Clear liquids and water until 2 hours before",
        "medications": "Discuss with doctor (may need to stop blood thinners)",
        "requirements": "Valid ID, prescription, consent form, escort required"
    },
    {
        "test_name": "Endoscopy",
        "content": "Fast for 6-8 hours before the procedure. No food or water after midnight if morning test. Inform doctor about medications and allergies. Arrange transportation home.",
        "fasting": "Yes - 6-8 hours",
        "water": "No water 2 hours before test",
        "medications": "Discuss with doctor (may pause blood thinners)",
        "requirements": "Valid ID, prescription, consent form, escort required"
    }
]


# Post-Surgery Care Instructions
POST_SURGERY_CARE = [
    {
        "surgery_name": "Appendectomy (Appendix Removal)",
        "content": "Keep the incision area clean and dry. Avoid heavy lifting for 2-3 weeks. Start with light walking after 24 hours. Gradually resume normal activities over 2-4 weeks.",
        "recovery_time": "2-4 weeks for full recovery",
        "medications": "Pain relievers, antibiotics as prescribed",
        "restrictions": "No heavy lifting (>5kg), avoid strenuous exercise for 3-4 weeks",
        "warning_signs": "Fever >100.4°F, increasing pain, redness/swelling at incision, pus drainage"
    },
    {
        "surgery_name": "Cesarean Section (C-Section)",
        "content": "Rest as much as possible. Avoid stairs for first week. Keep incision clean. Support abdomen when coughing/sneezing. Gentle walking aids recovery.",
        "recovery_time": "6-8 weeks for complete healing",
        "medications": "Pain medication, antibiotics, iron supplements",
        "restrictions": "No driving for 2-3 weeks, no heavy lifting, avoid sexual activity for 6 weeks",
        "warning_signs": "Heavy bleeding, fever, severe abdominal pain, foul-smelling discharge"
    },
    {
        "surgery_name": "Gallbladder Removal (Cholecystectomy)",
        "content": "Start with bland, low-fat diet. Gradually reintroduce regular foods. Rest for first few days. Short walks help prevent complications.",
        "recovery_time": "1-2 weeks (laparoscopic), 4-6 weeks (open surgery)",
        "medications": "Pain medication, anti-nausea medication if needed",
        "restrictions": "Avoid fatty foods initially, no heavy lifting for 2-3 weeks",
        "warning_signs": "Severe abdominal pain, yellowing of skin/eyes, persistent nausea/vomiting"
    },
    {
        "surgery_name": "Hernia Repair",
        "content": "Avoid straining, heavy lifting, and strenuous activities. Use ice packs for swelling. Wear support garment if recommended. Gradually increase activity.",
        "recovery_time": "2-4 weeks (laparoscopic), 4-6 weeks (open repair)",
        "medications": "Pain medication, stool softeners",
        "restrictions": "No lifting >10 lbs for 4-6 weeks, avoid constipation",
        "warning_signs": "Bulge at surgical site, increasing pain, fever, wound infection"
    },
    {
        "surgery_name": "Knee Replacement",
        "content": "Follow physical therapy exercises religiously. Use walker/crutches as advised. Ice and elevate knee regularly. Keep wound clean and dry.",
        "recovery_time": "3-6 months for full recovery, 1 year for maximum benefit",
        "medications": "Pain medication, blood thinners, antibiotics",
        "restrictions": "Avoid kneeling, high-impact activities; use elevated toilet seat",
        "warning_signs": "Increased swelling, severe pain, chest pain, calf pain/swelling"
    },
    {
        "surgery_name": "Hip Replacement",
        "content": "Follow hip precautions (don't bend hip >90°, don't cross legs). Use assistive devices. Physical therapy is crucial. Sleep on back or non-operated side.",
        "recovery_time": "6-12 months for full recovery",
        "medications": "Pain medication, blood thinners, antibiotics",
        "restrictions": "Avoid bending forward, crossing legs, twisting hip",
        "warning_signs": "Hip dislocation (severe pain, leg position change), chest pain, breathing difficulty"
    },
    {
        "surgery_name": "Cataract Surgery",
        "content": "Use prescribed eye drops regularly. Wear eye shield while sleeping. Avoid rubbing eyes. No swimming or hot tubs for 2 weeks.",
        "recovery_time": "4-6 weeks for complete healing",
        "medications": "Antibiotic and anti-inflammatory eye drops",
        "restrictions": "No driving for 24 hours, avoid heavy lifting, bending, swimming",
        "warning_signs": "Vision loss, severe pain, flashes of light, increased redness"
    },
    {
        "surgery_name": "Dental Extraction (Tooth Removal)",
        "content": "Bite on gauze for 30-45 minutes. Apply ice pack for swelling. Soft foods for 24-48 hours. Gentle saltwater rinses after 24 hours.",
        "recovery_time": "3-7 days",
        "medications": "Pain medication, antibiotics if prescribed",
        "restrictions": "No smoking, alcohol, straws (suction can dislodge clot), spicy foods",
        "warning_signs": "Excessive bleeding, severe pain after 3 days, fever, bad taste/smell"
    },
    {
        "surgery_name": "Hysterectomy",
        "content": "Rest for first 2 weeks. Avoid lifting, pushing, or pulling. No sexual activity for 6-8 weeks. Gradual return to normal activities.",
        "recovery_time": "6-8 weeks (laparoscopic), 8-12 weeks (abdominal)",
        "medications": "Pain medication, hormones if ovaries removed",
        "restrictions": "No heavy lifting, no driving for 2-3 weeks, no intercourse for 6-8 weeks",
        "warning_signs": "Heavy bleeding, fever, severe pain, foul discharge"
    },
    {
        "surgery_name": "Tonsillectomy",
        "content": "Cold liquids and soft foods for 1-2 weeks. Avoid acidic, spicy foods. Stay hydrated. Rest voice. Use humidifier.",
        "recovery_time": "10-14 days",
        "medications": "Pain medication, avoid aspirin",
        "restrictions": "Avoid strenuous activity, hot foods, coughing forcefully",
        "warning_signs": "Bleeding from throat, difficulty breathing, severe dehydration"
    }
]

def seed_test_preparations():
    """Seed test preparation instructions"""
    
    try:
        with DatabaseConnection.get_connection() as conn:
            cur = conn.cursor()
            
            print("🧪 Seeding test preparation instructions...")
            
            for test in TEST_PREPARATIONS:
                # Create embedding
                embedding_text = f"{test['test_name']} {test['content']}"
                embedding = rag_service.create_embedding(embedding_text)
                
                if not embedding:
                    print(f"❌ Failed to create embedding for {test['test_name']}")
                    continue
                
                # Prepare metadata
                metadata = {
                    "test_name": test["test_name"],
                    "fasting": test["fasting"],
                    "water": test["water"],
                    "medications": test["medications"],
                    "requirements": test["requirements"]
                }
                
                # Insert into database
                insert_query = """
                    INSERT INTO document_embeddings (content, embedding, doc_type, metadata, source)
                    VALUES (%s, %s::vector, %s, %s, %s)
                """
                
                cur.execute(
                    insert_query,
                    (
                        test["content"],
                        embedding,
                        "test_preparation",
                        json.dumps(metadata),
                        f"medical_guidelines_{test['test_name']}"
                    )
                )
                
                print(f"✅ Added: {test['test_name']}")
            
            print(f"✅ Seeded {len(TEST_PREPARATIONS)} test preparations")
            cur.close()
            
    except Exception as e:
        print(f"❌ Error seeding test preparations: {e}")
        raise


def seed_post_surgery_care():
    """Seed post-surgery care instructions"""
    
    try:
        with DatabaseConnection.get_connection() as conn:
            cur = conn.cursor()
            
            print("🏥 Seeding post-surgery care instructions...")
            
            for surgery in POST_SURGERY_CARE:
                # Create embedding
                embedding_text = f"{surgery['surgery_name']} {surgery['content']}"
                embedding = rag_service.create_embedding(embedding_text)
                
                if not embedding:
                    print(f"❌ Failed to create embedding for {surgery['surgery_name']}")
                    continue
                
                # Prepare metadata
                metadata = {
                    "surgery_name": surgery["surgery_name"],
                    "recovery_time": surgery["recovery_time"],
                    "medications": surgery["medications"],
                    "restrictions": surgery["restrictions"],
                    "warning_signs": surgery["warning_signs"]
                }
                
                # Insert into database
                insert_query = """
                    INSERT INTO document_embeddings (content, embedding, doc_type, metadata, source)
                    VALUES (%s, %s::vector, %s, %s, %s)
                """
                
                cur.execute(
                    insert_query,
                    (
                        surgery["content"],
                        embedding,
                        "post_surgery_care",
                        json.dumps(metadata),
                        f"medical_guidelines_{surgery['surgery_name']}"
                    )
                )
                
                print(f"✅ Added: {surgery['surgery_name']}")
            
            print(f"✅ Seeded {len(POST_SURGERY_CARE)} post-surgery care instructions")
            cur.close()
            
    except Exception as e:
        print(f"❌ Error seeding post-surgery care: {e}")
        raise


if __name__ == "__main__":
    print("🚀 Starting medical instructions seeding...")
    print("=" * 60)
    
    seed_test_preparations()
    print()
    seed_post_surgery_care()
    
    print("=" * 60)
    print("✅ All medical instructions seeded successfully!")