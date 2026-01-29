"""
Seed medicine instructions into PGVector for RAG
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.db_connection import DatabaseConnection
from backend.rag_service import rag_service
import json


# Enhanced medicine instructions database with timing, dosage, and age
MEDICINE_INSTRUCTIONS = [
    # Pain Relief & Fever (10)
    {
        'medicine': 'Paracetamol 500mg',
        'timing': 'After food',
        'dosage': '1 tablet every 4-6 hours, maximum 8 tablets in 24 hours',
        'age_restriction': 'Adults and children above 12 years',
        'instructions': 'Take after meals to reduce stomach irritation. Space doses at least 4 hours apart.',
        'precautions': 'Avoid alcohol. Do not combine with other paracetamol-containing medicines. Overdose can cause liver damage.',
        'category': 'Pain Relief'
    },
    {
        'medicine': 'Paracetamol 650mg',
        'timing': 'After food',
        'dosage': '1 tablet every 6 hours, maximum 4 tablets in 24 hours',
        'age_restriction': 'Adults only',
        'instructions': 'Take after meals. Suitable for higher pain or fever. Do not exceed recommended dose.',
        'precautions': 'Avoid alcohol. Risk of liver damage if overdosed.',
        'category': 'Pain Relief'
    },
    {
        'medicine': 'Ibuprofen 400mg',
        'timing': 'After food',
        'dosage': '1 tablet every 6-8 hours, maximum 3 tablets per day',
        'age_restriction': 'Adults and children above 12 years',
        'instructions': 'Must be taken with or immediately after food to protect stomach lining.',
        'precautions': 'Avoid if you have stomach ulcers, kidney problems, or heart disease. Not for long-term use.',
        'category': 'Pain Relief'
    },
    {
        'medicine': 'Diclofenac 50mg',
        'timing': 'After food',
        'dosage': '1 tablet twice or thrice daily',
        'age_restriction': 'Adults only',
        'instructions': 'Take after meals. Strong pain reliever for joint and muscle pain.',
        'precautions': 'High risk of stomach ulcers. Avoid in elderly, heart patients, and kidney disease.',
        'category': 'Pain Relief'
    },
    {
        'medicine': 'Tramadol 50mg',
        'timing': 'With or without food',
        'dosage': '1 tablet every 6 hours as needed, maximum 8 tablets in 24 hours',
        'age_restriction': 'Adults only, prescription required',
        'instructions': 'Strong pain medication. May cause drowsiness.',
        'precautions': 'Do not drive or operate machinery. Risk of addiction. Avoid alcohol.',
        'category': 'Pain Relief'
    },
    {
        'medicine': 'Mefenamic Acid 500mg',
        'timing': 'After food',
        'dosage': '1 tablet 3 times daily for maximum 7 days',
        'age_restriction': 'Adults and children above 14 years',
        'instructions': 'Take after meals. Commonly used for menstrual pain.',
        'precautions': 'Do not use for more than 7 days. Avoid in kidney disease.',
        'category': 'Pain Relief'
    },
    {
        'medicine': 'Aspirin 75mg',
        'timing': 'After food',
        'dosage': '1 tablet once daily',
        'age_restriction': 'Adults only',
        'instructions': 'Low-dose aspirin for heart protection. Take after breakfast daily.',
        'precautions': 'Risk of bleeding. Inform surgeon before any procedure. Avoid NSAIDs.',
        'category': 'Blood Thinner'
    },
    {
        'medicine': 'Aspirin 325mg',
        'timing': 'After food',
        'dosage': '1 tablet when needed, maximum 4 times daily',
        'age_restriction': 'Adults only',
        'instructions': 'Take with food or milk. For pain and fever.',
        'precautions': 'Risk of stomach bleeding. Not for children (Reye syndrome risk).',
        'category': 'Pain Relief'
    },
    {
        'medicine': 'Ketorolac 10mg',
        'timing': 'After food',
        'dosage': '1 tablet every 6 hours, maximum 5 days',
        'age_restriction': 'Adults only',
        'instructions': 'Very strong pain reliever. Short-term use only.',
        'precautions': 'High risk of side effects. Not for long-term use. Avoid in elderly.',
        'category': 'Pain Relief'
    },
    {
        'medicine': 'Aceclofenac 100mg',
        'timing': 'After food',
        'dosage': '1 tablet twice daily',
        'age_restriction': 'Adults only',
        'instructions': 'Take after breakfast and dinner for joint pain.',
        'precautions': 'Protect stomach with food. Risk of gastric issues.',
        'category': 'Pain Relief'
    },
    
    # Antibiotics (15)
    {
        'medicine': 'Amoxicillin 500mg',
        'timing': 'With or without food',
        'dosage': '1 capsule 3 times daily for 5-7 days',
        'age_restriction': 'All ages (dose varies)',
        'instructions': 'Complete the full course even if symptoms improve. Space doses evenly (every 8 hours).',
        'precautions': 'Allergic to penicillin? Do not take. May cause diarrhea. Probiotics recommended.',
        'category': 'Antibiotic'
    },
    {
        'medicine': 'Azithromycin 500mg',
        'timing': '1 hour before food or 2 hours after food',
        'dosage': '1 tablet once daily for 3 days',
        'age_restriction': 'Adults and children above 6 months (dose varies)',
        'instructions': 'Take on empty stomach for better absorption. Short 3-day course.',
        'precautions': 'Avoid antacids within 2 hours. May cause nausea.',
        'category': 'Antibiotic'
    },
    {
        'medicine': 'Ciprofloxacin 500mg',
        'timing': '2 hours before or after food/milk',
        'dosage': '1 tablet twice daily for 7-14 days',
        'age_restriction': 'Adults only, not for children',
        'instructions': 'Do not take with dairy products or antacids. Drink plenty of water.',
        'precautions': 'Risk of tendon rupture. Avoid sunlight. Not for pregnant women or children.',
        'category': 'Antibiotic'
    },
    {
        'medicine': 'Cefixime 200mg',
        'timing': 'With or without food',
        'dosage': '1 tablet twice daily or 400mg once daily for 7 days',
        'age_restriction': 'All ages (dose varies)',
        'instructions': 'Can be taken with food to reduce nausea. Complete full course.',
        'precautions': 'Inform doctor if allergic to penicillin. May cause diarrhea.',
        'category': 'Antibiotic'
    },
    {
        'medicine': 'Doxycycline 100mg',
        'timing': 'After food with full glass of water',
        'dosage': '1 tablet twice daily or once daily as prescribed',
        'age_restriction': 'Adults and children above 8 years',
        'instructions': 'Take with plenty of water. Stay upright for 30 minutes after taking to avoid esophageal irritation.',
        'precautions': 'Avoid dairy, iron, antacids within 2 hours. Increases sun sensitivity. Tooth discoloration in children.',
        'category': 'Antibiotic'
    },
    {
        'medicine': 'Levofloxacin 500mg',
        'timing': 'With or without food',
        'dosage': '1 tablet once daily for 7-14 days',
        'age_restriction': 'Adults only',
        'instructions': 'Can be taken with meals. Avoid dairy and antacids.',
        'precautions': 'Risk of tendon rupture. Avoid in children and pregnant women.',
        'category': 'Antibiotic'
    },
    {
        'medicine': 'Metronidazole 400mg',
        'timing': 'With or after food',
        'dosage': '1 tablet 2-3 times daily for 5-10 days',
        'age_restriction': 'All ages (dose varies)',
        'instructions': 'Take with or after meals to reduce nausea.',
        'precautions': 'Absolutely no alcohol during and 3 days after treatment (severe reaction). May cause metallic taste.',
        'category': 'Antibiotic'
    },

    
]


def seed_medicine_instructions():
    """Seed enhanced medicine instructions into PGVector"""
    
    try:
        with DatabaseConnection.get_connection() as conn:
            cur = conn.cursor()
            
            print(f"\nSeeding {len(MEDICINE_INSTRUCTIONS)} medicine instructions...")
            
            for idx, med_info in enumerate(MEDICINE_INSTRUCTIONS, 1):
                # Create comprehensive content for embedding with all details
                content = (
                    f"{med_info['medicine']}. "
                    f"Timing: {med_info['timing']}. "
                    f"Dosage: {med_info['dosage']}. "
                    f"Age: {med_info['age_restriction']}. "
                    f"{med_info['instructions']} "
                    f"{med_info['precautions']}"
                )
                
                print(f"{idx}. Embedding: {med_info['medicine']}...")
                
                embedding = rag_service.create_embedding(content)
                
                if not embedding:
                    print(f"❌ Failed to create embedding for {med_info['medicine']}")
                    continue
                
                metadata = {
                    'medicine': med_info['medicine'],
                    'timing': med_info['timing'],
                    'dosage': med_info['dosage'],
                    'age_restriction': med_info['age_restriction'],
                    'instructions': med_info['instructions'],
                    'precautions': med_info['precautions'],
                    'category': med_info['category']
                }
                
                insert_query = """
                    INSERT INTO document_embeddings 
                    (content, embedding, metadata, doc_type)
                    VALUES (%s, %s::vector, %s, %s)
                """
                
                cur.execute(insert_query, (
                    content,
                    embedding,
                    json.dumps(metadata),
                    'medicine_info'
                ))
            
            print(f"\n✅ Successfully seeded {len(MEDICINE_INSTRUCTIONS)} medicine instructions!")
            
            cur.execute("SELECT COUNT(*) FROM document_embeddings WHERE doc_type = 'medicine_info'")
            count = cur.fetchone()[0]
            print(f"✅ Total medicine instructions in database: {count}")
            
            cur.close()
        
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    seed_medicine_instructions()
