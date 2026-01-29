import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.db_connection import DatabaseConnection
from backend.rag_service import rag_service
import json


# Symptom to specialist mappings
SYMPTOM_MAPPINGS = [
    # Cardiology (15 entries)
    {
        'symptoms': 'chest pain, shortness of breath, palpitations, rapid heartbeat, dizziness',
        'specialists': ['Cardiologist', 'General Medicine'],
        'severity': 'high'
    },
    {
        'symptoms': 'high blood pressure, hypertension, chest discomfort',
        'specialists': ['Cardiologist', 'General Medicine'],
        'severity': 'high'
    },
    {
        'symptoms': 'irregular heartbeat, arrhythmia, heart racing, skipped beats',
        'specialists': ['Cardiologist', 'General Medicine'],
        'severity': 'high'
    },
    {
        'symptoms': 'leg swelling, ankle edema, fluid retention, puffy feet',
        'specialists': ['Cardiologist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'heart murmur, abnormal heart sounds, valve problems',
        'specialists': ['Cardiologist'],
        'severity': 'high'
    },
    {
        'symptoms': 'fainting, syncope, loss of consciousness, lightheadedness',
        'specialists': ['Cardiologist', 'Neurologist', 'General Medicine'],
        'severity': 'high'
    },
    {
        'symptoms': 'chest tightness, angina, pressure in chest, squeezing sensation',
        'specialists': ['Cardiologist', 'General Medicine'],
        'severity': 'high'
    },
    {
        'symptoms': 'slow heartbeat, bradycardia, weak pulse',
        'specialists': ['Cardiologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'rapid pulse, tachycardia, fast heart rate over 100',
        'specialists': ['Cardiologist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'cold extremities, cold hands and feet, poor circulation',
        'specialists': ['Cardiologist', 'Vascular Surgeon'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'blue lips, cyanosis, bluish skin, oxygen deficiency',
        'specialists': ['Cardiologist', 'Pulmonologist'],
        'severity': 'high'
    },
    {
        'symptoms': 'heart attack symptoms, left arm pain, jaw pain, sweating',
        'specialists': ['Cardiologist', 'Emergency Medicine'],
        'severity': 'high'
    },
    {
        'symptoms': 'varicose veins, leg vein problems, bulging veins',
        'specialists': ['Vascular Surgeon', 'Cardiologist'],
        'severity': 'low'
    },
    {
        'symptoms': 'deep vein thrombosis, DVT, leg pain, leg swelling',
        'specialists': ['Vascular Surgeon', 'Cardiologist'],
        'severity': 'high'
    },
    {
        'symptoms': 'peripheral artery disease, PAD, leg cramping while walking',
        'specialists': ['Vascular Surgeon', 'Cardiologist'],
        'severity': 'moderate'
    },
    
    # Pulmonology (10 entries)
    {
        'symptoms': 'breathing difficulty, asthma, wheezing, persistent cough',
        'specialists': ['Pulmonologist', 'General Medicine'],
        'severity': 'high'
    },
    {
        'symptoms': 'chronic cough, persistent cough for weeks, dry cough',
        'specialists': ['Pulmonologist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'coughing blood, hemoptysis, blood in sputum',
        'specialists': ['Pulmonologist', 'General Medicine'],
        'severity': 'high'
    },
    {
        'symptoms': 'lung infection, pneumonia, chest congestion, productive cough',
        'specialists': ['Pulmonologist', 'General Medicine'],
        'severity': 'high'
    },
    {
        'symptoms': 'COPD, chronic bronchitis, emphysema, smoking-related lung disease',
        'specialists': ['Pulmonologist'],
        'severity': 'high'
    },
    {
        'symptoms': 'shortness of breath on exertion, dyspnea, breathlessness',
        'specialists': ['Pulmonologist', 'Cardiologist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'sleep apnea, snoring, daytime sleepiness, breathing pauses',
        'specialists': ['Pulmonologist', 'ENT Specialist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'tuberculosis symptoms, TB, night sweats, weight loss, chronic cough',
        'specialists': ['Pulmonologist', 'Infectious Disease'],
        'severity': 'high'
    },
    {
        'symptoms': 'pulmonary embolism, sudden breathlessness, chest pain',
        'specialists': ['Pulmonologist', 'Cardiologist'],
        'severity': 'high'
    },
    {
        'symptoms': 'lung nodule, lung mass, abnormal chest x-ray',
        'specialists': ['Pulmonologist', 'Oncologist'],
        'severity': 'moderate'
    },
    
    # Gastroenterology (12 entries)
    {
        'symptoms': 'stomach pain, abdominal cramps, nausea, vomiting, diarrhea, indigestion',
        'specialists': ['Gastroenterologist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'acid reflux, GERD, heartburn, chest burning sensation',
        'specialists': ['Gastroenterologist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'constipation, difficulty passing stools, bloating',
        'specialists': ['Gastroenterologist', 'General Medicine'],
        'severity': 'low'
    },
    {
        'symptoms': 'blood in stool, rectal bleeding, dark stools, melena',
        'specialists': ['Gastroenterologist', 'General Medicine'],
        'severity': 'high'
    },
    {
        'symptoms': 'jaundice, yellow skin, yellow eyes, dark urine',
        'specialists': ['Gastroenterologist', 'Hepatologist'],
        'severity': 'high'
    },
    {
        'symptoms': 'liver disease, hepatitis, elevated liver enzymes',
        'specialists': ['Gastroenterologist', 'Hepatologist'],
        'severity': 'high'
    },
    {
        'symptoms': 'irritable bowel syndrome, IBS, alternating diarrhea and constipation',
        'specialists': ['Gastroenterologist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'inflammatory bowel disease, IBD, Crohns disease, ulcerative colitis',
        'specialists': ['Gastroenterologist'],
        'severity': 'high'
    },
    {
        'symptoms': 'gallstones, gallbladder pain, upper right abdominal pain',
        'specialists': ['Gastroenterologist', 'General Surgeon'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'pancreatitis, severe upper abdominal pain, pancreas inflammation',
        'specialists': ['Gastroenterologist', 'General Medicine'],
        'severity': 'high'
    },
    {
        'symptoms': 'peptic ulcer, stomach ulcer, burning stomach pain',
        'specialists': ['Gastroenterologist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'hemorrhoids, piles, anal pain, rectal discomfort',
        'specialists': ['Gastroenterologist', 'General Surgeon'],
        'severity': 'low'
    },
    
    # Neurology (12 entries)
    {
        'symptoms': 'severe headache, migraine, vision problems, sensitivity to light',
        'specialists': ['Neurologist', 'General Medicine'],
        'severity': 'high'
    },
    {
        'symptoms': 'dizziness, vertigo, spinning sensation, balance problems',
        'specialists': ['Neurologist', 'ENT Specialist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'seizures, epilepsy, convulsions, loss of consciousness',
        'specialists': ['Neurologist'],
        'severity': 'high'
    },
    {
        'symptoms': 'tremors, shaking, involuntary movements, Parkinsons symptoms',
        'specialists': ['Neurologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'numbness, tingling, pins and needles, limb weakness',
        'specialists': ['Neurologist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'memory loss, forgetfulness, cognitive decline, confusion',
        'specialists': ['Neurologist', 'Geriatrics'],
        'severity': 'high'
    },
    {
        'symptoms': 'stroke symptoms, facial drooping, arm weakness, speech difficulty',
        'specialists': ['Neurologist', 'Emergency Medicine'],
        'severity': 'high'
    },
    {
        'symptoms': 'muscle weakness, paralysis, difficulty moving limbs',
        'specialists': ['Neurologist', 'General Medicine'],
        'severity': 'high'
    },
    {
        'symptoms': 'nerve pain, neuropathy, burning pain in extremities',
        'specialists': ['Neurologist', 'Endocrinologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'multiple sclerosis symptoms, MS, vision changes, coordination problems',
        'specialists': ['Neurologist'],
        'severity': 'high'
    },
    {
        'symptoms': 'dementia, Alzheimers disease, progressive memory loss',
        'specialists': ['Neurologist', 'Geriatrics'],
        'severity': 'high'
    },
    {
        'symptoms': 'cluster headaches, severe one-sided headache, eye pain',
        'specialists': ['Neurologist', 'General Medicine'],
        'severity': 'high'
    },
    
    # Orthopedics (12 entries)
    {
        'symptoms': 'joint pain, swelling, stiffness, arthritis, muscle pain',
        'specialists': ['Orthopedic', 'Rheumatologist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'back pain, lower back pain, sciatica, neck pain, spinal issues',
        'specialists': ['Orthopedic', 'Neurologist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'knee pain, knee injury, knee swelling, difficulty walking',
        'specialists': ['Orthopedic', 'Sports Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'shoulder pain, rotator cuff injury, frozen shoulder',
        'specialists': ['Orthopedic', 'Sports Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'fracture, broken bone, bone injury, trauma',
        'specialists': ['Orthopedic', 'Trauma Surgery'],
        'severity': 'high'
    },
    {
        'symptoms': 'sprain, ligament injury, ankle twist, joint instability',
        'specialists': ['Orthopedic', 'Sports Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'sports injury, muscle tear, athletic injury',
        'specialists': ['Orthopedic', 'Sports Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'hip pain, hip arthritis, difficulty walking, groin pain',
        'specialists': ['Orthopedic', 'Rheumatologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'carpal tunnel syndrome, wrist pain, hand numbness',
        'specialists': ['Orthopedic', 'Neurologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'tennis elbow, elbow pain, lateral epicondylitis',
        'specialists': ['Orthopedic', 'Sports Medicine'],
        'severity': 'low'
    },
    {
        'symptoms': 'plantar fasciitis, heel pain, foot arch pain',
        'specialists': ['Orthopedic', 'Podiatrist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'osteoporosis, bone weakness, increased fracture risk',
        'specialists': ['Orthopedic', 'Endocrinologist'],
        'severity': 'moderate'
    },
    
    # Dermatology (10 entries)
    {
        'symptoms': 'skin rash, itching, redness, swelling, hives, eczema',
        'specialists': ['Dermatologist', 'General Medicine'],
        'severity': 'low'
    },
    {
        'symptoms': 'acne, pimples, blackheads, whiteheads, oily skin',
        'specialists': ['Dermatologist'],
        'severity': 'low'
    },
    {
        'symptoms': 'eczema, atopic dermatitis, dry skin, itchy patches',
        'specialists': ['Dermatologist', 'Allergist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'psoriasis, scaly patches, silvery scales, red plaques',
        'specialists': ['Dermatologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'hair loss, alopecia, baldness, thinning hair',
        'specialists': ['Dermatologist', 'Endocrinologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'nail problems, nail fungus, discolored nails, brittle nails',
        'specialists': ['Dermatologist'],
        'severity': 'low'
    },
    {
        'symptoms': 'skin infection, cellulitis, bacterial skin infection',
        'specialists': ['Dermatologist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'fungal infection, ringworm, athletes foot, jock itch',
        'specialists': ['Dermatologist', 'General Medicine'],
        'severity': 'low'
    },
    {
        'symptoms': 'mole changes, skin lesion, suspicious skin growth',
        'specialists': ['Dermatologist', 'Oncologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'vitiligo, skin depigmentation, white patches on skin',
        'specialists': ['Dermatologist'],
        'severity': 'low'
    },
    
    # General Medicine (10 entries)
    {
        'symptoms': 'fever, high temperature, pyrexia, chills',
        'specialists': ['General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'cough, persistent cough, dry cough, mucus production',
        'specialists': ['General Medicine', 'Pulmonologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'cold, runny nose, nasal congestion, sneezing',
        'specialists': ['General Medicine'],
        'severity': 'low'
    },
    {
        'symptoms': 'sore throat, throat pain, difficulty swallowing',
        'specialists': ['General Medicine', 'ENT Specialist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'body ache, muscle pain, generalized pain, malaise',
        'specialists': ['General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'fatigue, tiredness, exhaustion, lack of energy',
        'specialists': ['General Medicine', 'Endocrinologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'weight loss, unexplained weight loss, loss of appetite',
        'specialists': ['General Medicine', 'Oncologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'night sweats, excessive sweating, drenching sweats',
        'specialists': ['General Medicine', 'Infectious Disease'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'flu symptoms, influenza, body aches, fever, cough',
        'specialists': ['General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'dehydration, excessive thirst, dry mouth, dark urine',
        'specialists': ['General Medicine'],
        'severity': 'moderate'
    },
    
    # Endocrinology (8 entries)
    {
        'symptoms': 'diabetes, high blood sugar, frequent urination, excessive thirst',
        'specialists': ['Endocrinologist', 'General Medicine'],
        'severity': 'high'
    },
    {
        'symptoms': 'thyroid problems, weight changes, fatigue, hair loss',
        'specialists': ['Endocrinologist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'hyperthyroidism, weight loss, rapid heartbeat, anxiety, sweating',
        'specialists': ['Endocrinologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'hypothyroidism, weight gain, fatigue, cold intolerance, depression',
        'specialists': ['Endocrinologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'hormonal imbalance, irregular periods, mood swings, acne',
        'specialists': ['Endocrinologist', 'Gynecologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'obesity, weight management, difficulty losing weight',
        'specialists': ['Endocrinologist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'adrenal insufficiency, Addisons disease, fatigue, low blood pressure',
        'specialists': ['Endocrinologist'],
        'severity': 'high'
    },
    {
        'symptoms': 'growth hormone problems, short stature, delayed puberty',
        'specialists': ['Endocrinologist', 'Pediatrics'],
        'severity': 'moderate'
    },
    
    # Urology & Nephrology (10 entries)
    {
        'symptoms': 'kidney pain, urinary problems, blood in urine, frequent urination',
        'specialists': ['Nephrologist', 'Urologist', 'General Medicine'],
        'severity': 'high'
    },
    {
        'symptoms': 'kidney stones, renal calculi, severe flank pain',
        'specialists': ['Urologist', 'Nephrologist'],
        'severity': 'high'
    },
    {
        'symptoms': 'urinary tract infection, UTI, burning urination, urgency',
        'specialists': ['Urologist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'urinary incontinence, leaking urine, bladder control problems',
        'specialists': ['Urologist', 'Gynecologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'prostate problems, enlarged prostate, difficulty urinating',
        'specialists': ['Urologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'kidney disease, chronic kidney disease, elevated creatinine',
        'specialists': ['Nephrologist'],
        'severity': 'high'
    },
    {
        'symptoms': 'kidney failure, renal failure, need for dialysis',
        'specialists': ['Nephrologist'],
        'severity': 'high'
    },
    {
        'symptoms': 'protein in urine, proteinuria, foamy urine',
        'specialists': ['Nephrologist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'erectile dysfunction, ED, male sexual problems',
        'specialists': ['Urologist', 'Endocrinologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'testicular pain, scrotal swelling, testicular mass',
        'specialists': ['Urologist'],
        'severity': 'high'
    },
    
    # ENT (8 entries)
    {
        'symptoms': 'ear pain, hearing loss, tinnitus, vertigo, balance problems',
        'specialists': ['ENT Specialist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'hearing loss, deafness, difficulty hearing',
        'specialists': ['ENT Specialist', 'Audiologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'tinnitus, ringing in ears, buzzing sounds',
        'specialists': ['ENT Specialist', 'Neurologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'throat infection, pharyngitis, tonsillitis, swollen tonsils',
        'specialists': ['ENT Specialist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'sinus infection, sinusitis, facial pain, nasal discharge',
        'specialists': ['ENT Specialist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'nasal congestion, blocked nose, stuffy nose, nasal polyps',
        'specialists': ['ENT Specialist'],
        'severity': 'low'
    },
    {
        'symptoms': 'nosebleed, epistaxis, frequent nose bleeding',
        'specialists': ['ENT Specialist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'voice problems, hoarseness, vocal cord issues, laryngitis',
        'specialists': ['ENT Specialist'],
        'severity': 'moderate'
    },
    
    # Ophthalmology (8 entries)
    {
        'symptoms': 'eye pain, blurred vision, redness, discharge, vision loss',
        'specialists': ['Ophthalmologist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'blurred vision, vision problems, difficulty seeing',
        'specialists': ['Ophthalmologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'eye redness, red eyes, bloodshot eyes, conjunctivitis',
        'specialists': ['Ophthalmologist', 'General Medicine'],
        'severity': 'low'
    },
    {
        'symptoms': 'cataracts, cloudy vision, difficulty seeing at night',
        'specialists': ['Ophthalmologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'glaucoma, increased eye pressure, peripheral vision loss',
        'specialists': ['Ophthalmologist'],
        'severity': 'high'
    },
    {
        'symptoms': 'dry eyes, eye irritation, gritty feeling, burning eyes',
        'specialists': ['Ophthalmologist'],
        'severity': 'low'
    },
    {
        'symptoms': 'diabetic retinopathy, vision changes with diabetes',
        'specialists': ['Ophthalmologist', 'Endocrinologist'],
        'severity': 'high'
    },
    {
        'symptoms': 'sudden vision loss, blind spot, retinal detachment',
        'specialists': ['Ophthalmologist', 'Emergency Medicine'],
        'severity': 'high'
    },
    
    # Psychiatry (8 entries)
    {
        'symptoms': 'anxiety, panic attacks, excessive worry, nervousness',
        'specialists': ['Psychiatrist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'depression, sadness, low mood, loss of interest, suicidal thoughts',
        'specialists': ['Psychiatrist', 'General Medicine'],
        'severity': 'high'
    },
    {
        'symptoms': 'stress, overwhelming stress, burnout, emotional distress',
        'specialists': ['Psychiatrist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'sleep disorders, insomnia, difficulty sleeping, nightmares',
        'specialists': ['Psychiatrist', 'Neurologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'behavioral issues, mood swings, anger management problems',
        'specialists': ['Psychiatrist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'OCD, obsessive thoughts, compulsive behaviors, repetitive actions',
        'specialists': ['Psychiatrist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'bipolar disorder, manic episodes, extreme mood swings',
        'specialists': ['Psychiatrist'],
        'severity': 'high'
    },
    {
        'symptoms': 'PTSD, post-traumatic stress, flashbacks, nightmares',
        'specialists': ['Psychiatrist'],
        'severity': 'high'
    },
    
    # Gynecology (8 entries)
    {
        'symptoms': 'pregnancy care, prenatal care, expecting baby',
        'specialists': ['Gynecologist', 'Obstetrician'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'menstrual problems, irregular periods, heavy bleeding, missed periods',
        'specialists': ['Gynecologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'pelvic pain, lower abdominal pain, ovarian pain',
        'specialists': ['Gynecologist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'PCOS, polycystic ovary syndrome, irregular periods, acne, weight gain',
        'specialists': ['Gynecologist', 'Endocrinologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'menopause symptoms, hot flashes, night sweats, mood changes',
        'specialists': ['Gynecologist', 'Endocrinologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'infertility, difficulty getting pregnant, unable to conceive',
        'specialists': ['Gynecologist', 'Reproductive Endocrinologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'vaginal discharge, unusual discharge, vaginal infection',
        'specialists': ['Gynecologist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'endometriosis, severe period pain, pelvic pain',
        'specialists': ['Gynecologist'],
        'severity': 'high'
    },
    
    # Rheumatology (6 entries)
    {
        'symptoms': 'rheumatoid arthritis, joint inflammation, morning stiffness, swollen joints',
        'specialists': ['Rheumatologist', 'Orthopedic'],
        'severity': 'high'
    },
    {
        'symptoms': 'lupus, SLE, autoimmune disease, butterfly rash, joint pain',
        'specialists': ['Rheumatologist'],
        'severity': 'high'
    },
    {
        'symptoms': 'gout, gouty arthritis, big toe pain, joint redness',
        'specialists': ['Rheumatologist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'fibromyalgia, widespread pain, chronic fatigue, tender points',
        'specialists': ['Rheumatologist', 'Pain Management'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'ankylosing spondylitis, spinal arthritis, back stiffness',
        'specialists': ['Rheumatologist', 'Orthopedic'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'polymyalgia rheumatica, shoulder pain, hip pain, morning stiffness',
        'specialists': ['Rheumatologist'],
        'severity': 'moderate'
    },
    
    # Oncology (6 entries)
    {
        'symptoms': 'cancer screening, cancer checkup, family history of cancer',
        'specialists': ['Oncologist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'tumor, mass evaluation, lump, abnormal growth',
        'specialists': ['Oncologist', 'General Surgery'],
        'severity': 'high'
    },
    {
        'symptoms': 'breast lump, breast mass, breast changes',
        'specialists': ['Oncologist', 'Breast Surgeon'],
        'severity': 'high'
    },
    {
        'symptoms': 'unexplained weight loss, loss of appetite, night sweats',
        'specialists': ['Oncologist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'persistent fatigue, anemia, easy bruising',
        'specialists': ['Oncologist', 'Hematologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'lymph node swelling, enlarged lymph nodes, lymphadenopathy',
        'specialists': ['Oncologist', 'Hematologist', 'General Medicine'],
        'severity': 'moderate'
    },
    
    # Pediatrics (6 entries)
    {
        'symptoms': 'child fever, pediatric fever, high temperature in child',
        'specialists': ['Pediatrics', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'child growth problems, short stature, delayed development',
        'specialists': ['Pediatrics', 'Endocrinologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'childhood vaccinations, immunizations, vaccine schedule',
        'specialists': ['Pediatrics'],
        'severity': 'low'
    },
    {
        'symptoms': 'newborn care, infant feeding problems, baby health',
        'specialists': ['Pediatrics', 'Neonatologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'child behavioral problems, ADHD, learning difficulties',
        'specialists': ['Pediatrics', 'Child Psychiatrist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'childhood asthma, wheezing in child, breathing difficulty',
        'specialists': ['Pediatrics', 'Pulmonologist'],
        'severity': 'moderate'
    },
    
    # Infectious Disease (5 entries)
    {
        'symptoms': 'HIV care, AIDS treatment, HIV positive',
        'specialists': ['Infectious Disease'],
        'severity': 'high'
    },
    {
        'symptoms': 'hepatitis, liver infection, viral hepatitis',
        'specialists': ['Infectious Disease', 'Gastroenterologist'],
        'severity': 'high'
    },
    {
        'symptoms': 'tropical infections, malaria, dengue, typhoid',
        'specialists': ['Infectious Disease', 'General Medicine'],
        'severity': 'high'
    },
    {
        'symptoms': 'recurrent infections, frequent illnesses, weak immune system',
        'specialists': ['Infectious Disease', 'Immunologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'sepsis, blood infection, severe infection, high fever with confusion',
        'specialists': ['Infectious Disease', 'Critical Care'],
        'severity': 'high'
    },
    
    # Allergist (4 entries)
    {
        'symptoms': 'allergies, allergic reactions, seasonal allergies, hay fever',
        'specialists': ['Allergist', 'General Medicine'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'food allergies, food intolerance, allergic reaction to food',
        'specialists': ['Allergist', 'Gastroenterologist'],
        'severity': 'moderate'
    },
    {
        'symptoms': 'anaphylaxis, severe allergic reaction, difficulty breathing, swelling',
        'specialists': ['Allergist', 'Emergency Medicine'],
        'severity': 'high'
    },
    {
        'symptoms': 'chronic hives, urticaria, persistent itching, skin welts',
        'specialists': ['Allergist', 'Dermatologist'],
        'severity': 'moderate'
    },
]


def seed_symptom_embeddings():
    """Seed symptom mappings with embeddings into PGVector"""
    
    try:
        with DatabaseConnection.get_connection() as conn:
            cur = conn.cursor()
            
            print(f"\nSeeding {len(SYMPTOM_MAPPINGS)} symptom mappings...")
            
            for idx, mapping in enumerate(SYMPTOM_MAPPINGS, 1):
                symptoms = mapping['symptoms']
                
                # Generate embedding using rag_service
                print(f"{idx}. Embedding: {symptoms[:50]}...")
                embedding = rag_service.create_embedding(symptoms)
                
                if not embedding:
                    print(f"❌ Failed to create embedding for: {symptoms[:50]}...")
                    continue
                
                # Prepare metadata
                metadata = {
                    'specialists': mapping['specialists'],
                    'severity': mapping['severity']
                }
                
                # Insert into database
                insert_query = """
                    INSERT INTO document_embeddings 
                    (content, embedding, metadata, doc_type)
                    VALUES (%s, %s::vector, %s, %s)
                """
                
                cur.execute(insert_query, (
                    symptoms,
                    embedding,
                    json.dumps(metadata),
                    'symptom_mapping'
                ))
            
            print(f"\n✅ Successfully seeded {len(SYMPTOM_MAPPINGS)} symptom mappings!")
            
            # Verify
            cur.execute("SELECT COUNT(*) FROM document_embeddings WHERE doc_type = 'symptom_mapping'")
            count = cur.fetchone()[0]
            print(f"✅ Total symptom mappings in database: {count}")
            
            cur.close()
        
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        raise


if __name__ == "__main__":
    seed_symptom_embeddings()