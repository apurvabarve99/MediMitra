==MediMitra ReadMe Notes by Aishwarya, Apurva and Vivek==

Requirements are specified in requirements.txt. Just

pip install -r requirements.txt

The DB Schema and seed data is in the file database/init_db.py. Run below once to initialize DB schema and seed data.
python database/schema_and_seed.sql. Initial implementation is in AWS RDS PostGres server. 
Publicly Accessible: Yes, Inbound rule on host IP granted. Backup retained for 24 hours. 
To initialize the RAG embeddings ONLY for the first time, run the below command

python scripts/seed_symptom_mappings.py
python scripts/seed_medicine_instructions.py


To run the app, below command:

streamlit run app.py


**IMPORTANT NOTICE
In a production medical environment, We would transition from public API endpoints to Private Inference Endpoints (VPC) to ensure data stays within a secure perimeter.
We have used Python 3.13 as PaddleOCR didn't have wheels for version 3.14.