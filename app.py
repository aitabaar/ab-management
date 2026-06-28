
import os, re, csv, io, base64, threading, hashlib, hmac, secrets
from datetime import datetime
from html import escape
from pathlib import Path
import qrcode
from io import BytesIO
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = os.environ.get("DATABASE_URL")
PORT = os.environ.get("PORT", "8000")
APP_NAME = "AB Management Web"
ROLE_NAMES = ["Super Admin", "Hospital Admin", "Reception User", "Lab/Result User", "Limited User", "Custom Role"]
PERMISSIONS = [
    ("create_slip", "Create Slip", "Patients"),
    ("edit_slip", "Edit Slip", "Patients"),
    ("delete_slip", "Delete Slip", "Patients"),
    ("change_panel", "Change Panel", "Patients"),
    ("view_patients", "View Patients", "Patients"),
    ("edit_patients", "Edit Patients", "Patients"),
    ("enter_result", "Enter Result", "Results"),
    ("edit_result", "Edit Result", "Results"),
    ("verify_result", "Verify Result", "Results"),
    ("view_report", "View Report", "Reports"),
    ("print_report", "Print Report", "Reports"),
    ("billing", "Billing", "Billing"),
    ("panel_rates", "Panel/Rates Management", "Admin"),
    ("test_master", "Test Master", "Admin"),
    ("user_management", "User Management", "Admin"),
    ("hospital_management", "Hospital Management", "Admin"),
    ("dashboard", "Dashboard Access", "Dashboard"),
]
ROLE_DEFAULTS = {
    "Super Admin": [p[0] for p in PERMISSIONS],
    "Hospital Admin": [p[0] for p in PERMISSIONS if p[0] != "hospital_management"],
    "Reception User": ["dashboard", "create_slip", "edit_slip", "change_panel", "view_patients", "edit_patients", "view_report", "print_report", "billing"],
    "Lab/Result User": ["dashboard", "view_patients", "enter_result", "edit_result", "verify_result", "view_report", "print_report"],
    "Limited User": ["dashboard", "view_patients", "view_report"],
    "Custom Role": [],
}
TEST_FORMATS = {'CBC': [('Hemoglobin', 'g/dL', '11.5 - 16.5'), ('RBC Count', '10^12/L', '4.0 - 5.5'), ('HCT / PCV', '%', '36 - 48'), ('MCV', 'fL', '76 - 96'), ('MCH', 'pg', '27 - 32'), ('MCHC', 'g/dL', '30 - 35'), ('WBC Count', '10^9/L', '4.0 - 11.0'), ('Neutrophils', '%', '40 - 75'), ('Lymphocytes', '%', '20 - 45'), ('Eosinophils', '%', '1 - 6'), ('Monocytes', '%', '2 - 10'), ('Basophils', '%', '0 - 1'), ('Platelets', '10^9/L', '150 - 400'), ('ESR', 'mm/hr', '0 - 20')], 'Blood Group': [('ABO Group', '', ''), ('Rh Factor', '', '')], 'Blood Sugar Random': [('Random Blood Sugar', 'mg/dL', '70 - 140')], 'Blood Sugar Fasting': [('Fasting Blood Sugar', 'mg/dL', '70 - 110')], 'Blood Sugar PP': [('Post Prandial Sugar', 'mg/dL', '70 - 160')], 'HbA1c': [('HbA1c', '%', 'Normal <5.7; Prediabetes 5.7 - 6.4; Diabetes >=6.5')], 'LFT': [('Bilirubin Total (BT)', 'mg/dL', '0.2 - 1.2'), ('Bilirubin Direct (BD)', 'mg/dL', '0.0 - 0.3'), ('ALT / SGPT', 'U/L', '0 - 45'), ('Gamma GT (GGT)', 'U/L', '9 - 48'), ('Alkaline Phosphatase (ALP)', 'U/L', '44 - 147')], 'RFT': [('Urea', 'mg/dL', '10 - 50'), ('Creatinine', 'mg/dL', '0.5 - 1.3'), ('Uric Acid', 'mg/dL', '3.4 - 7.0'), ('BUN', 'mg/dL', '7 - 20')], 'Uric Acid': [('Uric Acid', 'mg/dL', '3.4 - 7.0')], 'SGPT': [('ALT / SGPT', 'U/L', '0 - 45')], 'SGOT': [('AST / SGOT', 'U/L', '0 - 40')], 'Creatinine': [('Creatinine', 'mg/dL', '0.5 - 1.3')], 'Urea': [('Urea', 'mg/dL', '10 - 50')], 'Electrolytes': [('Sodium', 'mEq/L', '136 - 145'), ('Potassium', 'mEq/L', '3.5 - 5.1'), ('Chloride', 'mEq/L', '98 - 107')], 'Lipid Profile': [('Total Cholesterol', 'mg/dL', '100 - 200'), ('Triglycerides', 'mg/dL', '35 - 150'), ('HDL Cholesterol', 'mg/dL', '40 - 60'), ('LDL Cholesterol', 'mg/dL', '0 - 130'), ('VLDL', 'mg/dL', '5 - 40'), ('Cholesterol/HDL Ratio', '', '0 - 5')], 'Urine DR': [('Quantity', '', ''), ('Colour', '', ''), ('Appearance', '', ''), ('Specific Gravity', '', '1.005 - 1.030'), ('pH', '', '4.5 - 8.0'), ('Protein', '', 'NIL'), ('Glucose', '', 'NIL'), ('Ketones', '', 'NIL'), ('Bile Pigments', '', 'NIL'), ('Urobilinogen', '', 'Normal'), ('RBC', '/HPF', '0 - 2'), ('WBC', '/HPF', '0 - 5'), ('Epithelial Cells', '/HPF', 'Few'), ('Crystals', '', 'Not Seen'), ('Bacteria', '', 'Not Seen'), ('Casts', '', 'Not Seen')], 'Stool DR': [('Colour', '', ''), ('Consistency', '', ''), ('Mucus', '', 'Absent'), ('Blood', '', 'Absent'), ('Occult Blood', '', 'Negative'), ('Ova / Cyst', '', 'Not Seen'), ('RBC', '/HPF', '0 - 2'), ('Pus Cells', '/HPF', '0 - 2'), ('Epithelial Cells', '/HPF', 'Few'), ('Undigested Food Particles', '', 'Absent'), ('Bacteria', '', 'Normal flora')], 'Typhidot': [('Typhidot IgM', '', 'NEGATIVE'), ('Typhidot IgG', '', 'NEGATIVE')], 'Widal Test': [('S. Typhi O', '', 'Less than 1:80'), ('S. Typhi H', '', 'Less than 1:80'), ('S. Paratyphi AH', '', 'Less than 1:80'), ('S. Paratyphi BH', '', 'Less than 1:80')], 'Dengue NS1': [('Dengue NS1 Antigen', '', 'NEGATIVE')], 'Dengue IgG/IgM': [('Dengue IgM', '', 'NEGATIVE'), ('Dengue IgG', '', 'NEGATIVE')], 'Malaria Parasite': [('Malarial Parasite', '', 'Not Seen')], 'Malarial Parasite': [('Malarial Parasite', '', 'Not Seen')], 'HCV': [('Anti HCV', '', 'NON-REACTIVE')], 'HBsAg': [('HBsAg', '', 'NON-REACTIVE')], 'HIV': [('HIV I & II', '', 'NON-REACTIVE')], 'Pregnancy Test': [('Urine Pregnancy Test', '', 'NEGATIVE')], 'CRP': [('C-Reactive Protein', 'mg/L', '0 - 6')], 'RA Factor': [('RA Factor', 'IU/mL', '0 - 14')], 'ASO Titre': [('ASO Titre', 'IU/mL', '0 - 200')], 'Troponin I': [('Troponin I', '', 'NEGATIVE')], 'TSH': [('TSH', 'uIU/mL', '0.4 - 4.0')], 'T3': [('T3', 'ng/mL', '0.8 - 2.0')], 'T4': [('T4', 'ug/dL', '5.0 - 12.0')], 'Thyroid Profile': [('T3', 'ng/mL', '0.8 - 2.0'), ('T4', 'ug/dL', '5.0 - 12.0'), ('TSH', 'uIU/mL', '0.4 - 4.0')], 'PT / INR': [('Prothrombin Time', 'sec', '11 - 16'), ('Control', 'sec', ''), ('INR', '', '0.8 - 1.2')], 'BT / CT': [('Bleeding Time', 'min', '1 - 6'), ('Clotting Time', 'min', '5 - 11')], 'Peripheral Smear': [('RBC Morphology', '', ''), ('WBC Morphology', '', ''), ('Platelet Morphology', '', '')], 'Reticulocyte Count': [('Reticulocyte Count', '%', '0.5 - 2.5')], 'FSH': [('FSH', 'mIU/mL', '')], 'LH': [('LH', 'mIU/mL', '')], 'Prolactin': [('Prolactin', 'ng/mL', '')], 'Beta HCG': [('Beta HCG', 'mIU/mL', 'Non-pregnant <5; Pregnancy: interpret clinically')], 'Testosterone': [('Testosterone', 'ng/dL', '')], 'Progesterone': [('Progesterone', 'ng/mL', '')], 'Estradiol': [('Estradiol', 'pg/mL', '')], 'ANA': [('ANA', '', 'NEGATIVE')], 'Anti dsDNA': [('Anti dsDNA', 'IU/mL', '')], 'C3': [('C3', 'mg/dL', '90 - 180')], 'C4': [('C4', 'mg/dL', '10 - 40')], 'Vitamin D': [('25-Hydroxy Vitamin D', 'ng/mL', 'Deficient <20; Insufficient 20 - 29; Sufficient 30 - 100')], 'Vitamin D3': [('25-Hydroxy Vitamin D', 'ng/mL', 'Deficient <20; Insufficient 20 - 29; Sufficient 30 - 100')], 'Vitamin B12': [('Vitamin B12 (Cobalamin)', 'pg/mL', '200 - 900')], 'Hemoglobin': [('Hemoglobin', 'g/dL', '11.5 - 16.5')], 'ESR': [('ESR', 'mm/hr', '0 - 20')], 'Platelet Count': [('Platelets', '10^9/L', '150 - 400')], 'TLC': [('Total Leukocyte Count', '10^9/L', '4.0 - 11.0')], 'DLC': [('Neutrophils', '%', '40 - 75'), ('Lymphocytes', '%', '20 - 45'), ('Eosinophils', '%', '1 - 6'), ('Monocytes', '%', '2 - 10'), ('Basophils', '%', '0 - 1')], 'APTT': [('APTT', 'sec', '25 - 35'), ('Control', 'sec', '')], 'FBS': [('Fasting Blood Sugar', 'mg/dL', '70 - 110')], 'RBS': [('Random Blood Sugar', 'mg/dL', '70 - 140')], 'PPBS': [('Post Prandial Sugar', 'mg/dL', '70 - 160')], 'BUN': [('Blood Urea Nitrogen', 'mg/dL', '7 - 20')], 'Calcium': [('Calcium', 'mg/dL', '8.5 - 10.5')], 'Phosphorus': [('Phosphorus', 'mg/dL', '2.5 - 4.5')], 'Magnesium': [('Magnesium', 'mg/dL', '1.6 - 2.6')], 'Albumin': [('Albumin', 'g/dL', '3.5 - 5.2')], 'Total Protein': [('Total Protein', 'g/dL', '6.0 - 8.3')], 'Amylase': [('Amylase', 'U/L', '30 - 110')], 'Lipase': [('Lipase', 'U/L', '13 - 60')], 'CPK': [('Creatine Phosphokinase', 'U/L', '24 - 195')], 'CK-MB': [('CK-MB', 'U/L', '0 - 25')], 'LDH': [('LDH', 'U/L', '140 - 280')], 'Iron': [('Serum Iron', 'ug/dL', '60 - 170')], 'TIBC': [('TIBC', 'ug/dL', '240 - 450')], 'Ferritin': [('Ferritin', 'ng/mL', '30 - 400')], 'FT3': [('Free T3', 'pg/mL', '2.0 - 4.4')], 'FT4': [('Free T4', 'ng/dL', '0.8 - 1.8')], 'Anti HCV': [('Anti HCV', '', 'NON-REACTIVE')], 'HBsAg ICT': [('HBsAg', '', 'NON-REACTIVE')], 'H. Pylori': [('H. Pylori', '', 'NEGATIVE')], 'VDRL': [('VDRL', '', 'NON-REACTIVE')], 'TPHA': [('TPHA', '', 'NON-REACTIVE')], 'COVID-19 Antigen': [('COVID-19 Antigen', '', 'NEGATIVE')], 'MP ICT': [('P. Falciparum', '', 'NEGATIVE'), ('P. Vivax', '', 'NEGATIVE')], 'MP Slide': [('Malarial Parasite', '', 'Not Seen')], 'Microfilaria': [('Microfilaria', '', 'NOT SEEN')], 'Leishmania': [('Leishmania Donovan Bodies', '', 'NOT SEEN')], 'AMH': [('Anti Mullerian Hormone (AMH)', 'ng/mL', '')], 'Insulin Fasting': [('Fasting Insulin', 'uIU/mL', '2.6 - 24.9')], 'Insulin Random': [('Random Insulin', 'uIU/mL', '')], 'C-Peptide': [('C-Peptide', 'ng/mL', '0.8 - 3.1')], 'Cortisol': [('Cortisol', 'ug/dL', '')], 'PTH': [('Parathyroid Hormone', 'pg/mL', '15 - 65')], 'PSA Total': [('PSA Total', 'ng/mL', '0 - 4')], 'PSA Free': [('PSA Free', 'ng/mL', '')], 'CEA': [('CEA', 'ng/mL', '0 - 5')], 'AFP': [('AFP', 'ng/mL', '0 - 10')], 'CA-125': [('CA-125', 'U/mL', '0 - 35')], 'CA 15-3': [('CA 15-3', 'U/mL', '0 - 31')], 'CA 19-9': [('CA 19-9', 'U/mL', '0 - 37')], 'D-Dimer': [('D-Dimer', 'ng/mL', '<500')], 'Fibrinogen': [('Fibrinogen', 'mg/dL', '200 - 400')], 'Direct Coombs Test': [('Direct Coombs Test', '', 'NEGATIVE')], 'Indirect Coombs Test': [('Indirect Coombs Test', '', 'NEGATIVE')], 'Hb Electrophoresis': [('Hb A', '%', ''), ('Hb A2', '%', ''), ('Hb F', '%', '')], 'G6PD': [('G6PD', 'U/g Hb', '')], 'Serum Lithium': [('Serum Lithium', 'mmol/L', '0.6 - 1.2')], 'Sodium': [('Sodium', 'mEq/L', '136 - 145')], 'Potassium': [('Potassium', 'mEq/L', '3.5 - 5.1')], 'Chloride': [('Chloride', 'mEq/L', '98 - 107')], 'Bicarbonate': [('Bicarbonate', 'mEq/L', '22 - 29')], 'Bilirubin Total': [('Bilirubin Total', 'mg/dL', '0.2 - 1.2')], 'Bilirubin Direct': [('Bilirubin Direct', 'mg/dL', '0.0 - 0.3')], 'Alkaline Phosphatase': [('Alkaline Phosphatase', 'U/L', '44 - 147')], 'GGT': [('Gamma GT', 'U/L', '9 - 48')], 'Troponin T': [('Troponin T', '', 'NEGATIVE')], 'NT-proBNP': [('NT-proBNP', 'pg/mL', '')], 'Rubella IgG': [('Rubella IgG', 'IU/mL', '')], 'Rubella IgM': [('Rubella IgM', '', 'NEGATIVE')], 'Toxoplasma IgG': [('Toxoplasma IgG', 'IU/mL', '')], 'Toxoplasma IgM': [('Toxoplasma IgM', '', 'NEGATIVE')], 'CMV IgG': [('CMV IgG', 'IU/mL', '')], 'CMV IgM': [('CMV IgM', '', 'NEGATIVE')], 'HSV IgG': [('HSV IgG', '', '')], 'HSV IgM': [('HSV IgM', '', 'NEGATIVE')], 'HBeAg': [('HBeAg', '', 'NON-REACTIVE')], 'Anti HBs': [('Anti HBs', 'mIU/mL', '')], 'Anti HBc Total': [('Anti HBc Total', '', 'NON-REACTIVE')], 'Urine Culture': [('Culture', '', ''), ('Colony Count', 'CFU/mL', ''), ('Antibiotic Sensitivity', '', '')], 'Blood Culture': [('Culture', '', ''), ('Organism', '', ''), ('Antibiotic Sensitivity', '', '')], 'Semen Analysis': [('Volume', 'mL', ''), ('Count', 'million/mL', ''), ('Motility', '%', ''), ('Morphology', '%', '')]}
TEST_PRICES = {'CBC': 900, 'Blood Group': 300, 'Blood Sugar Random': 200, 'Blood Sugar Fasting': 200, 'Blood Sugar PP': 200, 'HbA1c': 1200, 'LFT': 1400, 'RFT': 1200, 'Uric Acid': 350, 'SGPT': 350, 'SGOT': 350, 'Creatinine': 350, 'Urea': 350, 'Electrolytes': 1000, 'Lipid Profile': 1400, 'Urine DR': 400, 'Stool DR': 500, 'Typhidot': 900, 'Widal Test': 700, 'Dengue NS1': 1200, 'Dengue IgG/IgM': 1500, 'Malaria Parasite': 400, 'Malarial Parasite': 400, 'HCV': 700, 'HBsAg': 700, 'HIV': 900, 'Pregnancy Test': 350, 'CRP': 700, 'RA Factor': 700, 'ASO Titre': 700, 'Troponin I': 1800, 'TSH': 1000, 'T3': 900, 'T4': 900, 'Vitamin D': 2200, 'Vitamin D3': 2200, 'Vitamin B12': 1800, 'Thyroid Profile': 2400, 'PT / INR': 800, 'BT / CT': 500, 'Peripheral Smear': 500, 'Reticulocyte Count': 600, 'FSH': 1400, 'LH': 1400, 'Prolactin': 1400, 'Beta HCG': 1400, 'Testosterone': 1800, 'Progesterone': 1800, 'Estradiol': 1800, 'ANA': 2200, 'Anti dsDNA': 2500, 'C3': 1800, 'C4': 1800, 'Hemoglobin': 250, 'ESR': 250, 'Platelet Count': 350, 'TLC': 300, 'DLC': 300, 'APTT': 800, 'FBS': 200, 'RBS': 200, 'PPBS': 200, 'BUN': 350, 'Calcium': 500, 'Phosphorus': 500, 'Magnesium': 700, 'Albumin': 400, 'Total Protein': 500, 'Amylase': 900, 'Lipase': 1200, 'CPK': 1000, 'CK-MB': 1200, 'LDH': 900, 'Iron': 900, 'TIBC': 900, 'Ferritin': 1800, 'FT3': 1000, 'FT4': 1000, 'Anti HCV': 700, 'HBsAg ICT': 700, 'H. Pylori': 800, 'VDRL': 600, 'TPHA': 1000, 'COVID-19 Antigen': 1200, 'MP ICT': 800, 'MP Slide': 400, 'Microfilaria': 500, 'Leishmania': 700, 'AMH': 3500, 'Insulin Fasting': 1500, 'Insulin Random': 1500, 'C-Peptide': 2500, 'Cortisol': 1800, 'PTH': 3000, 'PSA Total': 1800, 'PSA Free': 1800, 'CEA': 2200, 'AFP': 2200, 'CA-125': 2800, 'CA 15-3': 2800, 'CA 19-9': 2800, 'D-Dimer': 2500, 'Fibrinogen': 1800, 'Direct Coombs Test': 1200, 'Indirect Coombs Test': 1200, 'Hb Electrophoresis': 3500, 'G6PD': 2000, 'Serum Lithium': 1800, 'Sodium': 350, 'Potassium': 350, 'Chloride': 350, 'Bicarbonate': 500, 'Bilirubin Total': 350, 'Bilirubin Direct': 350, 'Alkaline Phosphatase': 500, 'GGT': 600, 'Troponin T': 1800, 'NT-proBNP': 4500, 'Rubella IgG': 2530, 'Rubella IgM': 2530, 'Toxoplasma IgG': 2000, 'Toxoplasma IgM': 2000, 'CMV IgG': 2000, 'CMV IgM': 2000, 'HSV IgG': 2000, 'HSV IgM': 2000, 'HBeAg': 1200, 'Anti HBs': 1800, 'Anti HBc Total': 1800, 'Urine Culture': 900, 'Blood Culture': 2500, 'Semen Analysis': 1500}

app = FastAPI(title=APP_NAME)
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("AB_WEB_SECRET", "change-this-secret-before-online"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

def money(value):
    try: return f"{float(value):,.0f}"
    except Exception: return "0"
templates.env.filters["money"] = money

def now_str(): return datetime.now().strftime("%d-%m-%Y %I:%M %p")
def today_str(): return datetime.now().strftime("%d-%m-%Y")

def generate_qr_code(data):
    """Generate QR code as base64 encoded PNG image"""
    try:
        from PIL import Image
        qr = qrcode.QRCode(version=1, box_size=3, border=1)
        qr.add_data(str(data))
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        qr_b64 = base64.b64encode(img_bytes.getvalue()).decode()
        return f"data:image/png;base64,{qr_b64}"
    except Exception as e:
        print(f"QR Code Error: {e}")
        return ""

def norm_result(value):
    value=str(value or '').strip()
    if not value: return ''
    if re.fullmatch(r"[<>]=?\s*[-+]?\d+(?:[.,]\d+)?(?:\s*[-â€“]\s*[-+]?\d+(?:[.,]\d+)?)?", value): return value.replace(',', '.')
    # CBC machine values: 7,600 -> 7.6 ; 400,000 -> 400
    if re.fullmatch(r"\d{1,3},\d{3}", value):
        try: return str(int(value.replace(',',''))/1000).rstrip('0').rstrip('.')
        except Exception: pass
    return re.sub(r"\s+", " ", value).upper()

def normalize_title(value):
    raw=str(value or '').strip(); key=raw.lower().replace('.','')
    return {'mr':'Mr.','mrs':'Mrs.','miss':'Miss','ms':'Ms.','baby':'Baby','dr':'Dr.'}.get(key, raw[:1].upper()+raw[1:] if raw else '')
def gender_for_title(value):
    key=str(value or '').strip().lower().replace('.','')
    if key=='mr': return 'Male'
    if key in {'mrs','miss','ms'}: return 'Female'
    return ''

def get_department_for_test(test_name):
    bio={"Blood Sugar Random","Blood Sugar Fasting","Blood Sugar PP","FBS","RBS","PPBS","LFT","RFT","Uric Acid","SGPT","SGOT","Creatinine","Urea","BUN","Electrolytes","Lipid Profile","Calcium","Phosphorus","Magnesium","Albumin","Total Protein","Amylase","Lipase","CPK","CK-MB","LDH","Iron","TIBC","Ferritin","Sodium","Potassium","Chloride","Bicarbonate","Bilirubin Total","Bilirubin Direct","Alkaline Phosphatase","GGT","Serum Lithium"}
    special={"HbA1c","Vitamin D","Vitamin D3","Vitamin B12"}
    thyroid={"TSH","T3","T4","FT3","FT4","Thyroid Profile"}
    hormones={"FSH","LH","Prolactin","Beta HCG","Testosterone","Progesterone","Estradiol","AMH","Insulin Fasting","Insulin Random","C-Peptide","Cortisol","PTH"}
    immunology={"ANA","Anti dsDNA","C3","C4","CRP","RA Factor","ASO Titre","Rubella IgG","Rubella IgM","Toxoplasma IgG","Toxoplasma IgM","CMV IgG","CMV IgM","HSV IgG","HSV IgM"}
    serology={"Typhidot","Widal Test","Dengue NS1","Dengue IgG/IgM","HCV","Anti HCV","HBsAg","HBsAg ICT","HIV","Troponin I","Troponin T","NT-proBNP","Pregnancy Test","H. Pylori","VDRL","TPHA","COVID-19 Antigen","HBeAg","Anti HBs","Anti HBc Total"}
    haema={"CBC","Blood Group","PT / INR","APTT","BT / CT","Peripheral Smear","Reticulocyte Count","Hemoglobin","ESR","Platelet Count","TLC","DLC","Malaria Parasite","Malarial Parasite","MP Slide","D-Dimer","Fibrinogen","Direct Coombs Test","Indirect Coombs Test","Hb Electrophoresis","G6PD"}
    cultures={"Urine Culture","Blood Culture"}; tumour={"PSA Total","PSA Free","CEA","AFP","CA-125","CA 15-3","CA 19-9"}
    if test_name in haema: return "HAEMATOLOGY"
    if test_name in bio: return "BIOCHEMISTRY"
    if test_name in special: return "SPECIAL CHEMISTRY"
    if test_name in thyroid: return "THYROID PROFILE"
    if test_name in hormones: return "HORMONES"
    if test_name in immunology: return "IMMUNOLOGY"
    if test_name in serology: return "SEROLOGY"
    if test_name == "Urine DR": return "URINE EXAMINATION"
    if test_name == "Stool DR": return "STOOL EXAMINATION"
    if test_name in {"MP ICT","Microfilaria","Leishmania"}: return "PARASITOLOGY"
    if test_name in cultures: return "MICROBIOLOGY"
    if test_name in tumour: return "TUMOUR MARKERS"
    if test_name == "Semen Analysis": return "ANDROLOGY"
    return "LABORATORY"

class PgConn:
    def __init__(self, url):
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError("Install psycopg first: pip install -r requirements.txt") from exc
        self._con = psycopg.connect(url, row_factory=dict_row, connect_timeout=10)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self._con.close()

    def _translate(self, sql):
        sql = sql.replace("IFNULL(", "COALESCE(")
        sql = sql.replace("INSERT OR IGNORE INTO", "INSERT INTO")
        sql = sql.replace("INSERT OR REPLACE INTO", "INSERT INTO")
        sql = re.sub(r"DATE\(([^)]+)\)", r"to_date(\1::text, 'DD-MM-YYYY')", sql)
        return sql.replace("?", "%s")

    def execute(self, sql, params=()):
        sql = self._translate(sql)
        if sql.lstrip().upper().startswith("INSERT INTO"):
            sql = self._add_conflict_clause(sql)
        return self._con.execute(sql, params)

    def _add_conflict_clause(self, sql):
        upper = sql.upper()
        if " ON CONFLICT " in upper:
            return sql
        conflict_rules = {
            "USERS": "(username) DO UPDATE SET password=excluded.password, role=excluded.role",
            "PATIENTS": "(lab_no) DO NOTHING",
            "TEST_MASTER": "(test_name) DO UPDATE SET department=excluded.department, price=excluded.price, status=excluded.status, report_mode=excluded.report_mode, report_heading=excluded.report_heading, report_group=excluded.report_group",
            "PANEL_NAMES": "(hospital_id,name) DO NOTHING",
            "PANEL_TEST_RATES": "(hospital_id,panel_name,test_name) DO UPDATE SET price=excluded.price",
            "RESULT_TEMPLATES": "(text) DO NOTHING",
            "APP_SETTINGS": "(setting_key) DO UPDATE SET setting_value=excluded.setting_value",
            "DOCTORS": "(name) DO NOTHING",
        }
        match = re.match(r"\s*INSERT\s+INTO\s+([a-zA-Z_][\w]*)", sql, flags=re.I)
        if not match:
            return sql
        table = match.group(1).upper()
        rule = conflict_rules.get(table)
        if not rule:
            return sql
        return f"{sql} ON CONFLICT {rule}"

    def commit(self):
        self._con.commit()

    def close(self):
        self._con.close()


def db_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is required. Set it to the Supabase PostgreSQL connection string.")
    return PgConn(DATABASE_URL)

def _schema_statements(sql_text):
    statements=[]
    current=[]
    for line in sql_text.splitlines():
        stripped=line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(current).rstrip(";"))
            current=[]
    if current:
        statements.append("\n".join(current))
    return statements

def seed_default_data(cur):
    cur.execute("INSERT INTO hospitals(name,code,status,created_at) VALUES('AB Management','ABM','ACTIVE',?) ON CONFLICT (name) DO NOTHING",(now_str(),))
    default_hospital = cur.execute("SELECT id FROM hospitals WHERE name='AB Management'").fetchone()
    default_hospital_id = default_hospital['id'] if default_hospital else None
    for role in ROLE_NAMES:
        cur.execute("INSERT INTO roles(name,description,is_system,created_at) VALUES(?,?,true,?) ON CONFLICT (name) DO NOTHING",(role,role,now_str()))
    for key,label,category in PERMISSIONS:
        cur.execute("INSERT INTO permissions(permission_key,label,category) VALUES(?,?,?) ON CONFLICT (permission_key) DO NOTHING",(key,label,category))
    for role, perms in ROLE_DEFAULTS.items():
        role_row = cur.execute("SELECT id FROM roles WHERE name=?",(role,)).fetchone()
        if role_row:
            for perm in perms:
                cur.execute("INSERT INTO role_permissions(role_id,permission_key) VALUES(?,?) ON CONFLICT (role_id,permission_key) DO NOTHING",(role_row['id'],perm))
    for username,password,role in [('syedali','Ali@0312','Admin'),('aliabdi','12345','Reception'),('rizwanyounus','12345','Lab Technician'),('admin','admin123','Admin')]:
        cur.execute("INSERT INTO users(username,password,password_hash,role,is_active,created_at) VALUES(?,?,?,?,true,?) ON CONFLICT (username) DO NOTHING",(username,'',hash_password(password),role,now_str()))
    for u in cur.execute("SELECT id,password FROM users WHERE COALESCE(password_hash,'')='' AND COALESCE(password,'')<>''").fetchall():
        cur.execute("UPDATE users SET password_hash=?, password='', updated_at=? WHERE id=?",(hash_password(u['password']),now_str(),u['id']))
    super_role = cur.execute("SELECT id FROM roles WHERE name='Super Admin'").fetchone()
    if super_role:
        cur.execute("UPDATE users SET role='Super Admin', role_id=?, is_active=true WHERE role='Admin' OR username IN ('admin','syedali')",(super_role['id'],))
    role_map = {'Reception':'Reception User','Lab Technician':'Lab/Result User'}
    for old_role,new_role in role_map.items():
        rr = cur.execute("SELECT id FROM roles WHERE name=?",(new_role,)).fetchone()
        if rr:
            cur.execute("UPDATE users SET role=?, role_id=?, is_active=true WHERE role=?",(new_role,rr['id'],old_role))
    for user_row in cur.execute("SELECT id FROM users WHERE role='Super Admin'").fetchall():
        if default_hospital_id:
            cur.execute("INSERT INTO user_hospitals(user_id,hospital_id) VALUES(?,?) ON CONFLICT (user_id,hospital_id) DO NOTHING",(user_row['id'],default_hospital_id))
    for panel in ['Self','Eshal Medical','Dua Clinic','Lady Rafat Hospital']:
        cur.execute("INSERT INTO panel_names(name,status,hospital_id) VALUES(?,'ACTIVE',?) ON CONFLICT (hospital_id,name) DO NOTHING",(panel,default_hospital_id))
    for key,val in {'lab_name':'AB LAB','lab_subtitle':'Laboratory & Diagnostic Centre','lab_address':'','lab_phone':'','report_footer_note':'This is a computer generated report therefore does not require any signature.'}.items():
        cur.execute("INSERT INTO app_settings(setting_key,setting_value) VALUES(?,?) ON CONFLICT (setting_key) DO NOTHING",(key,val))
    for key,val in {
        'report_header_space_px':'145',
        'report_footer_space_px':'190',
        'report_content_width_px':'720',
        'report_logo_path':'',
        'report_header_image_path':'',
        'report_footer_image_path':'',
    }.items():
        cur.execute("INSERT INTO app_settings(setting_key,setting_value) VALUES(?,?) ON CONFLICT (setting_key) DO NOTHING",(key,val))
    test_count = cur.execute("SELECT COUNT(*) c FROM test_master").fetchone()['c']
    if test_count == 0:
        for test,price in TEST_PRICES.items():
            dept=get_department_for_test(test)
            cur.execute("INSERT INTO test_master(test_name,department,price,status,report_mode,report_heading) VALUES(?,?,?,'ACTIVE','AUTO',?) ON CONFLICT (test_name) DO NOTHING",(test,dept,float(price or 0),dept))
            for i,item in enumerate(TEST_FORMATS.get(test,[(test,'','')]),1):
                param,unit,ref=item
                cur.execute("INSERT INTO test_parameters(test_name,parameter,unit,reference_range,sort_order) VALUES(?,?,?,?,?)",(test,param,unit,ref,i))
    rate_count = cur.execute("SELECT COUNT(*) c FROM panel_test_rates").fetchone()['c']
    if rate_count == 0:
        for panel in [r['name'] for r in cur.execute("SELECT name FROM panel_names")]:
            for test,price in TEST_PRICES.items():
                cur.execute("INSERT INTO panel_test_rates(hospital_id,panel_name,test_name,price) VALUES(?,?,?,?) ON CONFLICT (hospital_id,panel_name,test_name) DO NOTHING",(default_hospital_id,panel,test,float(price or 0)))
    cur.execute("UPDATE test_master SET report_group='VITAMINS', report_heading='VITAMINS' WHERE test_name IN ('Vitamin B12','Vitamin D','Vitamin D3') AND COALESCE(TRIM(report_group),'')=''")
    cur.execute("UPDATE test_master SET report_group='HBA1C', report_heading='HBA1C' WHERE test_name='HbA1c' AND COALESCE(TRIM(report_group),'')=''")
    default_templates = [
        ('MORPHOLOGY', 'NCN', 'Normocytic Normochromic'),
        ('MORPHOLOGY', 'MCH', 'Microcytic Hypochromic'),
        ('MORPHOLOGY', 'MAC', 'Macrocytic'),
        ('MORPHOLOGY', 'DIM', 'Dimorphic Picture'),
        ('REMARKS', 'NL', 'Within Normal Limits'),
        ('REMARKS', 'IDA', 'Iron deficiency anemia, Advise Serum Iron Profile.'),
        ('REMARKS', 'MA', 'Mild anemia present.'),
        ('REMARKS', 'LCO', 'Leukocytosis present.'),
        ('REMARKS', 'THR', 'Thrombocytopenia present.'),
    ]
    for ttype, shortcut, text in default_templates:
        cur.execute("INSERT INTO result_templates(template_type,shortcut,text) VALUES(?,?,?) ON CONFLICT (text) DO NOTHING",(ttype,shortcut,text))
    if default_hospital_id:
        for table in ["patients","patient_tests","test_results","panel_names","panel_test_rates","expenses","doctors","daily_patients","report_logs"]:
            cur.execute(f"UPDATE {table} SET hospital_id=? WHERE hospital_id IS NULL",(default_hospital_id,))

def ensure_database_schema():
    schema_path = BASE_DIR / "supabase_schema.sql"
    with db_conn() as con:
        for statement in _schema_statements(schema_path.read_text(encoding="utf-8")):
            con.execute(statement)
        con.execute('ALTER TABLE patients ADD COLUMN IF NOT EXISTS ref_by text DEFAULT \'\'')
        con.execute('ALTER TABLE patients ADD COLUMN IF NOT EXISTS panel_name text DEFAULT \'Self\'')
        con.execute('ALTER TABLE patient_tests ADD COLUMN IF NOT EXISTS status text DEFAULT \'PENDING\'')
        con.execute('ALTER TABLE patient_tests ADD COLUMN IF NOT EXISTS result_entered_at text')
        con.execute('ALTER TABLE test_results ADD COLUMN IF NOT EXISTS morphology text')
        con.execute('ALTER TABLE test_results ADD COLUMN IF NOT EXISTS remarks text')
        con.execute('ALTER TABLE test_master ADD COLUMN IF NOT EXISTS report_mode text DEFAULT \'AUTO\'')
        con.execute('ALTER TABLE test_master ADD COLUMN IF NOT EXISTS report_heading text DEFAULT \'\'')
        con.execute('ALTER TABLE test_master ADD COLUMN IF NOT EXISTS report_group text DEFAULT \'\'')
        con.execute('ALTER TABLE report_logs ADD COLUMN IF NOT EXISTS department text')
        con.execute('ALTER TABLE report_logs ADD COLUMN IF NOT EXISTS "user" text')
        con.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash text')
        con.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name text')
        con.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS role_id bigint')
        con.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active boolean DEFAULT true')
        con.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS must_change_password boolean DEFAULT false')
        con.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at text')
        con.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at text')
        con.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at text')
        for table in ["patients","patient_tests","test_results","panel_names","panel_test_rates","expenses","doctors","daily_patients","report_logs"]:
            con.execute(f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS hospital_id bigint')
        con.execute('ALTER TABLE patients ADD COLUMN IF NOT EXISTS created_by bigint')
        con.execute('ALTER TABLE patients ADD COLUMN IF NOT EXISTS updated_by bigint')
        con.execute('ALTER TABLE patients ADD COLUMN IF NOT EXISTS deleted_by bigint')
        con.execute('ALTER TABLE patients ADD COLUMN IF NOT EXISTS deleted_at text')
        con.execute('ALTER TABLE patient_tests ADD COLUMN IF NOT EXISTS created_by bigint')
        con.execute('ALTER TABLE patient_tests ADD COLUMN IF NOT EXISTS updated_by bigint')
        con.execute('ALTER TABLE test_results ADD COLUMN IF NOT EXISTS entered_by bigint')
        con.execute('ALTER TABLE test_results ADD COLUMN IF NOT EXISTS updated_by bigint')
        con.execute('ALTER TABLE test_results ADD COLUMN IF NOT EXISTS verified_by bigint')
        con.execute('ALTER TABLE test_results ADD COLUMN IF NOT EXISTS verified_at text')
        con.execute('ALTER TABLE panel_names DROP CONSTRAINT IF EXISTS panel_names_name_key')
        con.execute('ALTER TABLE panel_test_rates DROP CONSTRAINT IF EXISTS panel_test_rates_panel_name_test_name_key')
        con.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_panel_names_hospital_name ON panel_names(hospital_id, name)')
        con.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_panel_rates_hospital_panel_test ON panel_test_rates(hospital_id, panel_name, test_name)')
        seed_default_data(con)
        con.commit()

@app.on_event("startup")
def start_schema_check():
    def run():
        try:
            ensure_database_schema()
            print("Database schema check completed.")
        except Exception as exc:
            print(f"Database schema check failed: {exc}")
    threading.Thread(target=run, daemon=True).start()

def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", str(password).encode("utf-8"), salt.encode("utf-8"), 260000).hex()
    return f"pbkdf2_sha256${salt}${digest}"

def verify_password(password, stored):
    stored = str(stored or "")
    if stored.startswith("pbkdf2_sha256$"):
        try:
            _, salt, digest = stored.split("$", 2)
            check = hashlib.pbkdf2_hmac("sha256", str(password).encode("utf-8"), salt.encode("utf-8"), 260000).hex()
            return hmac.compare_digest(check, digest)
        except Exception:
            return False
    return hmac.compare_digest(str(password), stored)

def password_error(password, confirm=None):
    if confirm is not None and password != confirm:
        return "New password and confirm password must match."
    if len(str(password or "")) < 6:
        return "Password must be at least 6 characters."
    return ""

def current_user(request): return request.session.get('user')
def user_id(request): return (current_user(request) or {}).get('id')
def is_super_admin(request): return (current_user(request) or {}).get('role') == 'Super Admin'
def user_permissions(request): return set((current_user(request) or {}).get('permissions') or [])
def user_hospital_ids(request): return [int(x) for x in ((current_user(request) or {}).get('hospital_ids') or [])]
def current_hospital_id(request):
    ids = user_hospital_ids(request)
    selected = (current_user(request) or {}).get('current_hospital_id')
    if selected and (is_super_admin(request) or int(selected) in ids):
        return int(selected)
    return ids[0] if ids else None
def has_permission(request, permission):
    return is_super_admin(request) or permission in user_permissions(request)
def access_denied():
    return HTMLResponse("Access denied", status_code=403)
def require_permission(request, permission):
    red = require_login(request)
    if red: return red
    if not has_permission(request, permission):
        return HTMLResponse("Access denied", status_code=403)
def require_login(request):
    if not current_user(request): return RedirectResponse('/login',status_code=303)
def is_admin(request): return (current_user(request) or {}).get('role') in {'Admin','Super Admin','Hospital Admin'}
def require_admin(request):
    red=require_login(request)
    if red: return red
    if not (is_admin(request) or has_permission(request,'user_management')): return HTMLResponse("Admin access required", status_code=403)
def hospital_clause(request, alias=''):
    if is_super_admin(request):
        return "", []
    ids = user_hospital_ids(request)
    if not ids:
        return " AND 1=0", []
    prefix = f"{alias}." if alias else ""
    return f" AND {prefix}hospital_id IN ({','.join(['?']*len(ids))})", ids
def require_patient_access(con, request, lab_no):
    clause, params = hospital_clause(request)
    row = con.execute(f"SELECT * FROM patients WHERE lab_no=?{clause}", [lab_no] + params).fetchone()
    return row
def load_user_context(con, user_row):
    role_name = user_row['role'] or 'Limited User'
    role_row = con.execute("SELECT id,name FROM roles WHERE name=?",(role_name,)).fetchone()
    permissions = set()
    if role_row:
        permissions.update(r['permission_key'] for r in con.execute("SELECT permission_key FROM role_permissions WHERE role_id=?",(role_row['id'],)).fetchall())
    permissions.update(r['permission_key'] for r in con.execute("SELECT permission_key FROM user_permissions WHERE user_id=? AND allowed=true",(user_row['id'],)).fetchall())
    hospital_ids = [r['hospital_id'] for r in con.execute("SELECT hospital_id FROM user_hospitals WHERE user_id=?",(user_row['id'],)).fetchall()]
    if role_name == 'Super Admin' and not hospital_ids:
        hospital_ids = [r['id'] for r in con.execute("SELECT id FROM hospitals WHERE status='ACTIVE' ORDER BY id").fetchall()]
    return {'id':user_row['id'],'username':user_row['username'],'role':role_name,'permissions':sorted(permissions),'hospital_ids':hospital_ids,'current_hospital_id':hospital_ids[0] if hospital_ids else None}
def log_report_action(con, request, lab_no, department='', action='VIEW'):
    user=(current_user(request) or {}).get('username','PUBLIC')
    p=con.execute("SELECT hospital_id FROM patients WHERE lab_no=?",(lab_no,)).fetchone()
    con.execute('INSERT INTO report_logs(hospital_id,lab_no,department,action,"user",created_at) VALUES(?,?,?,?,?,?)',(p['hospital_id'] if p else current_hospital_id(request),lab_no,department or '',action,user,now_str()))
def audit_log(con, request, action, entity_type='', entity_id='', lab_no='', details=''):
    user=current_user(request) or {}
    hid=current_hospital_id(request)
    if lab_no:
        p=con.execute("SELECT hospital_id FROM patients WHERE lab_no=?",(lab_no,)).fetchone()
        if p: hid=p['hospital_id']
    con.execute("INSERT INTO audit_logs(hospital_id,user_id,username,action,entity_type,entity_id,lab_no,details,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(hid,user.get('id'),user.get('username','PUBLIC'),action,entity_type,entity_id,lab_no,details,now_str()))
def is_abnormal_value(result, ref):
    try:
        value=float(str(result).replace(',','.').strip().lstrip('<>').strip())
        nums=[float(x.replace(',','.')) for x in re.findall(r"-?\d+(?:[.,]\d+)?", str(ref or ''))]
        if len(nums) >= 2:
            low, high = nums[0], nums[1]
            return value < low or value > high
    except Exception:
        return False
    return False

def next_lab_no(con):
    row=con.execute("SELECT lab_no FROM patients ORDER BY id DESC LIMIT 1").fetchone()
    if not row: return '0001'
    try: return str(int(str(row['lab_no']).split('-')[-1])+1).zfill(4)
    except Exception: return '0001'

def active_tests(con): return con.execute("SELECT test_name,IFNULL(price,0) price,IFNULL(department,'') department FROM test_master WHERE IFNULL(status,'ACTIVE')='ACTIVE' ORDER BY test_name").fetchall()
def departments(con): return [r['department'] for r in con.execute("SELECT DISTINCT IFNULL(department,'LABORATORY') department FROM test_master WHERE IFNULL(TRIM(department),'')<>'' ORDER BY department").fetchall()]
def test_department(con,test_name):
    row=con.execute("SELECT department FROM test_master WHERE test_name=?",(test_name,)).fetchone(); return row['department'] if row and row['department'] else 'LABORATORY'
def test_report_meta(con,test_name):
    row=con.execute("SELECT department,report_heading,report_group FROM test_master WHERE test_name=?",(test_name,)).fetchone()
    dept=(row['department'] if row and row['department'] else 'LABORATORY')
    group=(row['report_group'] if row and row['report_group'] else '').strip()
    heading=(row['report_heading'] if row and row['report_heading'] else '').strip()
    return {'department':dept,'group':group or dept,'heading':heading or group or dept}
def test_format(con,test_name):
    rows=con.execute("""
        SELECT parameter, unit, reference_range
          FROM test_parameters
         WHERE test_name=?
         ORDER BY sort_order, id
    """,(test_name,)).fetchall()
    unique=[]
    seen=set()
    for row in rows:
        key=(str(row['parameter'] or '').strip(), str(row['unit'] or '').strip(), str(row['reference_range'] or '').strip())
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique or [{'parameter':test_name,'unit':'','reference_range':''}]
def panel_price(con,panel,test,hospital_id=None):
    if hospital_id:
        row=con.execute("SELECT price FROM panel_test_rates WHERE panel_name=? AND test_name=? AND hospital_id=?",(panel,test,hospital_id)).fetchone()
        if row: return float(row['price'] or 0)
    row=con.execute("SELECT price FROM panel_test_rates WHERE panel_name=? AND test_name=?",(panel,test)).fetchone()
    if row: return float(row['price'] or 0)
    row=con.execute("SELECT price FROM test_master WHERE test_name=?",(test,)).fetchone(); return float(row['price'] if row else 0)

def sync_status(con,lab_no):
    booked=[r['test_name'] for r in con.execute("SELECT test_name FROM patient_tests WHERE lab_no=?",(lab_no,)).fetchall()]
    done={r['test_name'] for r in con.execute("SELECT DISTINCT test_name FROM test_results WHERE lab_no=? AND IFNULL(TRIM(result),'')<>'-' AND IFNULL(TRIM(result),'')<>'JS_EMPTY' AND IFNULL(TRIM(result),'')<>''",(lab_no,)).fetchall()}
    status='READY' if booked and all(t in done for t in booked) else ('PARTIAL' if done else 'PENDING')
    con.execute("UPDATE patients SET report_status=?, reporting_date=?, last_updated=? WHERE lab_no=?",(status,now_str() if done else '',now_str(),lab_no))
    con.execute("UPDATE patient_tests SET status='PENDING' WHERE lab_no=?",(lab_no,))
    for t in done: con.execute("UPDATE patient_tests SET status='COMPLETED', result_entered_at=? WHERE lab_no=? AND test_name=?",(now_str(),lab_no,t))
    return status

def render_report_html(con, lab_no, department=None):
    patient=con.execute("SELECT * FROM patients WHERE lab_no=?",(lab_no,)).fetchone()
    if not patient: return ''
    qr_code=generate_qr_code(lab_no)
    rows=con.execute("SELECT * FROM test_results WHERE lab_no=? ORDER BY test_name,id",(lab_no,)).fetchall()
    grouped={}
    notes={}
    for r in rows:
        meta=test_report_meta(con,r['test_name'])
        dept=meta['department']
        if department and dept!=department: continue
        page_key=meta['group']
        key=(page_key,r['test_name'])
        notes.setdefault(key, {'morphology':'', 'remarks':''})
        param=str(r['parameter'] or '').strip().upper()
        if param == 'MORPHOLOGY':
            notes[key]['morphology'] = r['result'] or r['morphology'] or ''
            continue
        if param == 'REMARKS':
            notes[key]['remarks'] = r['result'] or r['remarks'] or ''
            continue
        if r['morphology']: notes[key]['morphology'] = r['morphology']
        if r['remarks']: notes[key]['remarks'] = r['remarks']
        page=grouped.setdefault(page_key,{'heading':meta['heading'],'tests':{}})
        page['tests'].setdefault(r['test_name'],[]).append(r)
    pages=[]
    footer_note=escape(setting(con,'report_footer_note','This is a computer generated report therefore does not require any signature.'))
    header_space=int(float(setting(con,'report_header_space_px','168') or 168))
    content_width=int(float(setting(con,'report_content_width_px','720') or 720))
    footer_space=int(float(setting(con,'report_footer_space_px','120') or 120))
    for page_key,page in grouped.items():
        tests=page['tests']
        page_heading=page['heading']
        body=''
        printed_remarks=False
        for test_name,items in tests.items():
            if len(tests)>1 and len(items)>1:
                body += f"<tr><td colspan='4' class='test-group'>{escape(str(test_name))}</td></tr>"
            for r in items:
                fmt=test_format(con,r['test_name'])
                unit=next((x['unit'] for x in fmt if x['parameter']==r['parameter']),'')
                ref=next((x['reference_range'] for x in fmt if x['parameter']==r['parameter']),'')
                result_class='result abnormal' if is_abnormal_value(r['result'], ref) else 'result'
                body += f"<tr><td>{escape(str(r['parameter']))}</td><td class='{result_class}'><b>{escape(str(r['result'] or ''))}</b></td><td>{escape(str(unit or ''))}</td><td>{escape(str(ref or ''))}</td></tr>"
            note=notes.get((page_key,test_name),{})
            if str(test_name).strip().upper() == 'CBC' and note.get('morphology'):
                body += f"<tr><td colspan='4' class='morphology-row'><b>Morphology :</b>&nbsp; {escape(str(note['morphology']))}</td></tr>"
            if note.get('remarks'):
                printed_remarks=True
                body += f"<tr><td colspan='4' class='remarks-row'><b>Remarks :</b>&nbsp; {escape(str(note['remarks']))}</td></tr>"
        if not printed_remarks:
            body += "<tr><td colspan='4' class='remarks-row blank'><b>Remarks :</b></td></tr>"
        pages.append(f"""
        <section class='print-page a4-report' style='--header-space:{header_space}px; --footer-space:{footer_space}px; --content-width:{content_width}px;'>
          <div class='report-top-space' style='height:{header_space}px;'></div>
          <div class='patient-strip a4-patient-strip'>
            <div class='patient-main'><strong>{escape(str(patient['title'] or ''))} {escape(str(patient['patient_name'] or '')).upper()}</strong><br>Age : {escape(str(patient['age'] or ''))} {escape(str(patient['age_type'] or ''))}<br>Sex : {escape(str(patient['gender'] or ''))}<br>PID : {escape(str(patient['lab_no']))}</div>
            <div class='a4-qr-cell'><img class='a4-inline-qr' src='{qr_code}' alt='QR Code'></div>
            <div><strong>Sample Collected At:</strong><br>{escape(str(patient['booking_date'] or ''))}<br><br><strong>Ref. By:</strong><br>{escape(str(patient['ref_by'] or patient['doctor'] or 'SELF'))}</div>
            <div><strong>Panel</strong><br>{escape(str(patient['panel_name'] or 'SELF'))}<br><br><strong>MR/Ref No</strong><br>{escape(str(patient['ref_by'] or patient['doctor'] or '-'))}</div>
          </div>
          <div class='report-head'><strong>Department of {escape(str(page_heading).title())}</strong><span>Reporting Time:&nbsp;&nbsp;{escape(str(patient['reporting_date'] or ''))}</span></div>
          <table class='report-table a4-results'><thead><tr><th>Test</th><th>Result</th><th>Unit</th><th>Normal Value</th></tr></thead><tbody>{body}</tbody></table>
          <div class='report-note'>{footer_note}</div>
        </section>""")
    return '\n'.join(pages) or "<section class='print-page a4-report'><div class='empty-report'>No results saved yet.</div></section>"


def setting(con,key,default=''):
    row=con.execute("SELECT setting_value FROM app_settings WHERE setting_key=?",(key,)).fetchone(); return row['setting_value'] if row else default


def suggestions(con, template_type):
    return [r['text'] for r in con.execute("SELECT text FROM result_templates WHERE template_type=? ORDER BY id DESC LIMIT 200", (template_type,)).fetchall()]


def remember_suggestion(con, template_type, value):
    value = str(value or '').strip()
    if not value:
        return
    con.execute("INSERT OR IGNORE INTO result_templates(template_type,shortcut,text) VALUES(?,?,?)", (template_type, value[:30], value))

@app.get('/',response_class=HTMLResponse)
def home(request:Request): return templates.TemplateResponse(request,'home.html',{'user':current_user(request)})
@app.get('/login',response_class=HTMLResponse)
def login_page(request:Request): return templates.TemplateResponse(request,'login.html',{'error':''})
@app.post('/login',response_class=HTMLResponse)
def login(request:Request,username:str=Form(...),password:str=Form(...)):
    username=username.strip()
    with db_conn() as con:
        row=con.execute("SELECT * FROM users WHERE username=?",(username,)).fetchone()
        ok = bool(row and row['is_active'] is not False and (verify_password(password,row.get('password_hash')) or verify_password(password,row.get('password'))))
        con.execute("INSERT INTO login_logs(user_id,username,success,ip_address,created_at) VALUES(?,?,?,?,?)",(row['id'] if row else None,username,ok,request.client.host if request.client else '',now_str()))
        if not ok:
            con.commit()
            return templates.TemplateResponse(request,'login.html',{'error':'Invalid username or password'})
        if not row.get('password_hash'):
            con.execute("UPDATE users SET password_hash=?, password='', updated_at=? WHERE id=?",(hash_password(password),now_str(),row['id']))
            row=con.execute("SELECT * FROM users WHERE id=?",(row['id'],)).fetchone()
        con.execute("UPDATE users SET last_login_at=? WHERE id=?",(now_str(),row['id']))
        request.session['user']=load_user_context(con,row)
        audit_log(con,request,'LOGIN','users',str(row['id']),'','')
        con.commit()
    return RedirectResponse('/dashboard',status_code=303)
@app.get('/logout')
def logout(request:Request): request.session.clear(); return RedirectResponse('/login',status_code=303)
@app.get('/public-report',response_class=HTMLResponse)
def public_report_search(request:Request,lab_no:str=''):
    patient=None; html=''; error=''
    lab_no=lab_no.strip()
    if lab_no:
        with db_conn() as con:
            patient=con.execute("SELECT * FROM patients WHERE lab_no=?",(lab_no,)).fetchone()
            if patient:
                html=render_report_html(con,lab_no)
            else:
                error='No report found for this lab number.'
    return templates.TemplateResponse(request,'public_report.html',{'lab_no':lab_no,'patient':patient,'report_html':html,'error':error})
@app.get('/public-report/{lab_no}',response_class=HTMLResponse)
def public_report_by_lab(request:Request,lab_no:str):
    return public_report_search(request,lab_no)
@app.get('/dashboard',response_class=HTMLResponse)
def dashboard(request:Request):
    red=require_permission(request,'dashboard')
    if red: return red
    with db_conn() as con:
        clause, hparams = hospital_clause(request)
        today=today_str(); stats={
            'today_patients':con.execute(f"SELECT COUNT(*) c FROM patients WHERE booking_date LIKE ?{clause}",[today+'%']+hparams).fetchone()['c'],
            'total_patients':con.execute(f"SELECT COUNT(*) c FROM patients WHERE 1=1{clause}",hparams).fetchone()['c'],
            'today_revenue':con.execute(f"SELECT IFNULL(SUM(paid_amount),0) s FROM patients WHERE booking_date LIKE ?{clause}",[today+'%']+hparams).fetchone()['s'],
            'pending':con.execute(f"SELECT COUNT(*) c FROM patients WHERE IFNULL(report_status,'PENDING')<>'READY'{clause}",hparams).fetchone()['c']}
        recent=con.execute(f"SELECT * FROM patients WHERE 1=1{clause} ORDER BY id DESC LIMIT 12",hparams).fetchall()
    return templates.TemplateResponse(request,'dashboard.html',{'user':current_user(request),'stats':stats,'recent':recent})
@app.get('/patients',response_class=HTMLResponse)
def patients(request:Request,q:str='',date_from:str='',date_to:str=''):
    red=require_permission(request,'view_patients')
    if red: return red
    like=f"%{q.strip()}%"
    with db_conn() as con:
        clause, hparams = hospital_clause(request)
        if date_from and date_to:
            rows=con.execute(f"SELECT * FROM patients WHERE (booking_date BETWEEN ? AND ?) AND (?='' OR lab_no LIKE ? OR patient_name LIKE ? OR contact LIKE ? OR IFNULL(ref_by,doctor) LIKE ? OR IFNULL(panel_name,'') LIKE ?){clause} ORDER BY id DESC LIMIT 500",[date_from+' 00:00',date_to+' 23:59',q.strip(),like,like,like,like,like]+hparams).fetchall()
        else:
            rows=con.execute(f"SELECT * FROM patients WHERE (?='' OR lab_no LIKE ? OR patient_name LIKE ? OR contact LIKE ? OR IFNULL(ref_by,doctor) LIKE ? OR IFNULL(panel_name,'') LIKE ?){clause} ORDER BY id DESC LIMIT 500",[q.strip(),like,like,like,like,like]+hparams).fetchall()
    return templates.TemplateResponse(request,'patients.html',{'user':current_user(request),'patients':rows,'q':q,'date_from':date_from,'date_to':date_to})
@app.get('/patients/new',response_class=HTMLResponse)
def new_patient(request:Request):
    red=require_permission(request,'create_slip')
    if red: return red
    with db_conn() as con:
        clause, hparams = hospital_clause(request)
        panels=con.execute(f"SELECT name FROM panel_names WHERE status='ACTIVE'{clause} ORDER BY name",hparams).fetchall()
        ids=user_hospital_ids(request)
        if is_super_admin(request):
            hospitals=con.execute("SELECT id,name FROM hospitals WHERE status='ACTIVE' ORDER BY name").fetchall()
        elif ids:
            hospitals=con.execute(f"SELECT id,name FROM hospitals WHERE id IN ({','.join(['?']*len(ids))}) ORDER BY name",ids).fetchall()
        else:
            hospitals=[]
        return templates.TemplateResponse(request,'patient_form.html',{'user':current_user(request),'tests':active_tests(con),'panels':panels,'hospitals':hospitals,'current_hospital_id':current_hospital_id(request),'lab_no':next_lab_no(con)})
@app.post('/patients/new')
def create_patient(request:Request,title:str=Form(...),patient_name:str=Form(...),age:str=Form(''),age_type:str=Form('Years'),gender:str=Form(''),contact:str=Form(''),ref_by:str=Form(''),panel_name:str=Form('Self'),test_names:list[str]=Form(...),discount:float=Form(0),paid_amount:float=Form(0),total_amount:float=Form(0),payment_status:str=Form('UNPAID'),hospital_id:int=Form(0)):
    red=require_permission(request,'create_slip')
    if red: return red
    title=normalize_title(title); gender=gender or gender_for_title(title) or 'Male'; clean=[t for t in test_names if t.strip()]
    if not clean: return RedirectResponse('/patients/new',status_code=303)
    with db_conn() as con:
        requested_hospital_id=hospital_id or current_hospital_id(request)
        if not is_super_admin(request) and requested_hospital_id not in user_hospital_ids(request):
            return HTMLResponse("Access denied", status_code=403)
        hospital_id=requested_hospital_id
        lab_no=next_lab_no(con)
        # Use form total_amount if provided, otherwise calculate
        if total_amount <= 0:
            prices=[panel_price(con,panel_name,t,hospital_id) for t in clean]
            total=sum(prices)
        else:
            total = total_amount
        balance=max(total-float(discount or 0)-float(paid_amount or 0),0)
        # Validate payment status
        pay = payment_status if payment_status in ['PAID','PARTIAL','UNPAID'] else ('PAID' if balance<=0 and total>0 else ('PARTIAL' if paid_amount>0 else 'UNPAID'))
        con.execute("INSERT INTO patients(hospital_id,lab_no,title,patient_name,age,age_type,gender,contact,doctor,ref_by,panel_name,booking_date,reporting_date,total_amount,discount,paid_amount,balance,payment_status,report_status,last_updated,created_by) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(hospital_id,lab_no,title,patient_name.strip(),age,age_type,gender,contact,ref_by,ref_by,panel_name,now_str(),'',total,discount,paid_amount,balance,pay,'PENDING',now_str(),user_id(request)))
        for t in clean: con.execute("INSERT INTO patient_tests(hospital_id,lab_no,test_name,price,created_by) VALUES(?,?,?,?,?)",(hospital_id,lab_no,t,panel_price(con,panel_name,t,hospital_id),user_id(request)))
        audit_log(con,request,'SLIP_CREATED','patients',lab_no,lab_no,f"{patient_name.strip()} / {panel_name}")
        con.commit()
    return RedirectResponse(f'/patients/{lab_no}',status_code=303)
@app.get('/patients/{lab_no}',response_class=HTMLResponse)
def patient_detail(request:Request,lab_no:str):
    red=require_permission(request,'view_patients')
    if red: return red
    with db_conn() as con:
        p=require_patient_access(con,request,lab_no)
        tests=con.execute("SELECT * FROM patient_tests WHERE lab_no=? ORDER BY id",(lab_no,)).fetchall() if p else []
    if not p: return RedirectResponse('/patients',status_code=303)
    return templates.TemplateResponse(request,'patient_detail.html',{'user':current_user(request),'patient':p,'tests':tests})
@app.get('/results',response_class=HTMLResponse)
def results_lookup(request:Request,lab_no:str=''):
    red=require_permission(request,'enter_result')
    if red: return red
    patient=None; blocks=[]; result_map={}
    result_suggestions=[]; remark_suggestions=[]; morphology_suggestions=[]
    with db_conn() as con:
        if lab_no.strip():
            patient=require_patient_access(con,request,lab_no.strip())
            if patient:
                existing=con.execute("SELECT * FROM test_results WHERE lab_no=?",(lab_no.strip(),)).fetchall(); result_map={f"{r['test_name']}||{r['parameter']}":r['result'] for r in existing}; notes_map={}; [notes_map.setdefault(r['test_name'], {'morphology':'', 'remarks':''}) for r in existing]; [notes_map.__setitem__(r['test_name'], {'morphology': (r['morphology'] or notes_map.get(r['test_name'],{}).get('morphology','')), 'remarks': (r['remarks'] or notes_map.get(r['test_name'],{}).get('remarks',''))}) for r in existing if (r['morphology'] or r['remarks'])]
                for t in con.execute("SELECT * FROM patient_tests WHERE lab_no=? ORDER BY id",(lab_no.strip(),)).fetchall(): blocks.append({'test_name':t['test_name'],'department':test_department(con,t['test_name']),'params':test_format(con,t['test_name']),'morphology':notes_map.get(t['test_name'],{}).get('morphology',''),'remarks':notes_map.get(t['test_name'],{}).get('remarks','')})
        clause, hparams = hospital_clause(request)
        recent=con.execute(f"SELECT lab_no,patient_name,booking_date,report_status FROM patients WHERE 1=1{clause} ORDER BY id DESC LIMIT 15",hparams).fetchall()
        result_suggestions=suggestions(con,'RESULT')
        remark_suggestions=suggestions(con,'REMARKS')
        morphology_suggestions=suggestions(con,'MORPHOLOGY')
    return templates.TemplateResponse(request,'results.html',{'user':current_user(request),'lab_no':lab_no,'patient':patient,'test_blocks':blocks,'result_map':result_map,'recent':recent,'result_suggestions':result_suggestions,'remark_suggestions':remark_suggestions,'morphology_suggestions':morphology_suggestions})
@app.post('/results/{lab_no}')
async def save_results(request:Request,lab_no:str):
    red=require_permission(request,'enter_result')
    if red: return red
    form=await request.form(); entries=[]; notes={}
    for k,v in form.multi_items():
        if k.startswith('result::'):
            parts=k.split('::',2)
            if len(parts)==3 and str(v).strip(): entries.append((parts[1],parts[2],norm_result(v)))
        elif k.startswith('morphology::'):
            notes.setdefault(k.split('::',1)[1],{})['morphology']=str(v).strip()
        elif k.startswith('remarks::'):
            notes.setdefault(k.split('::',1)[1],{})['remarks']=str(v).strip()
    with db_conn() as con:
        patient=require_patient_access(con,request,lab_no)
        if not patient: return HTMLResponse("Access denied", status_code=403)
        con.execute("DELETE FROM test_results WHERE lab_no=?",(lab_no,))
        for t,param,res in entries:
            n=notes.get(t,{})
            con.execute("INSERT INTO test_results(hospital_id,lab_no,test_name,parameter,result,morphology,remarks,entered_by,updated_by) VALUES(?,?,?,?,?,?,?,?,?)",(patient['hospital_id'],lab_no,t,param,res,n.get('morphology',''),n.get('remarks',''),user_id(request),user_id(request)))
        for t,n in notes.items():
            if n.get('morphology'):
                con.execute("INSERT INTO test_results(hospital_id,lab_no,test_name,parameter,result,morphology,remarks,entered_by,updated_by) VALUES(?,?,?,?,?,?,?,?,?)",(patient['hospital_id'],lab_no,t,'MORPHOLOGY',n.get('morphology',''),n.get('morphology',''),'',user_id(request),user_id(request)))
            if n.get('remarks'):
                con.execute("INSERT INTO test_results(hospital_id,lab_no,test_name,parameter,result,morphology,remarks,entered_by,updated_by) VALUES(?,?,?,?,?,?,?,?,?)",(patient['hospital_id'],lab_no,t,'REMARKS',n.get('remarks',''),'',n.get('remarks',''),user_id(request),user_id(request)))
        for _,_,res in entries:
            remember_suggestion(con,'RESULT',res)
        for n in notes.values():
            remember_suggestion(con,'MORPHOLOGY',n.get('morphology',''))
            remember_suggestion(con,'REMARKS',n.get('remarks',''))
        sync_status(con,lab_no); audit_log(con,request,'RESULT_ENTERED','test_results','',lab_no,''); con.commit()
    return RedirectResponse(f'/report/{lab_no}',status_code=303)

@app.get('/pending-ready',response_class=HTMLResponse)
def pending_ready(request:Request,department:str='',status:str=''):
    red=require_permission(request,'enter_result')
    if red: return red
    rows=[]
    with db_conn() as con:
        clause, hparams = hospital_clause(request)
        dept_options=departments(con); patients=con.execute(f"SELECT * FROM patients WHERE 1=1{clause} ORDER BY id DESC LIMIT 500",hparams).fetchall()
        for p in patients:
            tests=con.execute("SELECT test_name FROM patient_tests WHERE lab_no=?",(p['lab_no'],)).fetchall(); booked=[]; done=0
            for t in tests:
                dept=test_department(con,t['test_name'])
                if department and dept!=department: continue
                booked.append({'name':t['test_name'],'department':dept})
                if con.execute("SELECT 1 FROM test_results WHERE lab_no=? AND test_name=? AND IFNULL(TRIM(result),'')<>'' LIMIT 1",(p['lab_no'],t['test_name'])).fetchone(): done+=1
            if not booked: continue
            row_status='READY' if done==len(booked) else ('PARTIAL' if done else 'PENDING')
            if status and row_status!=status: continue
            rows.append({'patient':p,'tests':booked,'done':done,'total':len(booked),'status':row_status})
    return templates.TemplateResponse(request,'pending_ready.html',{'user':current_user(request),'rows':rows,'departments':dept_options,'department':department,'status':status})
@app.get('/slip/{lab_no}',response_class=HTMLResponse)
def slip_preview(request:Request,lab_no:str):
    red=require_permission(request,'view_report')
    if red: return red
    with db_conn() as con:
        p=require_patient_access(con,request,lab_no); tests=con.execute("SELECT * FROM patient_tests WHERE lab_no=? ORDER BY id",(lab_no,)).fetchall() if p else []
    if not p: return RedirectResponse('/patients',status_code=303)
    qr_code = generate_qr_code(str(request.url_for('public_report_by_lab', lab_no=lab_no)))
    return templates.TemplateResponse(request,'slip.html',{'user':current_user(request),'patient':p,'tests':tests,'qr_code':qr_code})
@app.get('/report/{lab_no}',response_class=HTMLResponse)
def report_preview(request:Request,lab_no:str,department:str=''):
    red=require_permission(request,'view_report')
    if red: return red
    with db_conn() as con:
        p=require_patient_access(con,request,lab_no)
        if not p: return RedirectResponse('/patients',status_code=303)
        sync_status(con,lab_no); log_report_action(con,request,lab_no,department,'VIEW'); con.commit(); html=render_report_html(con,lab_no,department or None); depts=departments(con)
    if not p: return RedirectResponse('/patients',status_code=303)
    qr_code = generate_qr_code(lab_no)
    return templates.TemplateResponse(request,'report.html',{'user':current_user(request),'patient':p,'report_html':html,'departments':depts,'department':department,'qr_code':qr_code})
@app.post('/report/{lab_no}/mark-printed')
def mark_report_printed(request:Request,lab_no:str,department:str=Form('')):
    red=require_permission(request,'print_report')
    if red: return red
    with db_conn() as con:
        if not require_patient_access(con,request,lab_no): return HTMLResponse("Access denied", status_code=403)
        log_report_action(con,request,lab_no,department,'PRINT')
        con.execute("UPDATE patients SET report_status='PRINTED', last_updated=? WHERE lab_no=?",(now_str(),lab_no))
        audit_log(con,request,'REPORT_PRINTED','patients',lab_no,lab_no,department)
        con.commit()
    return RedirectResponse(f'/report/{lab_no}' + (f'?department={department}' if department else ''),status_code=303)
@app.get('/tests',response_class=HTMLResponse)
def tests_page(request:Request,q:str=''):
    red=require_permission(request,'test_master')
    if red: return red
    like=f"%{q.strip()}%"
    with db_conn() as con: rows=con.execute("SELECT * FROM test_master WHERE ?='' OR test_name LIKE ? OR department LIKE ? ORDER BY department,test_name LIMIT 800",(q.strip(),like,like)).fetchall()
    return templates.TemplateResponse(request,'tests.html',{'user':current_user(request),'tests':rows,'q':q})
@app.post('/tests/update')
def update_test(request:Request,test_name:str=Form(...),department:str=Form(...),price:float=Form(0),status:str=Form('ACTIVE'),report_heading:str=Form(''),report_group:str=Form('')):
    red=require_permission(request,'test_master')
    if red: return red
    heading=(report_heading or department).strip().upper()
    group=report_group.strip().upper()
    with db_conn() as con: con.execute("UPDATE test_master SET department=?,price=?,status=?,report_heading=?,report_group=? WHERE test_name=?",(department.strip().upper(),price,status.strip().upper(),heading,group,test_name)); con.commit()
    return RedirectResponse('/tests',status_code=303)
@app.post('/tests/create')
async def create_test_with_format(request:Request):
    red=require_permission(request,'test_master')
    if red: return red
    form=await request.form()
    test_name=str(form.get('test_name','')).strip()
    department=str(form.get('department','LABORATORY')).strip().upper()
    report_heading=str(form.get('report_heading') or department).strip().upper()
    report_group=str(form.get('report_group') or '').strip().upper()
    price=clean_float(form.get('price',0))
    params=form.getlist('parameter')
    units=form.getlist('unit')
    refs=form.getlist('reference_range')
    if test_name:
        with db_conn() as con:
            con.execute("INSERT OR REPLACE INTO test_master(test_name,department,price,status,report_mode,report_heading,report_group) VALUES(?,?,?,'ACTIVE','AUTO',?,?)",(test_name,department,price,report_heading,report_group))
            con.execute("DELETE FROM test_parameters WHERE test_name=?",(test_name,))
            order=1
            for p,u,r in zip(params,units,refs):
                if str(p).strip():
                    con.execute("INSERT INTO test_parameters(test_name,parameter,unit,reference_range,sort_order) VALUES(?,?,?,?,?)",(test_name,str(p).strip(),str(u).strip(),str(r).strip(),order)); order+=1
            if order==1:
                con.execute("INSERT INTO test_parameters(test_name,parameter,unit,reference_range,sort_order) VALUES(?,?,?,?,1)",(test_name,test_name,'',''))
            con.commit()
    return RedirectResponse('/tests',status_code=303)
@app.get('/settings',response_class=HTMLResponse)
def settings_page(request:Request):
    red=require_permission(request,'hospital_management')
    if red: return red
    with db_conn() as con: settings={r['setting_key']:r['setting_value'] for r in con.execute("SELECT * FROM app_settings").fetchall()}
    return templates.TemplateResponse(request,'settings.html',{'user':current_user(request),'settings':settings})
@app.post('/settings')
def save_settings(request:Request, lab_name:str=Form(''), lab_subtitle:str=Form(''), lab_address:str=Form(''), lab_phone:str=Form(''), report_footer_note:str=Form(''), report_header_space_px:str=Form('145'), report_footer_space_px:str=Form('190'), report_content_width_px:str=Form('720'), report_logo_path:str=Form(''), report_header_image_path:str=Form(''), report_footer_image_path:str=Form('')):
    red=require_permission(request,'hospital_management')
    if red: return red
    with db_conn() as con:
        for k,v in {'lab_name':lab_name,'lab_subtitle':lab_subtitle,'lab_address':lab_address,'lab_phone':lab_phone,'report_footer_note':report_footer_note,'report_header_space_px':report_header_space_px,'report_footer_space_px':report_footer_space_px,'report_content_width_px':report_content_width_px,'report_logo_path':report_logo_path,'report_header_image_path':report_header_image_path,'report_footer_image_path':report_footer_image_path}.items(): con.execute("INSERT OR REPLACE INTO app_settings(setting_key,setting_value) VALUES(?,?)",(k,v))
        con.commit()
    return RedirectResponse('/settings',status_code=303)
@app.get('/panels',response_class=HTMLResponse)
def panels_page(request:Request,panel:str='Self',q:str=''):
    red=require_permission(request,'panel_rates')
    if red: return red
    like=f"%{q.strip()}%"
    with db_conn() as con:
        clause, hparams = hospital_clause(request)
        hid=current_hospital_id(request)
        panels=con.execute(f"SELECT name FROM panel_names WHERE status='ACTIVE'{clause} ORDER BY name",hparams).fetchall()
        rows=con.execute("SELECT tm.test_name,tm.department,tm.price self_price,IFNULL(ptr.price,tm.price) panel_price FROM test_master tm LEFT JOIN panel_test_rates ptr ON ptr.test_name=tm.test_name AND ptr.panel_name=? AND ptr.hospital_id=? WHERE ?='' OR tm.test_name LIKE ? OR tm.department LIKE ? ORDER BY tm.department,tm.test_name LIMIT 500",(panel,hid,q.strip(),like,like)).fetchall()
    return templates.TemplateResponse(request,'panels.html',{'user':current_user(request),'panels':panels,'panel':panel,'rows':rows,'q':q})
@app.post('/panels/update')
def panels_update(request:Request,panel:str=Form(...),test_name:list[str]=Form(...),price:list[float]=Form(...)):
    red=require_permission(request,'panel_rates')
    if red: return red
    with db_conn() as con:
        hid=current_hospital_id(request)
        con.execute("INSERT OR IGNORE INTO panel_names(name,status,hospital_id) VALUES(?,'ACTIVE',?)",(panel,hid))
        for t,p in zip(test_name,price): con.execute("INSERT OR REPLACE INTO panel_test_rates(hospital_id,panel_name,test_name,price) VALUES(?,?,?,?)",(hid,panel,t,float(p or 0)))
        audit_log(con,request,'PANEL_RATES_UPDATED','panel_names',panel,'',panel)
        con.commit()
    return RedirectResponse(f'/panels?panel={panel}',status_code=303)


# ---- Full web modules appended from desktop workflow ----

def clean_float(value):
    try: return float(str(value or '0').replace(',', ''))
    except Exception: return 0.0


def recalc_bill(con, lab_no):
    total = con.execute("SELECT IFNULL(SUM(price),0) s FROM patient_tests WHERE lab_no=?", (lab_no,)).fetchone()['s'] or 0
    p = con.execute("SELECT discount, paid_amount FROM patients WHERE lab_no=?", (lab_no,)).fetchone()
    discount = float(p['discount'] or 0) if p else 0
    paid = float(p['paid_amount'] or 0) if p else 0
    balance = max(float(total) - discount - paid, 0)
    status = 'PAID' if balance <= 0 and total > 0 else ('PARTIAL' if paid > 0 else 'UNPAID')
    con.execute("UPDATE patients SET total_amount=?, balance=?, payment_status=?, last_updated=? WHERE lab_no=?", (total, balance, status, now_str(), lab_no))


@app.post('/patients/{lab_no}/edit')
def edit_patient(request:Request, lab_no:str, title:str=Form('Mr.'), patient_name:str=Form(...), age:str=Form(''), age_type:str=Form('Years'), gender:str=Form('Male'), contact:str=Form(''), ref_by:str=Form(''), panel_name:str=Form('Self'), discount:float=Form(0), paid_amount:float=Form(0), payment_status:str=Form('')):
    red=require_permission(request,'edit_patients')
    if red: return red
    with db_conn() as con:
        patient=require_patient_access(con,request,lab_no)
        if not patient: return HTMLResponse("Access denied", status_code=403)
        hid=patient['hospital_id']
        con.execute("INSERT OR IGNORE INTO panel_names(name,status,hospital_id) VALUES(?,'ACTIVE',?)", (panel_name or 'Self',hid))
        update_query = "UPDATE patients SET title=?, patient_name=?, age=?, age_type=?, gender=?, contact=?, doctor=?, ref_by=?, panel_name=?, discount=?, paid_amount=?"
        params = [normalize_title(title), patient_name.strip(), age, age_type, gender, contact, ref_by, ref_by, panel_name, discount, paid_amount]
        if payment_status and payment_status in ['PAID','PARTIAL','UNPAID']:
            update_query += ", payment_status=?"
            params.append(payment_status)
        update_query += ", updated_by=?, last_updated=? WHERE lab_no=?"
        params.extend([user_id(request), now_str(), lab_no])
        con.execute(update_query, params)
        recalc_bill(con, lab_no)
        audit_log(con,request,'PATIENT_UPDATED','patients',lab_no,lab_no,patient_name)
        con.commit()
    return RedirectResponse(f'/patients/{lab_no}', status_code=303)


@app.post('/patients/{lab_no}/tests/add')
def add_patient_test(request:Request, lab_no:str, test_name:str=Form(...)):
    red=require_permission(request,'edit_slip')
    if red: return red
    with db_conn() as con:
        p=require_patient_access(con,request,lab_no)
        if not p: return HTMLResponse("Access denied", status_code=403)
        price=panel_price(con, p['panel_name'] if p else 'Self', test_name, p['hospital_id'])
        exists=con.execute("SELECT 1 FROM patient_tests WHERE lab_no=? AND test_name=?", (lab_no,test_name)).fetchone()
        if not exists:
            con.execute("INSERT INTO patient_tests(hospital_id,lab_no,test_name,price,status,created_by) VALUES(?,?,?,?,'PENDING',?)", (p['hospital_id'],lab_no,test_name,price,user_id(request)))
        con.execute("UPDATE patients SET report_status='PENDING', last_updated=? WHERE lab_no=?", (now_str(), lab_no))
        recalc_bill(con, lab_no)
        audit_log(con,request,'SLIP_TEST_ADDED','patient_tests',test_name,lab_no,test_name)
        con.commit()
    return RedirectResponse(f'/patients/{lab_no}', status_code=303)


@app.post('/patients/{lab_no}/tests/{test_id}/remove')
def remove_patient_test(request:Request, lab_no:str, test_id:int):
    red=require_permission(request,'edit_slip')
    if red: return red
    with db_conn() as con:
        if not require_patient_access(con,request,lab_no): return HTMLResponse("Access denied", status_code=403)
        row=con.execute("SELECT test_name FROM patient_tests WHERE id=? AND lab_no=?", (test_id,lab_no)).fetchone()
        if row:
            con.execute("DELETE FROM patient_tests WHERE id=? AND lab_no=?", (test_id,lab_no))
            con.execute("DELETE FROM test_results WHERE lab_no=? AND test_name=?", (lab_no,row['test_name']))
        recalc_bill(con, lab_no)
        sync_status(con, lab_no)
        audit_log(con,request,'SLIP_TEST_REMOVED','patient_tests',str(test_id),lab_no,row['test_name'] if row else '')
        con.commit()
    return RedirectResponse(f'/patients/{lab_no}', status_code=303)


@app.get('/reports', response_class=HTMLResponse)
def reports_page(request:Request, q:str='', date_from:str='', date_to:str=''):
    red=require_permission(request,'view_report')
    if red: return red
    like=f"%{q.strip()}%"
    with db_conn() as con:
        clause, hparams = hospital_clause(request)
        if date_from and date_to:
            rows=con.execute("""
                SELECT * FROM patients
                 WHERE (reporting_date BETWEEN ? AND ? OR booking_date BETWEEN ? AND ?)
                   AND (?='' OR lab_no LIKE ? OR patient_name LIKE ? OR contact LIKE ?)
                   """ + clause + """
                  ORDER BY id DESC LIMIT 500
            """, [date_from+' 00:00',date_to+' 23:59',date_from+' 00:00',date_to+' 23:59',q.strip(),like,like,like]+hparams).fetchall()
        else:
            rows=con.execute(f"SELECT * FROM patients WHERE (?='' OR lab_no LIKE ? OR patient_name LIKE ? OR contact LIKE ?){clause} ORDER BY id DESC LIMIT 500",[q.strip(),like,like,like]+hparams).fetchall()
    return templates.TemplateResponse(request,'reports.html',{'user':current_user(request),'patients':rows,'q':q,'date_from':date_from,'date_to':date_to})

@app.get('/report-logs', response_class=HTMLResponse)
def report_logs_page(request:Request, q:str=''):
    red=require_permission(request,'view_report')
    if red: return red
    like=f"%{q.strip()}%"
    with db_conn() as con:
        clause, hparams = hospital_clause(request)
        rows=con.execute(f'SELECT * FROM report_logs WHERE (?=\'\' OR lab_no LIKE ? OR "user" LIKE ? OR action LIKE ?){clause} ORDER BY id DESC LIMIT 500',[q.strip(),like,like,like]+hparams).fetchall()
    return templates.TemplateResponse(request,'report_logs.html',{'user':current_user(request),'logs':rows,'q':q})


@app.get('/billing', response_class=HTMLResponse)
def billing_page(request:Request, date_from:str='', date_to:str='', panel:str='', q:str=''):
    red=require_permission(request,'billing')
    if red: return red
    date_from=date_from or today_str(); date_to=date_to or date_from; like=f"%{q.strip()}%"
    with db_conn() as con:
        clause, hparams = hospital_clause(request)
        where="WHERE booking_date>=? AND booking_date<=? AND (?='' OR lab_no LIKE ? OR patient_name LIKE ? OR contact LIKE ?)"
        params=[date_from, date_to+' 99:99', q.strip(), like, like, like]
        if panel:
            where += " AND IFNULL(panel_name,'')=?"; params.append(panel)
        where += clause; params += hparams
        rows=con.execute(f"SELECT * FROM patients {where} ORDER BY id DESC", params).fetchall()
        totals={'total':sum(float(r['total_amount'] or 0) for r in rows),'paid':sum(float(r['paid_amount'] or 0) for r in rows),'balance':sum(float(r['balance'] or 0) for r in rows)}
        panel_clause, panel_params = hospital_clause(request)
        panel_rows=con.execute(f"SELECT name FROM panel_names WHERE status='ACTIVE'{panel_clause} ORDER BY name",panel_params).fetchall()
    return templates.TemplateResponse(request,'billing.html',{'user':current_user(request),'patients':rows,'totals':totals,'date_from':date_from,'date_to':date_to,'panel':panel,'q':q,'panels':panel_rows})


@app.get('/billing/export.csv')
def billing_export(request:Request, date_from:str='', date_to:str='', panel:str='', q:str=''):
    red=require_permission(request,'billing')
    if red: return red
    date_from=date_from or today_str(); date_to=date_to or date_from; like=f"%{q.strip()}%"
    with db_conn() as con:
        clause, hparams = hospital_clause(request)
        where="WHERE booking_date>=? AND booking_date<=? AND (?='' OR lab_no LIKE ? OR patient_name LIKE ? OR contact LIKE ?)"
        params=[date_from, date_to+' 99:99', q.strip(), like, like, like]
        if panel:
            where += " AND IFNULL(panel_name,'')=?"; params.append(panel)
        where += clause; params += hparams
        rows=con.execute(f"SELECT * FROM patients {where} ORDER BY id DESC", params).fetchall()
    out=io.StringIO(); w=csv.writer(out)
    w.writerow(['Lab No','Patient','Contact','Panel','Booking','Total','Paid','Balance','Status'])
    for p in rows:
        w.writerow([p['lab_no'],f"{p['title']} {p['patient_name']}",p['contact'],p['panel_name'],p['booking_date'],p['total_amount'],p['paid_amount'],p['balance'],p['payment_status']])
    return StreamingResponse(iter([out.getvalue()]), media_type='text/csv', headers={'Content-Disposition':'attachment; filename=billing.csv'})

@app.get('/billing/export.xls')
def billing_export_excel(request:Request, date_from:str='', date_to:str='', panel:str='', q:str=''):
    red=require_permission(request,'billing')
    if red: return red
    date_from=date_from or today_str(); date_to=date_to or date_from; like=f"%{q.strip()}%"
    with db_conn() as con:
        clause, hparams = hospital_clause(request)
        where="WHERE booking_date>=? AND booking_date<=? AND (?='' OR lab_no LIKE ? OR patient_name LIKE ? OR contact LIKE ?)"
        params=[date_from, date_to+' 99:99', q.strip(), like, like, like]
        if panel:
            where += " AND IFNULL(panel_name,'')=?"; params.append(panel)
        where += clause; params += hparams
        rows=con.execute(f"SELECT * FROM patients {where} ORDER BY id DESC", params).fetchall()
    body="<table><tr><th>Lab No</th><th>Patient</th><th>Contact</th><th>Panel</th><th>Booking</th><th>Total</th><th>Paid</th><th>Balance</th><th>Status</th></tr>"
    for p in rows:
        body += f"<tr><td>{escape(str(p['lab_no']))}</td><td>{escape(str(p['title']))} {escape(str(p['patient_name']))}</td><td>{escape(str(p['contact'] or ''))}</td><td>{escape(str(p['panel_name'] or ''))}</td><td>{escape(str(p['booking_date'] or ''))}</td><td>{p['total_amount']}</td><td>{p['paid_amount']}</td><td>{p['balance']}</td><td>{escape(str(p['payment_status'] or ''))}</td></tr>"
    body += "</table>"
    return HTMLResponse(body, media_type='application/vnd.ms-excel', headers={'Content-Disposition':'attachment; filename=billing.xls'})


@app.get('/users', response_class=HTMLResponse)
def users_page(request:Request):
    red=require_permission(request,'user_management')
    if red: return red
    with db_conn() as con:
        users=con.execute("SELECT id,username,full_name,role,is_active,last_login_at FROM users ORDER BY username").fetchall()
        roles=con.execute("SELECT name FROM roles ORDER BY id").fetchall()
        hospitals=con.execute("SELECT id,name FROM hospitals WHERE status='ACTIVE' ORDER BY name").fetchall()
        permissions=con.execute("SELECT permission_key,label,category FROM permissions ORDER BY category,label").fetchall()
        user_hospitals={r['user_id']:[] for r in con.execute("SELECT DISTINCT user_id FROM user_hospitals").fetchall()}
        for r in con.execute("SELECT user_id,hospital_id FROM user_hospitals").fetchall():
            user_hospitals.setdefault(r['user_id'],[]).append(r['hospital_id'])
        user_permissions_map={r['user_id']:[] for r in con.execute("SELECT DISTINCT user_id FROM user_permissions WHERE allowed=true").fetchall()}
        for r in con.execute("SELECT user_id,permission_key FROM user_permissions WHERE allowed=true").fetchall():
            user_permissions_map.setdefault(r['user_id'],[]).append(r['permission_key'])
    return templates.TemplateResponse(request,'users.html',{'user':current_user(request),'users':users,'roles':roles,'hospitals':hospitals,'permissions':permissions,'user_hospitals':user_hospitals,'user_permissions':user_permissions_map})


@app.post('/users/save')
async def users_save(request:Request):
    red=require_permission(request,'user_management')
    if red: return red
    form=await request.form()
    username=str(form.get('username','')).strip()
    password=str(form.get('password',''))
    role=str(form.get('role','Limited User'))
    full_name=str(form.get('full_name','')).strip()
    is_active=str(form.get('is_active','ACTIVE')) == 'ACTIVE'
    hospital_ids=[int(x) for x in form.getlist('hospital_ids') if str(x).isdigit()]
    custom_permissions=[str(x) for x in form.getlist('permissions')]
    if not username:
        return RedirectResponse('/users', status_code=303)
    with db_conn() as con:
        existing=con.execute("SELECT id FROM users WHERE username=?",(username,)).fetchone()
        role_row=con.execute("SELECT id FROM roles WHERE name=?",(role,)).fetchone()
        if existing:
            con.execute("UPDATE users SET full_name=?, role=?, role_id=?, is_active=?, updated_at=? WHERE id=?",(full_name,role,role_row['id'] if role_row else None,is_active,now_str(),existing['id']))
            uid=existing['id']
            if password:
                err=password_error(password)
                if not err: con.execute("UPDATE users SET password_hash=?, password='', must_change_password=false, updated_at=? WHERE id=?",(hash_password(password),now_str(),uid))
        else:
            if not password:
                password=secrets.token_urlsafe(8)
            con.execute("INSERT INTO users(username,password,password_hash,full_name,role,role_id,is_active,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",(username,'',hash_password(password),full_name,role,role_row['id'] if role_row else None,is_active,now_str(),now_str()))
            uid=con.execute("SELECT id FROM users WHERE username=?",(username,)).fetchone()['id']
        con.execute("DELETE FROM user_hospitals WHERE user_id=?",(uid,))
        for hid in hospital_ids:
            con.execute("INSERT INTO user_hospitals(user_id,hospital_id) VALUES(?,?) ON CONFLICT (user_id,hospital_id) DO NOTHING",(uid,hid))
        con.execute("DELETE FROM user_permissions WHERE user_id=?",(uid,))
        for perm in custom_permissions:
            con.execute("INSERT INTO user_permissions(user_id,permission_key,allowed) VALUES(?,?,true) ON CONFLICT (user_id,permission_key) DO UPDATE SET allowed=true",(uid,perm))
        audit_log(con,request,'USER_SAVED','users',str(uid),'',username)
        con.commit()
    return RedirectResponse('/users', status_code=303)


@app.post('/users/delete')
def users_delete(request:Request, username:str=Form(...)):
    red=require_permission(request,'user_management')
    if red: return red
    if username not in {'admin','syedali'}:
        with db_conn() as con:
            row=con.execute("SELECT id FROM users WHERE username=?",(username,)).fetchone()
            if row:
                con.execute("DELETE FROM user_hospitals WHERE user_id=?",(row['id'],))
                con.execute("DELETE FROM user_permissions WHERE user_id=?",(row['id'],))
                con.execute("DELETE FROM users WHERE id=?", (row['id'],))
                audit_log(con,request,'USER_DELETED','users',str(row['id']),'',username)
                con.commit()
    return RedirectResponse('/users', status_code=303)

@app.post('/users/status')
def users_status(request:Request, username:str=Form(...), status:str=Form('ACTIVE')):
    red=require_permission(request,'user_management')
    if red: return red
    with db_conn() as con:
        con.execute("UPDATE users SET is_active=?, updated_at=? WHERE username=?",(status=='ACTIVE',now_str(),username))
        audit_log(con,request,'USER_STATUS_CHANGED','users',username,'',status)
        con.commit()
    return RedirectResponse('/users', status_code=303)

@app.post('/users/reset-password')
def users_reset_password(request:Request, username:str=Form(...), new_password:str=Form(...), confirm_password:str=Form(...)):
    red=require_permission(request,'user_management')
    if red: return red
    err=password_error(new_password,confirm_password)
    if err: return HTMLResponse(err, status_code=400)
    with db_conn() as con:
        row=con.execute("SELECT id FROM users WHERE username=?",(username,)).fetchone()
        if row:
            con.execute("UPDATE users SET password_hash=?, password='', must_change_password=false, updated_at=? WHERE id=?",(hash_password(new_password),now_str(),row['id']))
            audit_log(con,request,'PASSWORD_RESET','users',str(row['id']),'',username)
            con.commit()
    return RedirectResponse('/users', status_code=303)

@app.get('/my-account', response_class=HTMLResponse)
def my_account(request:Request):
    red=require_login(request)
    if red: return red
    return templates.TemplateResponse(request,'my_account.html',{'user':current_user(request),'error':'','success':''})

@app.post('/my-account/password', response_class=HTMLResponse)
def change_own_password(request:Request, current_password:str=Form(...), new_password:str=Form(...), confirm_password:str=Form(...)):
    red=require_login(request)
    if red: return red
    err=password_error(new_password,confirm_password)
    if err: return templates.TemplateResponse(request,'my_account.html',{'user':current_user(request),'error':err,'success':''})
    with db_conn() as con:
        row=con.execute("SELECT * FROM users WHERE id=?",(user_id(request),)).fetchone()
        if not row or not verify_password(current_password,row.get('password_hash') or row.get('password')):
            return templates.TemplateResponse(request,'my_account.html',{'user':current_user(request),'error':'Current password is incorrect.','success':''})
        con.execute("UPDATE users SET password_hash=?, password='', must_change_password=false, updated_at=? WHERE id=?",(hash_password(new_password),now_str(),row['id']))
        audit_log(con,request,'PASSWORD_CHANGED','users',str(row['id']),'',row['username'])
        con.commit()
    return templates.TemplateResponse(request,'my_account.html',{'user':current_user(request),'error':'','success':'Password changed successfully.'})

@app.get('/hospitals', response_class=HTMLResponse)
def hospitals_page(request:Request):
    red=require_permission(request,'hospital_management')
    if red: return red
    with db_conn() as con:
        hospitals=con.execute("SELECT * FROM hospitals ORDER BY name").fetchall()
    return templates.TemplateResponse(request,'hospitals.html',{'user':current_user(request),'hospitals':hospitals})

@app.post('/hospitals/save')
def hospitals_save(request:Request, hospital_id:int=Form(0), name:str=Form(...), code:str=Form(''), address:str=Form(''), phone:str=Form(''), status:str=Form('ACTIVE')):
    red=require_permission(request,'hospital_management')
    if red: return red
    with db_conn() as con:
        if hospital_id:
            con.execute("UPDATE hospitals SET name=?, code=?, address=?, phone=?, status=?, updated_at=? WHERE id=?",(name.strip(),code.strip(),address,phone,status,now_str(),hospital_id))
            hid=hospital_id
        else:
            con.execute("INSERT INTO hospitals(name,code,address,phone,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT (name) DO UPDATE SET code=excluded.code,address=excluded.address,phone=excluded.phone,status=excluded.status,updated_at=excluded.updated_at",(name.strip(),code.strip(),address,phone,status,now_str(),now_str()))
            hid=con.execute("SELECT id FROM hospitals WHERE name=?",(name.strip(),)).fetchone()['id']
        audit_log(con,request,'HOSPITAL_SAVED','hospitals',str(hid),'',name.strip())
        con.commit()
    return RedirectResponse('/hospitals', status_code=303)

@app.post('/hospitals/delete')
def hospitals_delete(request:Request, hospital_id:int=Form(...)):
    red=require_permission(request,'hospital_management')
    if red: return red
    with db_conn() as con:
        used=con.execute("SELECT COUNT(*) c FROM patients WHERE hospital_id=?",(hospital_id,)).fetchone()['c']
        if used:
            con.execute("UPDATE hospitals SET status='INACTIVE', updated_at=? WHERE id=?",(now_str(),hospital_id))
        else:
            con.execute("DELETE FROM hospitals WHERE id=?",(hospital_id,))
        audit_log(con,request,'HOSPITAL_DELETED','hospitals',str(hospital_id),'','')
        con.commit()
    return RedirectResponse('/hospitals', status_code=303)

@app.get('/roles', response_class=HTMLResponse)
def roles_page(request:Request):
    red=require_permission(request,'user_management')
    if red: return red
    with db_conn() as con:
        roles=con.execute("SELECT * FROM roles ORDER BY id").fetchall()
        permissions=con.execute("SELECT * FROM permissions ORDER BY category,label").fetchall()
        role_permissions_map={}
        for r in con.execute("SELECT role_id,permission_key FROM role_permissions").fetchall():
            role_permissions_map.setdefault(r['role_id'],[]).append(r['permission_key'])
    return templates.TemplateResponse(request,'roles.html',{'user':current_user(request),'roles':roles,'permissions':permissions,'role_permissions':role_permissions_map})

@app.post('/roles/save')
def roles_save(request:Request, role_id:int=Form(0), name:str=Form(...), description:str=Form(''), permissions:list[str]=Form([])):
    red=require_permission(request,'user_management')
    if red: return red
    with db_conn() as con:
        if role_id:
            con.execute("UPDATE roles SET name=?, description=? WHERE id=?",(name.strip(),description,role_id)); rid=role_id
        else:
            con.execute("INSERT INTO roles(name,description,is_system,created_at) VALUES(?,?,false,?) ON CONFLICT (name) DO NOTHING",(name.strip(),description,now_str()))
            rid=con.execute("SELECT id FROM roles WHERE name=?",(name.strip(),)).fetchone()['id']
        con.execute("DELETE FROM role_permissions WHERE role_id=?",(rid,))
        for perm in permissions:
            con.execute("INSERT INTO role_permissions(role_id,permission_key) VALUES(?,?) ON CONFLICT (role_id,permission_key) DO NOTHING",(rid,perm))
        audit_log(con,request,'ROLE_SAVED','roles',str(rid),'',name.strip())
        con.commit()
    return RedirectResponse('/roles', status_code=303)


@app.get('/backup', response_class=HTMLResponse)
def backup_page(request:Request):
    red=require_permission(request,'hospital_management')
    if red: return red
    return templates.TemplateResponse(request,'backup.html',{'user':current_user(request),'database_host':DATABASE_URL.split('@')[-1].split('/')[0] if DATABASE_URL and '@' in DATABASE_URL else 'Supabase PostgreSQL'})


@app.post('/backup/create')
def backup_create(request:Request):
    red=require_permission(request,'hospital_management')
    if red: return red
    return RedirectResponse('/backup', status_code=303)

@app.post('/backup/restore')
def backup_restore(request:Request, name:str=Form(...)):
    red=require_permission(request,'hospital_management')
    if red: return red
    return RedirectResponse('/backup', status_code=303)


@app.get('/backup/download/{name}')
def backup_download(request:Request, name:str):
    red=require_permission(request,'hospital_management')
    if red: return red
    return RedirectResponse('/backup', status_code=303)

@app.get('/slips', response_class=HTMLResponse)
def slips_page(request:Request, q:str='', date_from:str='', date_to:str=''):
    red=require_permission(request,'print_report')
    if red: return red
    like=f"%{q.strip()}%"
    with db_conn() as con:
        clause, hparams = hospital_clause(request)
        if date_from and date_to:
            rows=con.execute("""SELECT * FROM patients
                 WHERE booking_date BETWEEN ? AND ?
                   AND (?='' OR lab_no LIKE ? OR patient_name LIKE ? OR contact LIKE ?)
                 """ + clause + " ORDER BY id DESC LIMIT 500",[date_from+' 00:00',date_to+' 23:59',q.strip(),like,like,like]+hparams).fetchall()
        else:
            rows=con.execute(f"""SELECT * FROM patients
                 WHERE (?='' OR lab_no LIKE ? OR patient_name LIKE ? OR contact LIKE ?)
                 {clause} ORDER BY id DESC LIMIT 500""",[q.strip(),like,like,like]+hparams).fetchall()
    return templates.TemplateResponse(request,'slips.html',{'user':current_user(request),'patients':rows,'q':q,'date_from':date_from,'date_to':date_to})

@app.get('/departments', response_class=HTMLResponse)
def departments_page(request:Request):
    red=require_permission(request,'test_master')
    if red: return red
    with db_conn() as con:
        rows=con.execute("SELECT department,COUNT(*) count FROM test_master GROUP BY department ORDER BY department").fetchall()
    return templates.TemplateResponse(request,'departments.html',{'user':current_user(request),'departments':rows})

@app.post('/departments/add')
def department_add(request:Request, department:str=Form(...)):
    red=require_permission(request,'test_master')
    if red: return red
    name=department.strip().upper()
    if name:
        with db_conn() as con:
            con.execute("INSERT OR IGNORE INTO test_master(test_name,department,price,status,report_heading) VALUES(?,?,0,'INACTIVE',?)",(f"{name} PLACEHOLDER",name,name))
            con.commit()
    return RedirectResponse('/departments', status_code=303)

@app.post('/departments/rename')
def department_rename(request:Request, old_department:str=Form(...), new_department:str=Form(...)):
    red=require_permission(request,'test_master')
    if red: return red
    old=old_department.strip(); new=new_department.strip().upper()
    if old and new:
        with db_conn() as con:
            con.execute("UPDATE test_master SET department=?, report_heading=? WHERE department=?",(new,new,old))
            con.commit()
    return RedirectResponse('/departments', status_code=303)


@app.get('/tests/{test_name}/format', response_class=HTMLResponse)
def test_format_page(request:Request, test_name:str):
    red=require_permission(request,'test_master')
    if red: return red
    with db_conn() as con: rows=test_format(con,test_name)
    return templates.TemplateResponse(request,'test_format.html',{'user':current_user(request),'test_name':test_name,'rows':rows})


@app.post('/tests/{test_name}/format')
async def test_format_save(request:Request, test_name:str):
    red=require_permission(request,'test_master')
    if red: return red
    form=await request.form(); params=form.getlist('parameter'); units=form.getlist('unit'); refs=form.getlist('reference_range')
    with db_conn() as con:
        con.execute("DELETE FROM test_parameters WHERE test_name=?", (test_name,))
        order=1
        for p,u,r in zip(params,units,refs):
            if str(p).strip():
                con.execute("INSERT INTO test_parameters(test_name,parameter,unit,reference_range,sort_order) VALUES(?,?,?,?,?)", (test_name,str(p).strip(),str(u).strip(),str(r).strip(),order)); order+=1
        con.commit()
    return RedirectResponse('/tests', status_code=303)


@app.get('/test_master', response_class=HTMLResponse)
def test_master_alias(request:Request):
    return RedirectResponse('/tests', status_code=303)

# ========== NEW FEATURES FROM DESKTOP APP ==========

@app.get('/expenses', response_class=HTMLResponse)
def expenses_page(request:Request, start_date:str='', end_date:str=''):
    red=require_permission(request,'billing')
    if red: return red
    with db_conn() as con:
        clause, hparams = hospital_clause(request)
        if start_date and end_date:
            rows=con.execute(f"SELECT * FROM expenses WHERE expense_date BETWEEN ? AND ?{clause} ORDER BY expense_date DESC",[start_date,end_date]+hparams).fetchall()
        else:
            rows=con.execute(f"SELECT * FROM expenses WHERE 1=1{clause} ORDER BY expense_date DESC LIMIT 100",hparams).fetchall()
        total=con.execute(f"SELECT IFNULL(SUM(amount),0) total FROM expenses WHERE 1=1{clause}",hparams).fetchone()['total']
        categories=con.execute(f"SELECT DISTINCT category FROM expenses WHERE category IS NOT NULL AND category<>''{clause} ORDER BY category",hparams).fetchall()
    return templates.TemplateResponse(request,'expenses.html',{'user':current_user(request),'expenses':rows,'total':total,'categories':categories,'start_date':start_date,'end_date':end_date})

@app.post('/expenses')
def save_expense(request:Request, expense_date:str=Form(...), category:str=Form(...), description:str=Form(''), amount:float=Form(0)):
    red=require_permission(request,'billing')
    if red: return red
    with db_conn() as con:
        con.execute("INSERT INTO expenses(hospital_id,expense_date,category,description,amount,created_at) VALUES(?,?,?,?,?,?)",(current_hospital_id(request),expense_date,category,description,amount,now_str()))
        con.commit()
    return RedirectResponse('/expenses', status_code=303)

@app.get('/doctors', response_class=HTMLResponse)
def doctors_page(request:Request):
    red=require_permission(request,'create_slip')
    if red: return red
    with db_conn() as con:
        clause, hparams = hospital_clause(request)
        doctors=con.execute(f"SELECT * FROM doctors WHERE status='ACTIVE'{clause} ORDER BY name",hparams).fetchall()
    return templates.TemplateResponse(request,'doctors.html',{'user':current_user(request),'doctors':doctors})

@app.post('/doctors')
def save_doctor(request:Request, name:str=Form(...), phone:str=Form('')):
    red=require_permission(request,'create_slip')
    if red: return red
    with db_conn() as con:
        con.execute("INSERT OR IGNORE INTO doctors(hospital_id,name,phone,status) VALUES(?,?,?,'ACTIVE')",(current_hospital_id(request),name,phone))
        con.commit()
    return RedirectResponse('/doctors', status_code=303)

@app.post('/doctors/{doc_id}/delete')
def delete_doctor(request:Request, doc_id:int):
    red=require_permission(request,'create_slip')
    if red: return red
    with db_conn() as con:
        con.execute("UPDATE doctors SET status='INACTIVE' WHERE id=?",(doc_id,))
        con.commit()
    return RedirectResponse('/doctors', status_code=303)

@app.get('/daily-patients', response_class=HTMLResponse)
def daily_patients_page(request:Request, date:str=''):
    red=require_permission(request,'billing')
    if red: return red
    if not date: date=today_str()
    with db_conn() as con:
        clause, hparams = hospital_clause(request)
        rows=con.execute(f"SELECT lab_no,patient_name,total_amount,paid_amount,balance,payment_status,report_status FROM patients WHERE DATE(booking_date)=DATE(?){clause} ORDER BY id DESC",[date]+hparams).fetchall()
        stats=con.execute("""SELECT 
            COUNT(*) total_patients,
            IFNULL(SUM(total_amount),0) total_amount,
            IFNULL(SUM(paid_amount),0) total_paid,
            IFNULL(SUM(balance),0) total_balance
        FROM patients WHERE DATE(booking_date)=DATE(?)""" + clause, [date]+hparams).fetchone()
    return templates.TemplateResponse(request,'daily_patients.html',{'user':current_user(request),'patients':rows,'date':date,'stats':stats})

@app.get('/cash-report', response_class=HTMLResponse)
def cash_report_page(request:Request, start_date:str='', end_date:str=''):
    red=require_permission(request,'billing')
    if red: return red
    with db_conn() as con:
        clause, hparams = hospital_clause(request)
        if start_date and end_date:
            patients=con.execute(f"SELECT * FROM patients WHERE DATE(booking_date) BETWEEN ? AND ?{clause} ORDER BY booking_date DESC",[start_date,end_date]+hparams).fetchall()
            expenses=con.execute(f"SELECT * FROM expenses WHERE expense_date BETWEEN ? AND ?{clause} ORDER BY expense_date DESC",[start_date,end_date]+hparams).fetchall()
        else:
            patients=con.execute(f"SELECT * FROM patients WHERE 1=1{clause} ORDER BY id DESC LIMIT 300",hparams).fetchall()
            expenses=con.execute(f"SELECT * FROM expenses WHERE 1=1{clause} ORDER BY id DESC LIMIT 100",hparams).fetchall()
        total_collection=sum(float(p['paid_amount'] or 0) for p in patients)
        total_expenses=sum(float(e['amount'] or 0) for e in expenses)
        net_cash=total_collection - total_expenses
    return templates.TemplateResponse(request,'cash_report.html',{'user':current_user(request),'patients':patients,'expenses':expenses,'total_collection':total_collection,'total_expenses':total_expenses,'net_cash':net_cash,'start_date':start_date,'end_date':end_date})

@app.get('/result-templates', response_class=HTMLResponse)
def result_templates_page(request:Request):
    red=require_permission(request,'enter_result')
    if red: return red
    with db_conn() as con:
        templates_data=con.execute("SELECT * FROM result_templates ORDER BY template_type,shortcut").fetchall()
    return templates.TemplateResponse(request,'result_templates.html',{'user':current_user(request),'templates':templates_data})

@app.post('/result-templates')
def save_result_template(request:Request, template_type:str=Form(...), shortcut:str=Form(...), text:str=Form(...)):
    red=require_permission(request,'enter_result')
    if red: return red
    with db_conn() as con:
        con.execute("INSERT OR IGNORE INTO result_templates(template_type,shortcut,text) VALUES(?,?,?)",(template_type,shortcut,text))
        con.commit()
    return RedirectResponse('/result-templates', status_code=303)



