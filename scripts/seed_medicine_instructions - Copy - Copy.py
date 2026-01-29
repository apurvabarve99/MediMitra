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
    {
        'medicine': 'Clarithromycin 500mg',
        'timing': 'With food',
        'dosage': '1 tablet twice daily for 7-14 days',
        'age_restriction': 'All ages (dose varies)',
        'instructions': 'Take with meals to improve absorption and reduce stomach upset.',
        'precautions': 'May interact with many medications. Inform doctor of all medicines.',
        'category': 'Antibiotic'
    },
    {
        'medicine': 'Cloxacillin 500mg',
        'timing': '1 hour before food',
        'dosage': '1 capsule 4 times daily (every 6 hours)',
        'age_restriction': 'All ages (dose varies)',
        'instructions': 'Must be taken on empty stomach for best absorption.',
        'precautions': 'Penicillin allergy contraindicated. Complete full course.',
        'category': 'Antibiotic'
    },
    {
        'medicine': 'Linezolid 600mg',
        'timing': 'With or without food',
        'dosage': '1 tablet twice daily for 10-28 days',
        'age_restriction': 'All ages (dose varies)',
        'instructions': 'Expensive antibiotic for resistant infections. Space doses 12 hours apart.',
        'precautions': 'Avoid tyramine-rich foods (aged cheese, wine). Monitor blood counts.',
        'category': 'Antibiotic'
    },
    {
        'medicine': 'Moxifloxacin 400mg',
        'timing': 'With or without food',
        'dosage': '1 tablet once daily for 7-10 days',
        'age_restriction': 'Adults only',
        'instructions': 'Broad-spectrum antibiotic. Once daily dosing.',
        'precautions': 'Risk of tendon damage. Avoid in heart rhythm problems.',
        'category': 'Antibiotic'
    },
    {
        'medicine': 'Cefpodoxime 200mg',
        'timing': 'With food',
        'dosage': '1 tablet twice daily for 7-10 days',
        'age_restriction': 'All ages (dose varies)',
        'instructions': 'Take with meals for better absorption.',
        'precautions': 'Complete full course. May cause diarrhea.',
        'category': 'Antibiotic'
    },
    {
        'medicine': 'Nitrofurantoin 100mg',
        'timing': 'With food or milk',
        'dosage': '1 tablet twice daily for 7 days',
        'age_restriction': 'Adults and children above 1 month',
        'instructions': 'Specific for urinary tract infections. Take with food or milk.',
        'precautions': 'May turn urine dark yellow/brown (normal). Avoid in kidney disease.',
        'category': 'Antibiotic'
    },
    {
        'medicine': 'Co-Amoxiclav 625mg',
        'timing': 'At start of meal',
        'dosage': '1 tablet twice or thrice daily for 5-7 days',
        'age_restriction': 'All ages (dose varies)',
        'instructions': 'Amoxicillin + Clavulanic acid. Take at start of meal to reduce side effects.',
        'precautions': 'May cause diarrhea. Risk of liver issues with prolonged use.',
        'category': 'Antibiotic'
    },
    {
        'medicine': 'Norfloxacin 400mg',
        'timing': '1 hour before or 2 hours after food',
        'dosage': '1 tablet twice daily for 3-7 days',
        'age_restriction': 'Adults only',
        'instructions': 'Empty stomach for UTI treatment. Drink plenty of water.',
        'precautions': 'Avoid dairy, antacids. Risk of tendon issues.',
        'category': 'Antibiotic'
    },
    
    # Gastric/Antacids (12)
    {
        'medicine': 'Pantoprazole 40mg',
        'timing': '30 minutes before breakfast',
        'dosage': '1 tablet once daily',
        'age_restriction': 'Adults and children above 5 years',
        'instructions': 'Must be taken on empty stomach, 30 minutes before first meal for maximum effectiveness.',
        'precautions': 'Long-term use may cause vitamin B12, magnesium deficiency. Swallow whole, do not crush.',
        'category': 'Antacid'
    },
    {
        'medicine': 'Omeprazole 20mg',
        'timing': '30 minutes before breakfast',
        'dosage': '1 capsule once daily',
        'age_restriction': 'Adults and children above 1 year',
        'instructions': 'Take 30 minutes before breakfast on empty stomach. Swallow capsule whole.',
        'precautions': 'Long-term use increases fracture risk, vitamin B12 deficiency. Do not chew capsules.',
        'category': 'Antacid'
    },
    {
        'medicine': 'Rabeprazole 20mg',
        'timing': '30 minutes before breakfast',
        'dosage': '1 tablet once daily',
        'age_restriction': 'Adults only',
        'instructions': 'Empty stomach before breakfast for acid reflux, GERD, ulcers.',
        'precautions': 'Similar to other PPIs. Monitor for vitamin deficiencies on long-term use.',
        'category': 'Antacid'
    },
    {
        'medicine': 'Esomeprazole 40mg',
        'timing': '1 hour before food',
        'dosage': '1 tablet once daily',
        'age_restriction': 'Adults and children above 12 years',
        'instructions': 'Most potent PPI. Take 1 hour before meals.',
        'precautions': 'Long-term use needs monitoring. Risk of C. difficile infection.',
        'category': 'Antacid'
    },
    {
        'medicine': 'Ranitidine 150mg',
        'timing': 'Before food or at bedtime',
        'dosage': '1 tablet twice daily or 1 tablet at night',
        'age_restriction': 'All ages (dose varies)',
        'instructions': 'H2 blocker. Can be taken before meals or at bedtime for nighttime acid.',
        'precautions': 'Less potent than PPIs. Generally safe for short-term use.',
        'category': 'Antacid'
    },
    {
        'medicine': 'Famotidine 20mg',
        'timing': 'Before food or at bedtime',
        'dosage': '1 tablet once or twice daily',
        'age_restriction': 'All ages (dose varies)',
        'instructions': 'Alternative to ranitidine. Take before meals or at night.',
        'precautions': 'Fewer drug interactions than PPIs. Safe for most patients.',
        'category': 'Antacid'
    },
    {
        'medicine': 'Sucralfate 1g',
        'timing': '1 hour before food and at bedtime',
        'dosage': '1 tablet 4 times daily',
        'age_restriction': 'Adults and children above 4 years',
        'instructions': 'Forms protective coating over ulcers. Must be taken on empty stomach.',
        'precautions': 'Space apart from other medicines by 2 hours. May cause constipation.',
        'category': 'Antacid'
    },
    {
        'medicine': 'Domperidone 10mg',
        'timing': '15-30 minutes before food',
        'dosage': '1 tablet 3 times daily before meals',
        'age_restriction': 'Adults and children above 12 years',
        'instructions': 'Prokinetic agent for nausea, bloating, indigestion. Take before meals.',
        'precautions': 'May cause irregular heartbeat. Not for heart patients. Maximum 7 days use.',
        'category': 'Antiemetic'
    },
    {
        'medicine': 'Ondansetron 4mg',
        'timing': '30 minutes before food',
        'dosage': '1 tablet twice or thrice daily',
        'age_restriction': 'All ages (dose varies)',
        'instructions': 'Strong anti-nausea medication. Commonly used after chemotherapy or surgery.',
        'precautions': 'May cause constipation. Risk of heart rhythm issues at high doses.',
        'category': 'Antiemetic'
    },
    {
        'medicine': 'Itopride 50mg',
        'timing': '15 minutes before food',
        'dosage': '1 tablet 3 times daily',
        'age_restriction': 'Adults only',
        'instructions': 'For functional dyspepsia. Take before each meal.',
        'precautions': 'Safer than domperidone for cardiac patients. May cause diarrhea.',
        'category': 'Prokinetic'
    },
    {
        'medicine': 'Mosapride 5mg',
        'timing': '15 minutes before food',
        'dosage': '1 tablet 3 times daily',
        'age_restriction': 'Adults only',
        'instructions': 'Gastroprokinetic for GERD and functional dyspepsia. Before meals.',
        'precautions': 'Fewer cardiac side effects. May cause diarrhea.',
        'category': 'Prokinetic'
    },
    {
        'medicine': 'Antacid Syrup (Digene/Gelusil)',
        'timing': '1-2 hours after food and at bedtime',
        'dosage': '2 teaspoons 4 times daily',
        'age_restriction': 'All ages',
        'instructions': 'Neutralizes acid immediately. Take after meals when acid is produced.',
        'precautions': 'Temporary relief only. May interfere with other medicine absorption.',
        'category': 'Antacid'
    },
    
    # Diabetes (8)
    {
        'medicine': 'Metformin 500mg',
        'timing': 'With or after food',
        'dosage': '1 tablet twice daily with breakfast and dinner',
        'age_restriction': 'Adults and children above 10 years',
        'instructions': 'First-line diabetes medicine. Must be taken with meals to reduce stomach upset.',
        'precautions': 'May cause diarrhea initially. Avoid alcohol. Stop before surgery or CT scan with contrast. Monitor kidney function.',
        'category': 'Diabetes'
    },
    {
        'medicine': 'Metformin 1000mg Extended Release',
        'timing': 'With dinner',
        'dosage': '1 tablet once daily with evening meal',
        'age_restriction': 'Adults only',
        'instructions': 'Slow-release formula reduces side effects. Take with largest meal of the day.',
        'precautions': 'Swallow whole, do not crush or chew. May see tablet shell in stool (normal).',
        'category': 'Diabetes'
    },
    {
        'medicine': 'Glimepiride 1mg',
        'timing': 'Before breakfast',
        'dosage': '1 tablet once daily before first meal',
        'age_restriction': 'Adults only',
        'instructions': 'Stimulates insulin release. Must be taken before breakfast to work effectively.',
        'precautions': 'Risk of low blood sugar (hypoglycemia). Carry glucose/candy. Monitor blood sugar.',
        'category': 'Diabetes'
    },
    {
        'medicine': 'Glimepiride 2mg',
        'timing': 'Before breakfast',
        'dosage': '1 tablet once daily before first meal',
        'age_restriction': 'Adults only',
        'instructions': 'Higher dose for better control. Take 15-30 minutes before breakfast.',
        'precautions': 'Higher risk of hypoglycemia. Never skip meals after taking.',
        'category': 'Diabetes'
    },
    {
        'medicine': 'Gliclazide 80mg',
        'timing': 'Before breakfast',
        'dosage': '1-2 tablets once or twice daily before meals',
        'age_restriction': 'Adults only',
        'instructions': 'Sulfonylurea for type 2 diabetes. Take 30 minutes before meals.',
        'precautions': 'Risk of low blood sugar. Eat regular meals. Avoid alcohol.',
        'category': 'Diabetes'
    },
    {
        'medicine': 'Vildagliptin 50mg',
        'timing': 'With or without food',
        'dosage': '1 tablet twice daily (morning and evening)',
        'age_restriction': 'Adults only',
        'instructions': 'DPP-4 inhibitor. Can be taken with or without food. Often combined with metformin.',
        'precautions': 'Lower risk of hypoglycemia. Monitor liver function. May cause joint pain.',
        'category': 'Diabetes'
    },
    {
        'medicine': 'Sitagliptin 100mg',
        'timing': 'With or without food',
        'dosage': '1 tablet once daily',
        'age_restriction': 'Adults only',
        'instructions': 'DPP-4 inhibitor. Once daily dosing, any time of day.',
        'precautions': 'Dose adjustment needed in kidney disease. Risk of pancreatitis.',
        'category': 'Diabetes'
    },
    {
        'medicine': 'Empagliflozin 10mg',
        'timing': 'In the morning with or without food',
        'dosage': '1 tablet once daily in morning',
        'age_restriction': 'Adults only',
        'instructions': 'SGLT2 inhibitor. Take in morning. Increases urination and urinary glucose.',
        'precautions': 'Maintain hydration. Risk of urinary and genital infections. Monitor kidney function.',
        'category': 'Diabetes'
    },
    
    # Thyroid (4)
    {
        'medicine': 'Levothyroxine 25mcg',
        'timing': '1 hour before breakfast on empty stomach',
        'dosage': '1 tablet once daily',
        'age_restriction': 'All ages (dose varies)',
        'instructions': 'Thyroid hormone replacement. Must be taken 1 hour before breakfast for optimal absorption. Same time daily.',
        'precautions': 'Do not take with calcium, iron, soy, coffee. Wait 4 hours before these. Regular blood tests needed. Never stop suddenly.',
        'category': 'Thyroid'
    },
    {
        'medicine': 'Levothyroxine 50mcg',
        'timing': '1 hour before breakfast on empty stomach',
        'dosage': '1 tablet once daily',
        'age_restriction': 'All ages (dose varies)',
        'instructions': 'Common starting dose for hypothyroidism. Empty stomach, 1 hour before food.',
        'precautions': 'Space apart from vitamins, antacids, iron. Consistency is key.',
        'category': 'Thyroid'
    },
    {
        'medicine': 'Levothyroxine 100mcg',
        'timing': '1 hour before breakfast on empty stomach',
        'dosage': '1 tablet once daily',
        'age_restriction': 'Adults',
        'instructions': 'Higher dose for severe hypothyroidism. Strict timing required.',
        'precautions': 'May cause palpitations if overdosed. Monitor TSH regularly.',
        'category': 'Thyroid'
    },
    {
        'medicine': 'Carbimazole 5mg',
        'timing': 'With or after food',
        'dosage': '1-3 tablets daily in divided doses as prescribed',
        'age_restriction': 'All ages (dose varies)',
        'instructions': 'For hyperthyroidism (overactive thyroid). Take with meals.',
        'precautions': 'Regular blood tests needed. Report sore throat, fever immediately (sign of serious side effect).',
        'category': 'Thyroid'
    },
    
    # Blood Pressure (12)
    {
        'medicine': 'Amlodipine 5mg',
        'timing': 'Same time daily, with or without food',
        'dosage': '1 tablet once daily',
        'age_restriction': 'Adults and children above 6 years',
        'instructions': 'Calcium channel blocker. Can be taken morning or evening, but same time every day.',
        'precautions': 'May cause ankle swelling, headache. Do not stop suddenly. Monitor blood pressure.',
        'category': 'Blood Pressure'
    },
    {
        'medicine': 'Amlodipine 10mg',
        'timing': 'Same time daily, with or without food',
        'dosage': '1 tablet once daily',
        'age_restriction': 'Adults only',
        'instructions': 'Higher dose for resistant hypertension. Consistent timing important.',
        'precautions': 'Higher risk of edema. Gradual discontinuation if needed.',
        'category': 'Blood Pressure'
    },
    {
        'medicine': 'Telmisartan 40mg',
        'timing': 'Same time daily, preferably morning',
        'dosage': '1 tablet once daily',
        'age_restriction': 'Adults only',
        'instructions': 'ARB (Angiotensin Receptor Blocker). Morning dosing preferred.',
        'precautions': 'May cause dizziness when standing. Avoid potassium supplements. Monitor kidney function.',
        'category': 'Blood Pressure'
    },
    {
        'medicine': 'Losartan 50mg',
        'timing': 'Same time daily, with or without food',
        'dosage': '1 tablet once or twice daily',
        'age_restriction': 'Adults and children above 6 years',
        'instructions': 'ARB for blood pressure and kidney protection in diabetes.',
        'precautions': 'Dizziness on standing. Avoid potassium-rich foods in excess.',
        'category': 'Blood Pressure'
    },
    {
        'medicine': 'Atenolol 25mg',
        'timing': 'Same time daily, with or without food',
        'dosage': '1 tablet once or twice daily',
        'age_restriction': 'Adults only',
        'instructions': 'Beta blocker. Slows heart rate and lowers blood pressure.',
        'precautions': 'Do not stop suddenly (risk of rebound hypertension). May mask low blood sugar symptoms. Not for asthmatics.',
        'category': 'Blood Pressure'
    },
    {
        'medicine': 'Metoprolol 25mg',
        'timing': 'With or immediately after food',
        'dosage': '1 tablet twice daily',
        'age_restriction': 'Adults only',
        'instructions': 'Beta blocker for blood pressure and heart rate control. Take with meals.',
        'precautions': 'Do not stop abruptly. May cause fatigue, cold extremities. Not for asthmatics.',
        'category': 'Blood Pressure'
    },
    {
        'medicine': 'Enalapril 5mg',
        'timing': 'Same time daily, with or without food',
        'dosage': '1 tablet once or twice daily',
        'age_restriction': 'Adults and children above 1 month',
        'instructions': 'ACE inhibitor. First dose may cause dizziness (take at bedtime initially).',
        'precautions': 'May cause dry cough (switch to ARB if occurs). Monitor kidney function.',
        'category': 'Blood Pressure'
    },
    {
        'medicine': 'Ramipril 2.5mg',
        'timing': 'Same time daily, with or without food',
        'dosage': '1 tablet once daily',
        'age_restriction': 'Adults only',
        'instructions': 'ACE inhibitor for blood pressure and heart protection. Morning preferred.',
        'precautions': 'Common side effect: dry cough. Monitor potassium levels.',
        'category': 'Blood Pressure'
    },
    {
        'medicine': 'Hydrochlorothiazide 12.5mg',
        'timing': 'In the morning with food',
        'dosage': '1 tablet once daily in morning',
        'age_restriction': 'Adults',
        'instructions': 'Diuretic (water pill). Take in morning to avoid nighttime urination.',
        'precautions': 'Increases urination. May cause low potassium. Avoid if allergic to sulfa drugs.',
        'category': 'Diuretic'
    },
    {
        'medicine': 'Furosemide 40mg',
        'timing': 'In the morning with or without food',
        'dosage': '1 tablet once or twice daily (second dose before 4 PM)',
        'age_restriction': 'All ages (dose varies)',
        'instructions': 'Strong diuretic for fluid retention. Take early in day.',
        'precautions': 'Increases urination significantly. May cause dehydration, low potassium. Monitor electrolytes.',
        'category': 'Diuretic'
    },
    {
        'medicine': 'Spironolactone 25mg',
        'timing': 'With food',
        'dosage': '1 tablet once or twice daily',
        'age_restriction': 'Adults',
        'instructions': 'Potassium-sparing diuretic. Take with meals.',
        'precautions': 'Retains potassium (avoid supplements). May cause breast tenderness in men.',
        'category': 'Diuretic'
    },
    {
        'medicine': 'Nebivolol 5mg',
        'timing': 'Same time daily, with or without food',
        'dosage': '1 tablet once daily',
        'age_restriction': 'Adults only',
        'instructions': 'Modern beta blocker with fewer side effects. Once daily dosing.',
        'precautions': 'Do not stop suddenly. Monitor heart rate and blood pressure.',
        'category': 'Blood Pressure'
    },
    
    # Cholesterol (5)
    {
        'medicine': 'Atorvastatin 10mg',
        'timing': 'At night, with or without food',
        'dosage': '1 tablet once daily at bedtime',
        'age_restriction': 'Adults and children above 10 years',
        'instructions': 'Statin for cholesterol. Night dosing is optimal as cholesterol is synthesized at night.',
        'precautions': 'Avoid grapefruit juice (increases drug levels). Report muscle pain immediately. Monitor liver function.',
        'category': 'Cholesterol'
    },
    {
        'medicine': 'Atorvastatin 20mg',
        'timing': 'At night, with or without food',
        'dosage': '1 tablet once daily at bedtime',
        'age_restriction': 'Adults only',
        'instructions': 'Higher dose for high cholesterol or cardiovascular disease. Evening dosing.',
        'precautions': 'Risk of muscle damage (rhabdomyolysis). Avoid alcohol excess.',
        'category': 'Cholesterol'
    },
    {
        'medicine': 'Rosuvastatin 10mg',
        'timing': 'Same time daily, with or without food',
        'dosage': '1 tablet once daily',
        'age_restriction': 'Adults and children above 10 years',
        'instructions': 'Most potent statin. Can be taken any time but consistently.',
        'precautions': 'Higher risk of muscle side effects at high doses. Monitor regularly.',
        'category': 'Cholesterol'
    },
    {
        'medicine': 'Fenofibrate 145mg',
        'timing': 'With food',
        'dosage': '1 tablet once daily with main meal',
        'age_restriction': 'Adults only',
        'instructions': 'For high triglycerides. Must be taken with food for absorption.',
        'precautions': 'Risk of gallstones. Increases statin side effects if combined. Monitor liver and kidney.',
        'category': 'Cholesterol'
    },
    {
        'medicine': 'Ezetimibe 10mg',
        'timing': 'With or without food',
        'dosage': '1 tablet once daily',
        'age_restriction': 'Adults and children above 10 years',
        'instructions': 'Reduces cholesterol absorption. Often combined with statins.',
        'precautions': 'Generally well tolerated. Monitor liver function if combined with statins.',
        'category': 'Cholesterol'
    },
    
    # Blood Thinners (6)
    {
        'medicine': 'Clopidogrel 75mg',
        'timing': 'With or without food',
        'dosage': '1 tablet once daily',
        'age_restriction': 'Adults only',
        'instructions': 'Antiplatelet for heart attack/stroke prevention. Take at same time daily.',
        'precautions': 'Increases bleeding risk. Inform all doctors and dentist. Avoid NSAIDs. Report unusual bleeding.',
        'category': 'Blood Thinner'
    },
    {
        'medicine': 'Warfarin 5mg',
        'timing': 'Same time daily, preferably evening',
        'dosage': 'As per INR monitoring, usually 1 tablet daily',
        'age_restriction': 'Adults',
        'instructions': 'Strong anticoagulant. Requires regular INR blood tests. Evening dosing allows adjustment based on morning INR.',
        'precautions': 'Strict INR monitoring. Avoid vitamin K-rich foods variability. Many drug interactions. High bleeding risk.',
        'category': 'Blood Thinner'
    },
    {
        'medicine': 'Rivaroxaban 10mg',
        'timing': 'With food',
        'dosage': '1 tablet once daily with largest meal',
        'age_restriction': 'Adults only',
        'instructions': 'Direct oral anticoagulant (DOAC). Must be taken with food for proper absorption.',
        'precautions': 'No INR monitoring needed. Expensive. Bleeding risk. Avoid in severe kidney disease.',
        'category': 'Blood Thinner'
    },
    {
        'medicine': 'Apixaban 5mg',
        'timing': 'With or without food',
        'dosage': '1 tablet twice daily (12 hours apart)',
        'age_restriction': 'Adults only',
        'instructions': 'DOAC for atrial fibrillation and clot prevention. Strict 12-hour dosing.',
        'precautions': 'Do not miss doses. Bleeding risk. Safer in kidney disease than rivaroxaban.',
        'category': 'Blood Thinner'
    },
    {
        'medicine': 'Dabigatran 110mg',
        'timing': 'With or without food',
        'dosage': '1 capsule twice daily',
        'age_restriction': 'Adults only',
        'instructions': 'DOAC. Swallow capsule whole, do not open (irritates stomach).',
        'precautions': 'Higher risk of stomach upset. Keep in original blister until use (moisture sensitive).',
        'category': 'Blood Thinner'
    },
    {
        'medicine': 'Cilostazol 100mg',
        'timing': '30 minutes before or 2 hours after food',
        'dosage': '1 tablet twice daily',
        'age_restriction': 'Adults only',
        'instructions': 'For peripheral artery disease and claudication. Empty stomach required.',
        'precautions': 'Contraindicated in heart failure. May cause headache, diarrhea.',
        'category': 'Blood Thinner'
    },
    
    # Respiratory/Asthma (10)
    {
        'medicine': 'Montelukast 10mg',
        'timing': 'At night before bedtime',
        'dosage': '1 tablet once daily in the evening',
        'age_restriction': 'Adults and children above 6 years (dose varies)',
        'instructions': 'For asthma and allergic rhinitis. Evening dosing is important for asthma control.',
        'precautions': 'May cause mood changes, vivid dreams. Continue even when feeling well.',
        'category': 'Asthma'
    },
    {
        'medicine': 'Cetirizine 10mg',
        'timing': 'At night before bedtime',
        'dosage': '1 tablet once daily in the evening',
        'age_restriction': 'Adults and children above 6 years',
        'instructions': 'Antihistamine for allergies. Night dosing reduces daytime drowsiness.',
        'precautions': 'May cause drowsiness. Avoid driving after taking. Avoid alcohol.',
        'category': 'Antihistamine'
    },
    {
        'medicine': 'Levocetirizine 5mg',
        'timing': 'At night before bedtime',
        'dosage': '1 tablet once daily in evening',
        'age_restriction': 'Adults and children above 6 years',
        'instructions': 'More potent antihistamine. Less sedating than cetirizine but still best at night.',
        'precautions': 'Lower drowsiness risk but still possible. Avoid in kidney disease.',
        'category': 'Antihistamine'
    },
    {
        'medicine': 'Fexofenadine 120mg',
        'timing': 'With or without food',
        'dosage': '1 tablet once daily',
        'age_restriction': 'Adults and children above 12 years',
        'instructions': 'Non-sedating antihistamine. Can be taken any time.',
        'precautions': 'Minimal drowsiness. Avoid fruit juices (reduce absorption).',
        'category': 'Antihistamine'
    },
    {
        'medicine': 'Prednisolone 5mg',
        'timing': 'In the morning after breakfast',
        'dosage': 'As prescribed (varies widely), usually 1-4 tablets daily',
        'age_restriction': 'All ages (dose varies)',
        'instructions': 'Steroid for inflammation. Must be taken in morning with food to mimic natural cortisol rhythm.',
        'precautions': 'Never stop suddenly. Short-term use only when possible. Increases blood sugar, blood pressure. Risk of infections.',
        'category': 'Steroid'
    },
    {
        'medicine': 'Prednisolone 10mg',
        'timing': 'In the morning after breakfast',
        'dosage': 'As prescribed, usually tapered dose',
        'age_restriction': 'All ages (dose varies)',
        'instructions': 'Higher dose steroid. Always take with food in morning.',
        'precautions': 'Taper gradually as directed. Long-term use causes many side effects (weight gain, osteoporosis, diabetes).',
        'category': 'Steroid'
    },
    {
        'medicine': 'Dexamethasone 0.5mg',
        'timing': 'In the morning with food',
        'dosage': 'As prescribed (very potent, low dose)',
        'age_restriction': 'All ages (dose varies)',
        'instructions': 'Very potent steroid. Morning dosing with food.',
        'precautions': 'Much stronger than prednisolone. Strict medical supervision needed.',
        'category': 'Steroid'
    },
    {
        'medicine': 'Salbutamol Inhaler (100mcg)',
        'timing': 'As needed for breathlessness',
        'dosage': '1-2 puffs when required, maximum 8 puffs per day',
        'age_restriction': 'All ages',
        'instructions': 'Rescue inhaler for acute asthma symptoms. Shake well, breathe out fully, inhale deeply while pressing.',
        'precautions': 'If using >8 puffs daily, asthma is uncontrolled (see doctor). May cause tremors, palpitations.',
        'category': 'Asthma'
    },
    {
        'medicine': 'Budesonide Inhaler (200mcg)',
        'timing': 'Twice daily (morning and evening)',
        'dosage': '1-2 puffs twice daily',
        'age_restriction': 'All ages (dose varies)',
        'instructions': 'Controller inhaler (steroid) for asthma. Must be used daily even when feeling well. Rinse mouth after use.',
        'precautions': 'Not for acute relief. Rinse mouth to prevent oral thrush. Do not stop suddenly.',
        'category': 'Asthma'
    },
    {
        'medicine': 'Theophylline 200mg SR',
        'timing': 'Every 12 hours, with or without food',
        'dosage': '1 tablet twice daily',
        'age_restriction': 'Adults and children above 6 years',
        'instructions': 'Bronchodilator for asthma/COPD. Sustained release formula. Consistent timing important.',
        'precautions': 'Narrow therapeutic window. Many drug interactions. May cause palpitations, nausea.',
        'category': 'Asthma'
    },
    
    # Neurological/Psychiatric (15)
    {
        'medicine': 'Gabapentin 300mg',
        'timing': 'With or without food',
        'dosage': '1 capsule 1-3 times daily as prescribed',
        'age_restriction': 'Adults and children above 3 years',
        'instructions': 'For nerve pain and seizures. Start with low dose, gradually increase.',
        'precautions': 'May cause drowsiness, dizziness. Do not stop suddenly (seizure risk). Avoid alcohol.',
        'category': 'Neuropathic Pain'
    },
    {
        'medicine': 'Pregabalin 75mg',
        'timing': 'With or without food',
        'dosage': '1 capsule twice or thrice daily',
        'age_restriction': 'Adults only',
        'instructions': 'For nerve pain, fibromyalgia, anxiety. More potent than gabapentin.',
        'precautions': 'Causes drowsiness, weight gain. Risk of addiction. Gradual discontinuation needed.',
        'category': 'Neuropathic Pain'
    },
    {
        'medicine': 'Amitriptyline 10mg',
        'timing': 'At night 1-2 hours before bedtime',
        'dosage': '1 tablet once daily at night',
        'age_restriction': 'Adults and children above 12 years',
        'instructions': 'Low dose for nerve pain and migraine prevention. Night dosing due to sedation.',
        'precautions': 'Causes dry mouth, drowsiness, constipation. Not for heart patients. Avoid in elderly.',
        'category': 'Neuropathic Pain'
    },
    {
        'medicine': 'Duloxetine 30mg',
        'timing': 'Same time daily, with or without food',
        'dosage': '1 capsule once daily',
        'age_restriction': 'Adults only',
        'instructions': 'For depression, anxiety, diabetic neuropathy. Swallow whole, do not open capsule.',
        'precautions': 'May cause nausea initially. Do not stop abruptly. Monitor for suicidal thoughts.',
        'category': 'Antidepressant'
    },
    {
        'medicine': 'Sertraline 50mg',
        'timing': 'In the morning or evening, with food',
        'dosage': '1 tablet once daily',
        'age_restriction': 'Adults and children above 6 years',
        'instructions': 'SSRI for depression and anxiety. Take with food to reduce nausea. Same time daily.',
        'precautions': 'Takes 2-4 weeks to work. May cause nausea, sexual dysfunction. Do not stop suddenly.',
        'category': 'Antidepressant'
    },
    {
        'medicine': 'Escitalopram 10mg',
        'timing': 'Same time daily, with or without food',
        'dosage': '1 tablet once daily',
        'age_restriction': 'Adults and adolescents above 12 years',
        'instructions': 'SSRI for depression, anxiety. Morning or evening, but consistent.',
        'precautions': 'Initial worsening of anxiety possible. Monitor for suicidal ideation in young adults.',
        'category': 'Antidepressant'
    },
    {
        'medicine': 'Fluoxetine 20mg',
        'timing': 'In the morning with or without food',
        'dosage': '1 capsule once daily',
        'age_restriction': 'Adults and children above 8 years',
        'instructions': 'SSRI with long half-life. Morning dosing preferred (may cause insomnia).',
        'precautions': 'Takes 4-6 weeks for full effect. Easier to discontinue due to long half-life.',
        'category': 'Antidepressant'
    },
    {
        'medicine': 'Alprazolam 0.25mg',
        'timing': 'As needed or 2-3 times daily',
        'dosage': '1 tablet when required for anxiety',
        'age_restriction': 'Adults only',
        'instructions': 'Short-acting benzodiazepine for acute anxiety. Works within 30 minutes.',
        'precautions': 'Highly addictive. Short-term use only. Causes drowsiness. Avoid alcohol. Do not drive.',
        'category': 'Anxiolytic'
    },
    {
        'medicine': 'Clonazepam 0.5mg',
        'timing': 'At night before bedtime',
        'dosage': '1 tablet once or twice daily',
        'age_restriction': 'Adults and children above 10 years',
        'instructions': 'Longer-acting benzodiazepine for anxiety and seizures. Night dosing common.',
        'precautions': 'Risk of dependence. Gradual taper needed. Causes drowsiness and memory issues.',
        'category': 'Anxiolytic'
    },
    {
        'medicine': 'Zolpidem 10mg',
        'timing': 'Immediately before bedtime',
        'dosage': '1 tablet only when needed for sleep',
        'age_restriction': 'Adults only',
        'instructions': 'Sleep medication. Take only when you can sleep for 7-8 hours. Works in 15-30 minutes.',
        'precautions': 'Risk of dependence. May cause sleepwalking, amnesia. Do not take with alcohol. Do not drive after.',
        'category': 'Hypnotic'
    },
    {
        'medicine': 'Quetiapine 25mg',
        'timing': 'At night before bedtime',
        'dosage': '1 tablet once daily at bedtime',
        'age_restriction': 'Adults only',
        'instructions': 'Antipsychotic used for sleep and mood at low doses. Causes sedation.',
        'precautions': 'Weight gain, diabetes risk. Monitor blood sugar. Very sedating.',
        'category': 'Antipsychotic'
    },
    {
        'medicine': 'Risperidone 1mg',
        'timing': 'Same time daily, with or without food',
        'dosage': 'As prescribed by psychiatrist',
        'age_restriction': 'Adults and children above 5 years',
        'instructions': 'Antipsychotic for schizophrenia, bipolar disorder. Strict adherence needed.',
        'precautions': 'May cause movement disorders, weight gain, diabetes. Regular monitoring required.',
        'category': 'Antipsychotic'
    },
    {
        'medicine': 'Methylphenidate 10mg',
        'timing': 'In the morning with or after breakfast',
        'dosage': '1-3 tablets daily (morning and midday)',
        'age_restriction': 'Children above 6 years and adults with ADHD',
        'instructions': 'For ADHD. Take in morning and midday (not after 4 PM to avoid insomnia).',
        'precautions': 'Controlled substance. May suppress appetite, growth. Monitor heart rate, blood pressure.',
        'category': 'ADHD'
    },
    {
        'medicine': 'Levetiracetam 500mg',
        'timing': 'Every 12 hours, with or without food',
        'dosage': '1 tablet twice daily',
        'age_restriction': 'All ages (dose varies)',
        'instructions': 'Anti-epileptic drug. Strict 12-hour dosing. Fewer drug interactions.',
        'precautions': 'Do not stop suddenly (seizure risk). May cause mood changes, drowsiness.',
        'category': 'Antiepileptic'
    },
    {
        'medicine': 'Sodium Valproate 500mg',
        'timing': 'With or after food',
        'dosage': 'Twice daily or as prescribed',
        'age_restriction': 'All ages (dose varies)',
        'instructions': 'Anti-epileptic and mood stabilizer. Take with food to reduce stomach upset.',
        'precautions': 'Teratogenic (do not use in pregnancy). Weight gain, hair loss, tremor. Monitor liver function.',
        'category': 'Antiepileptic'
    },
    
    # Vitamins & Supplements (12)
    {
        'medicine': 'Vitamin D3 60,000 IU',
        'timing': 'After breakfast with fatty food',
        'dosage': '1 capsule once weekly',
        'age_restriction': 'All ages (dose varies)',
        'instructions': 'High-dose vitamin D for deficiency. Take with fatty meal for absorption (fat-soluble vitamin).',
        'precautions': 'Weekly dosing, not daily. Monitor vitamin D levels. Excess causes high calcium.',
        'category': 'Vitamin'
    },
    {
        'medicine': 'Calcium Carbonate 500mg + Vitamin D3',
        'timing': 'With meals',
        'dosage': '1-2 tablets daily with food',
        'age_restriction': 'All ages',
        'instructions': 'Calcium supplement. Must be taken with food for absorption.',
        'precautions': 'May cause constipation. Space apart from thyroid, iron, antibiotics by 2-4 hours.',
        'category': 'Mineral'
    },
    {
        'medicine': 'Iron Folic Acid (IFA)',
        'timing': '1 hour before food or 2 hours after food',
        'dosage': '1 tablet once daily',
        'age_restriction': 'All ages (especially pregnant women, anemic patients)',
        'instructions': 'For anemia. Empty stomach for best absorption. Vitamin C enhances absorption.',
        'precautions': 'Causes black stools (normal), constipation, nausea. Space apart from calcium, tea, coffee.',
        'category': 'Mineral'
    },
    {
        'medicine': 'Vitamin B12 (Methylcobalamin) 1500mcg',
        'timing': 'With or without food',
        'dosage': '1 tablet once daily',
        'age_restriction': 'All ages',
        'instructions': 'For B12 deficiency, nerve health. Sublingual (under tongue) formulation works faster.',
        'precautions': 'Very safe. Common in vegetarians, elderly, diabetes patients on metformin.',
        'category': 'Vitamin'
    },
    {
        'medicine': 'Multivitamin (A-Z)',
        'timing': 'With or after breakfast',
        'dosage': '1 tablet once daily',
        'age_restriction': 'Adults and children above 12 years',
        'instructions': 'General nutritional supplement. Morning with food for better absorption.',
        'precautions': 'Not a substitute for healthy diet. Avoid if taking other vitamin supplements (overdose risk).',
        'category': 'Vitamin'
    },
    {
        'medicine': 'Omega-3 Fatty Acids (Fish Oil)',
        'timing': 'With meals',
        'dosage': '1-2 capsules daily with food',
        'age_restriction': 'All ages',
        'instructions': 'For heart health, triglycerides. Take with fatty meal.',
        'precautions': 'May cause fishy aftertaste, burps. Increases bleeding risk if on blood thinners.',
        'category': 'Supplement'
    },
    {
        'medicine': 'Vitamin C 500mg',
        'timing': 'With or after food',
        'dosage': '1 tablet once or twice daily',
        'age_restriction': 'All ages',
        'instructions': 'Antioxidant, immunity booster. Take with meals.',
        'precautions': 'Excess excreted in urine. High doses may cause diarrhea, kidney stones.',
        'category': 'Vitamin'
    },
    {
        'medicine': 'Zinc Sulfate 20mg',
        'timing': '1 hour before or 2 hours after food',
        'dosage': '1 tablet once daily',
        'age_restriction': 'All ages (dose varies)',
        'instructions': 'For immunity, wound healing, skin. Empty stomach preferred.',
        'precautions': 'May cause nausea on empty stomach (take with small snack if needed). Do not exceed dose.',
        'category': 'Mineral'
    },
    {
        'medicine': 'Vitamin E 400 IU',
        'timing': 'With fatty meal',
        'dosage': '1 capsule once daily',
        'age_restriction': 'Adults',
        'instructions': 'Fat-soluble antioxidant. Take with meal containing fat.',
        'precautions': 'High doses increase bleeding risk. Not proven for most health claims.',
        'category': 'Vitamin'
    },
    {
        'medicine': 'Folic Acid 5mg',
        'timing': 'With or without food',
        'dosage': '1 tablet once daily',
        'age_restriction': 'All ages (especially pregnancy)',
        'instructions': 'For folate deficiency, pregnancy. Essential for fetal development.',
        'precautions': 'Masks B12 deficiency. Very safe.',
        'category': 'Vitamin'
    },
    {
        'medicine': 'Magnesium Oxide 400mg',
        'timing': 'With food',
        'dosage': '1 tablet once or twice daily',
        'age_restriction': 'Adults',
        'instructions': 'For magnesium deficiency, constipation, muscle cramps.',
        'precautions': 'Causes diarrhea at high doses. Space apart from antibiotics.',
        'category': 'Mineral'
    },
    {
        'medicine': 'Probiotics (Lactobacillus)',
        'timing': '2 hours before or after antibiotics',
        'dosage': '1 capsule 1-2 times daily',
        'age_restriction': 'All ages',
        'instructions': 'For gut health, especially during/after antibiotics. Space apart from antibiotics.',
        'precautions': 'Refrigerate some formulations. Generally very safe.',
        'category': 'Probiotic'
    },
    
    # Gynecology (8)
    {
        'medicine': 'Mifepristone 200mg + Misoprostol 200mcg',
        'timing': 'As per medical protocol',
        'dosage': 'Prescription-only medical abortion protocol',
        'age_restriction': 'Women of reproductive age',
        'instructions': 'Medical abortion. Strict medical supervision required. Mifepristone first, misoprostol 24-48 hours later.',
        'precautions': 'Prescription only. Heavy bleeding expected. Follow-up mandatory. Not for home use without supervision.',
        'category': 'Gynecology'
    },
    {
        'medicine': 'Oral Contraceptive Pill (Combined)',
        'timing': 'Same time every day',
        'dosage': '1 pill daily for 21 days, then 7-day break',
        'age_restriction': 'Women of reproductive age',
        'instructions': 'Birth control pill. Must be taken at the same time daily for effectiveness.',
        'precautions': 'Not for smokers over 35, blood clot risk. Reduces effectiveness with certain antibiotics.',
        'category': 'Contraceptive'
    },
    {
        'medicine': 'Progesterone-Only Pill (Mini Pill)',
        'timing': 'Same time every day (strict)',
        'dosage': '1 pill daily continuously (no break)',
        'age_restriction': 'Women of reproductive age',
        'instructions': 'Contraceptive for those who cannot take estrogen. Timing very critical (within 3-hour window).',
        'precautions': 'Less effective if not taken at same time. May cause irregular bleeding.',
        'category': 'Contraceptive'
    },
    {
        'medicine': 'Tranexamic Acid 500mg',
        'timing': 'With or without food',
        'dosage': '1 tablet 3 times daily during heavy menstruation',
        'age_restriction': 'Women of reproductive age',
        'instructions': 'Reduces heavy menstrual bleeding. Take only during periods, not continuously.',
        'precautions': 'Do not use if history of blood clots. Maximum 5 days per cycle.',
        'category': 'Gynecology'
    },
    {
        'medicine': 'Mefenamic Acid 500mg',
        'timing': 'After food',
        'dosage': '1 tablet 3 times daily during periods',
        'age_restriction': 'Adults and adolescents',
        'instructions': 'For menstrual pain. Take only during periods, maximum 7 days.',
        'precautions': 'Must be taken with food. Do not exceed 7 days.',
        'category': 'Gynecology'
    },
    {
        'medicine': 'Norethisterone 5mg',
        'timing': 'Same time daily',
        'dosage': '1 tablet 3 times daily to delay periods',
        'age_restriction': 'Women of reproductive age',
        'instructions': 'To delay menstruation. Start 3 days before expected period, continue until desired.',
        'precautions': 'Period starts 2-3 days after stopping. May cause nausea, breast tenderness.',
        'category': 'Gynecology'
    },
    {
        'medicine': 'Clomiphene Citrate 50mg',
        'timing': 'Same time daily',
        'dosage': '1 tablet daily for 5 days (cycle day 2-6 or 5-9)',
        'age_restriction': 'Women with infertility',
        'instructions': 'Ovulation induction. Strict medical supervision. Specific cycle days.',
        'precautions': 'Prescription only. Increases multiple pregnancy risk. Monitor with ultrasound.',
        'category': 'Fertility'
    },
    {
        'medicine': 'Emergency Contraceptive Pill (Levonorgestrel 1.5mg)',
        'timing': 'As soon as possible after unprotected intercourse',
        'dosage': '1 tablet single dose (effective up to 72 hours)',
        'age_restriction': 'Women of reproductive age',
        'instructions': 'Emergency contraception. Take as soon as possible (within 72 hours, ideally 24 hours).',
        'precautions': 'Not for regular contraception. May cause nausea, irregular bleeding. Does not terminate pregnancy.',
        'category': 'Contraceptive'
    },
    
    # Urology (6)
    {
        'medicine': 'Tamsulosin 0.4mg',
        'timing': '30 minutes after same meal daily',
        'dosage': '1 capsule once daily',
        'age_restriction': 'Adult men only',
        'instructions': 'For enlarged prostate (BPH). Take 30 minutes after breakfast or dinner, but same meal daily.',
        'precautions': 'May cause dizziness, orthostatic hypotension. Inform surgeon before cataract surgery. First-dose effect.',
        'category': 'Urology'
    },
    {
        'medicine': 'Sildenafil 50mg',
        'timing': '1 hour before sexual activity',
        'dosage': '1 tablet as needed, maximum once daily',
        'age_restriction': 'Adult men only',
        'instructions': 'For erectile dysfunction. Take 1 hour before activity. Effective for 4-6 hours.',
        'precautions': 'Contraindicated with nitrates (causes dangerous blood pressure drop). May cause headache, flushing.',
        'category': 'Erectile Dysfunction'
    },
    {
        'medicine': 'Tadalafil 10mg',
        'timing': '30 minutes before sexual activity OR daily',
        'dosage': '1 tablet as needed, or daily low dose (2.5-5mg)',
        'age_restriction': 'Adult men only',
        'instructions': 'For erectile dysfunction and BPH. Long-acting (up to 36 hours). Can be taken daily at low dose.',
        'precautions': 'Contraindicated with nitrates. Avoid grapefruit juice. May cause back pain.',
        'category': 'Erectile Dysfunction'
    },
    {
        'medicine': 'Alfuzosin 10mg',
        'timing': 'After same meal daily',
        'dosage': '1 tablet once daily',
        'age_restriction': 'Adult men only',
        'instructions': 'For BPH. Take after meal (breakfast or dinner) at same time daily.',
        'precautions': 'Similar to tamsulosin. Dizziness, low blood pressure.',
        'category': 'Urology'
    },

    
    # Allergy/Skin
    {
        'medicine': 'Hydroxyzine 25mg',
        'timing': 'At night before bedtime',
        'dosage': '1 tablet once or twice daily',
        'age_restriction': 'All ages (dose varies)',
        'instructions': 'Antihistamine for itching, urticaria. Causes drowsiness (good for night).',
        'precautions': 'Very sedating. Do not drive. Avoid alcohol.',
        'category': 'Antihistamine'
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
