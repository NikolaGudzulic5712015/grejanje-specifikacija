import streamlit as st
import pandas as pd
import json
from io import BytesIO
from fpdf import FPDF
import datetime

# --- IMPORTUJEMO SVE DODATNE MODULE ---
try:
    import bom_generator
except Exception as e:
    bom_generator = None
    st.sidebar.error(f"Greška u bom_generator: {e}")

try:
    import room_calculator
except Exception as e:
    room_calculator = None
    st.sidebar.error(f"Greška u room_calculator: {e}")

try:
    import doming_scraper
except Exception as e:
    doming_scraper = None
    st.sidebar.error(f"Greška u doming_scraper: {e}")

# --- PODEŠAVANJE APLIKACIJE ---
st.set_page_config(page_title="Specifikacija Grejnih Instalacija Pro", layout="wide", page_icon="🔥")

st.title("🔥 Specifikacija Materijala i Radova za Grejne Instalacije (Pro)")

# --- SIDEBAR CONFIGURATION ---
st.sidebar.title("⚙️ Podešavanja & Meni")
mode = st.sidebar.radio(
    "Izaberi režim rada:", 
    [
        "📋 Unos Specifikacije (Materijal & Radovi)", 
        "⚡ Automatski BOM Generator", 
        "🌡️ Proračun Soba & Radijatora",
        "🌐 Uvoz sa OpremaZaGrejanje.rs"
    ]
)

st.sidebar.divider()

# 1. VALUTA I KURS
st.sidebar.subheader("💱 Valuta i Kurs")
valuta = st.sidebar.selectbox("Izaberi primarnu valutu:", ["RSD", "EUR"])
kurs_eur = st.sidebar.number_input("Kurs EUR -> RSD", value=117.2, step=0.1)

# 2. LOGO ZA PDF
st.sidebar.subheader("🖼️ Brendiranje PDF-a")
logo_file = st.sidebar.file_uploader("Otpremi logo firme (PNG/JPG)", type=["png", "jpg", "jpeg"])

# --- POMOĆNA FUNKCIJA ZA BEZBEDAN TEKST U PDF-u ---
def clean_text(text):
    if not isinstance(text, str):
        text = str(text)
    zamene = {
        'č': 'c', 'Č': 'C',
        'ć': 'c', 'Ć': 'C',
        'đ': 'dj', 'Đ': 'Dj',
        'š': 's', 'Š': 'S',
        'ž': 'z', 'Ž': 'Z'
    }
    for k, v in zamene.items():
        text = text.replace(k, v)
    return text

# --- INICIJALIZACIJA SESSION STATE-A ---
if "lista_stavki" not in st.session_state:
    st.session_state["lista_stavki"] = []

if "custom_db" not in st.session_state:
    st.session_state["custom_db"] = pd.DataFrame([
        # BAZA MATERIJALA
        {"Tip": "Materijal", "Kategorija": "Cevi i fitinzi", "Naziv": "Bakarne cevi Ø15x1mm", "JM": "m", "Cena": 450.0},
        {"Tip": "Materijal", "Kategorija": "Cevi i fitinzi", "Naziv": "Bakarne cevi Ø18x1mm", "JM": "m", "Cena": 580.0},
        {"Tip": "Materijal", "Kategorija": "Cevi i fitinzi", "Naziv": "Alpex cev Ø16x2mm", "JM": "m", "Cena": 120.0},
        {"Tip": "Materijal", "Kategorija": "Armatura i ventili", "Naziv": "Radijatorski ventil prav 1/2\"", "JM": "kom", "Cena": 850.0},
        {"Tip": "Materijal", "Kategorija": "Armatura i ventili", "Naziv": "Termostatska glava M30x1.5", "JM": "kom", "Cena": 1400.0},
        {"Tip": "Materijal", "Kategorija": "Radijatori i oprema", "Naziv": "Panelni radijator Tip 22 600x800", "JM": "kom", "Cena": 8200.0},
        {"Tip": "Materijal", "Kategorija": "Radijatori i oprema", "Naziv": "Panelni radijator Tip 22 600x1000", "JM": "kom", "Cena": 9500.0},
        {"Tip": "Materijal", "Kategorija": "Kotlarnica i pumpe", "Naziv": "Cirkulaciona pumpa 25-60/180", "JM": "kom", "Cena": 12500.0},
        {"Tip": "Materijal", "Kategorija": "Kotlarnica i pumpe", "Naziv": "Električni kotao 9kW", "JM": "kom", "Cena": 48000.0},
        # BEOGRADSKA BAZA RADOVA / MONTAŽE
        {"Tip": "Radovi", "Kategorija": "Montažni radovi", "Naziv": "Montaža radijatora sa izradom priključaka i ventilima", "JM": "kom", "Cena": 7000.0},
        {"Tip": "Radovi", "Kategorija": "Montažni radovi", "Naziv": "Montaža razdelnog ormara sa sabirnicom", "JM": "kom", "Cena": 6000.0},
        {"Tip": "Radovi", "Kategorija": "Montažni radovi", "Naziv": "Montaža, povezivanje i puštanje u rad kotla", "JM": "kom", "Cena": 14000.0},
        {"Tip": "Radovi", "Kategorija": "Podno grejanje", "Naziv": "Izrada podnog grejanja (stiropor/raster + cevi)", "JM": "m2", "Cena": 1400.0},
        {"Tip": "Radovi", "Kategorija": "Ispitivanje", "Naziv": "Pritisna proba i punjenje sistema", "JM": "paušal", "Cena": 6000.0},
    ])

# --- KLASA ZA PDF GENERISANJE ---
class PDF(FPDF):
    def __init__(self, title_text='SPECIFIKACIJA MATERIJALA I RADOVA', logo_bytes=None):
        super().__init__()
        self.logo_bytes = logo_bytes
        self.title_text = title_text

    def header(self):
        if self.logo_bytes:
            try:
                with open("temp_logo.png", "wb") as f:
                    f.write(self.logo_bytes.getvalue())
                self.image("temp_logo.png", 10, 8, 33)
            except Exception:
                pass
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(26, 54, 93)
        self.cell(0, 10, clean_text(self.title_text), border=0, ln=True, align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, clean_text(f'Strana {self.page_no()}'), align='C')

# --- PDF KLIJENTSKA PONUDA ---
def create_pdf(investitor, objekat, datum, df, ukupno_mat, ukupno_rad, ukupno_bez_pdv, pdv_stopa, pdv_iznos, ukupno_sa_pdv, curr_label, logo_b):
    pdf = PDF(title_text='PONUDA ZA IZRADU GREJNE INSTALACIJE', logo_bytes=logo_b)
    pdf.add_page()
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(100, 6, clean_text(f"Investitor: {investitor}"), ln=0)
    pdf.cell(0, 6, clean_text(f"Datum: {datum.strftime('%d.%m.%Y.')}"), ln=1, align='R')
    pdf.cell(0, 6, clean_text(f"Objekat: {objekat}"), ln=1)
    pdf.ln(6)
    
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_fill_color(26, 54, 93)
    pdf.set_text_color(255, 255, 255)
    
    pdf.cell(10, 8, clean_text("R.b."), border=1, align='C', fill=True)
    pdf.cell(20, 8, clean_text("Tip"), border=1, align='C', fill=True)
    pdf.cell(62, 8, clean_text("Opis materijala / radova"), border=1, align='L', fill=True)
    pdf.cell(15, 8, clean_text("J.M."), border=1, align='C', fill=True)
    pdf.cell(18, 8, clean_text("Kolicina"), border=1, align='R', fill=True)
    pdf.cell(30, 8, clean_text(f"Cena ({curr_label})"), border=1, align='R', fill=True)
    pdf.cell(35, 8, clean_text(f"Ukupno ({curr_label})"), border=1, align='R', fill=True)
    pdf.ln()
    
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(0, 0, 0)
    fill = False
    
    for _, row in df.iterrows():
        pdf.set_fill_color(247, 250, 252)
        pdf.cell(10, 6, clean_text(str(int(row['R.b.']))), border=1, align='C', fill=fill)
        pdf.cell(20, 6, clean_text(str(row.get('Tip', 'Materijal'))), border=1, align='C', fill=fill)
        pdf.cell(62, 6, clean_text(str(row['Naziv stavke'])), border=1, align='L', fill=fill)
        pdf.cell(15, 6, clean_text(str(row['Jedinica mere'])), border=1, align='C', fill=fill)
        pdf.cell(18, 6, f"{row['Količina']:,.2f}", border=1, align='R', fill=fill)
        pdf.cell(30, 6, f"{row['Cena']:,.2f}", border=1, align='R', fill=fill)
        pdf.cell(35, 6, f"{row['Ukupno']:,.2f}", border=1, align='R', fill=fill)
        pdf.ln()
        fill = not fill
        
    pdf.ln(5)
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(115)
    pdf.cell(40, 5, clean_text("Ukupno Materijal:"), align='L')
    pdf.cell(35, 5, f"{ukupno_mat:,.2f} {curr_label}", align='R', ln=1)
    
    pdf.cell(115)
    pdf.cell(40, 5, clean_text("Ukupno Radovi / Montaza:"), align='L')
    pdf.cell(35, 5, f"{ukupno_rad:,.2f} {curr_label}", align='R', ln=1)

    pdf.line(125, pdf.get_y()+1, 200, pdf.get_y()+1)
    pdf.ln(2)

    pdf.cell(115)
    pdf.cell(40, 5, clean_text("Ukupno BEZ PDV:"), align='L')
    pdf.cell(35, 5, f"{ukupno_bez_pdv:,.2f} {curr_label}", align='R', ln=1)

    pdf.cell(115)
    pdf.cell(40, 5, clean_text(f"PDV ({pdv_stopa}%):"), align='L')
    pdf.cell(35, 5, f"{pdv_iznos:,.2f} {curr_label}", align='R', ln=1)
    
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(115)
    pdf.cell(40, 7, clean_text("UKUPNO SA PDV-om:"), border='T', align='L')
    pdf.cell(35, 7, f"{ukupno_sa_pdv:,.2f} {curr_label}", border='T', align='R', ln=1)
    
    return bytes(pdf.output())

# --- PDF RADNI NALOG ZA MONTERE (BEZ CENA) ---
def create_work_order_pdf(investitor, objekat, datum, df, napomena, logo_b):
    pdf = PDF(title_text='RADNI NALOG / TEHNICKA SPECIFIKACIJA', logo_bytes=logo_b)
    pdf.add_page()
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(100, 6, clean_text(f"Investitor / Klijent: {investitor}"), ln=0)
    pdf.cell(0, 6, clean_text(f"Datum izdavanja: {datum.strftime('%d.%m.%Y.')}"), ln=1, align='R')
    pdf.cell(0, 6, clean_text(f"Lokacija / Objekat: {objekat}"), ln=1)
    pdf.ln(8)
    
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_fill_color(44, 62, 80)
    pdf.set_text_color(255, 255, 255)
    
    pdf.cell(15, 8, clean_text("R.b."), border=1, align='C', fill=True)
    pdf.cell(20, 8, clean_text("Tip"), border=1, align='C', fill=True)
    pdf.cell(110, 8, clean_text("Naziv opreme / Pozicija ugradnje"), border=1, align='L', fill=True)
    pdf.cell(20, 8, clean_text("J.M."), border=1, align='C', fill=True)
    pdf.cell(25, 8, clean_text("Kolicina"), border=1, align='R', fill=True)
    pdf.ln()
    
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(0, 0, 0)
    fill = False
    
    for _, row in df.iterrows():
        pdf.set_fill_color(245, 247, 250)
        pdf.cell(15, 7, clean_text(str(int(row['R.b.']))), border=1, align='C', fill=fill)
        pdf.cell(20, 7, clean_text(str(row.get('Tip', 'Materijal'))), border=1, align='C', fill=fill)
        pdf.cell(110, 7, clean_text(str(row['Naziv stavke'])), border=1, align='L', fill=fill)
        pdf.cell(20, 7, clean_text(str(row['Jedinica mere'])), border=1, align='C', fill=fill)
        pdf.cell(25, 7, f"{row['Količina']:,.2f}", border=1, align='R', fill=fill)
        pdf.ln()
        fill = not fill
        
    pdf.ln(10)
    
    if napomena:
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 6, clean_text("Tehnicke napomene i instrukcije za montere:"), ln=1)
        pdf.set_font('Helvetica', '', 9)
        pdf.multi_cell(0, 5, clean_text(napomena), border=1)
        pdf.ln(15)
        
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(90, 6, clean_text("Radove izveo (Potpis montera): __________________"), ln=0)
    pdf.cell(0, 6, clean_text("Opremu preuzeo / Potvrdio: __________________"), ln=1, align='R')
    
    return bytes(pdf.output())

# --- ROUTING REŽIMA RADA ---
if mode == "⚡ Automatski BOM Generator":
    if bom_generator:
        bom_generator.render_bom_page()
    else:
        st.error("Fajl 'bom_generator.py' nije pronađen u istom folderu!")
elif mode == "🌡️ Proračun Soba & Radijatora":
    if room_calculator:
        room_calculator.render_room_calculator()
    else:
        st.error("Fajl 'room_calculator.py' nije pronađen u istom folderu!")
elif mode == "🌐 Uvoz sa OpremaZaGrejanje.rs":
    if doming_scraper:
        doming_scraper.render_doming_sync_ui()
    else:
        st.error("Fajl 'doming_scraper.py' nije pronađen u istom folderu!")
else:
    # --- 1. PROJEKTI: UČITAVANJE / ČUVANJE (JSON) ---
    with st.expander("📂 Upravljanje Projektima (Save / Load Project)", expanded=False):
        col_file1, col_file2 = st.columns(2)
        with col_file1:
            uploaded_proj = st.file_uploader("Učitaj postojeći projektni fajl (.json)", type=["json"])
            if uploaded_proj is not None:
                try:
                    proj_data = json.load(uploaded_proj)
                    st.session_state["investitor_val"] = proj_data.get("investitor", "")
                    st.session_state["objekat_val"] = proj_data.get("objekat", "")
                    st.session_state["lista_stavki"] = proj_data.get("lista_stavki", [])
                    st.success("Projekat je uspešno učitan!")
                except Exception as e:
                    st.error(f"Greška pri učitavanju projekta: {e}")

    # --- 2. PODACI O PROJEKTU ---
    with st.expander("📋 Podaci o objektu / investitoru", expanded=True):
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            investitor = st.text_input("Investitor / Klijent", value=st.session_state.get("investitor_val", "Petar Petrović"))
        with col_p2:
            objekat = st.text_input("Lokacija / Objekat", value=st.session_state.get("objekat_val", "Porodična kuća - Beograd"))
        with col_p3:
            datum = st.date_input("Datum izrade", datetime.date.today())

        proj_dict = {
            "investitor": investitor,
            "objekat": objekat,
            "datum": str(datum),
            "lista_stavki": st.session_state["lista_stavki"]
        }
        st.download_button(
            label="💾 Sačuvaj projekat (JSON)",
            data=json.dumps(proj_dict, indent=4, ensure_ascii=False),
            file_name=f"Projekat_{investitor.replace(' ', '_')}.json",
            mime="application/json"
        )

    st.divider()

    # --- 3. TABOVI ZA DODAVANJE MATERIJALA I RADOVA ---
    tab_mat, tab_rad = st.tabs(["📦 Dodaj Materijal", "🛠️ Dodaj Radove / Ugradnju"])

    # --- TAB 1: DODAVANJE MATERIJALA ---
    with tab_mat:
        db = st.session_state["custom_db"].copy()
        db_mat = db[db.get("Tip", "Materijal") == "Materijal"]

        col_f1, col_f2 = st.columns([2, 2])
        sve_kategorije = ["Sve kategorije", "Ručni unos"] + sorted(list(db_mat["Kategorija"].dropna().unique()))
        with col_f1:
            kat_filter = st.selectbox("📁 Kategorija materijala:", sve_kategorije)

        if kat_filter == "Ručni unos":
            col1, col2, col3, col4 = st.columns([3, 1, 1.5, 1.5])
            with col1:
                naziv = st.text_input("Naziv materijala")
            with col2:
                jedinica = st.selectbox("J.M.", ["m", "kom", "set", "kg", "l", "paušal"], key="jm_mat_manual")
            with col3:
                kolicina = st.number_input("Količina", min_value=0.01, value=1.0, step=1.0, key="qty_mat_manual")
            with col4:
                cena_input = st.number_input(f"Cena ({valuta})", min_value=0.0, value=0.0, step=50.0, key="price_mat_manual")
                cena_rsd = cena_input if valuta == "RSD" else cena_input * kurs_eur

            if st.button("➕ Dodaj ručni materijal u specifikaciju", type="primary"):
                if naziv.strip():
                    st.session_state["lista_stavki"].append({
                        "R.b.": len(st.session_state["lista_stavki"]) + 1,
                        "Tip": "Materijal",
                        "Naziv stavke": naziv,
                        "Jedinica mere": jedinica,
                        "Količina": float(kolicina),
                        "Cena bez PDV (RSD)": float(cena_rsd)
                    })
                    st.toast(f"Dodato: {naziv}", icon="✅")
                    st.rerun()

        else:
            db_filtered = db_mat[db_mat["Kategorija"] == kat_filter] if kat_filter != "Sve kategorije" else db_mat.copy()
            with col_f2:
                search_query = st.text_input("🔎 Pametna pretraga materijala:", value="", key="search_mat")

            if search_query.strip():
                for kw in search_query.lower().split():
                    db_filtered = db_filtered[db_filtered["Naziv"].str.lower().str.contains(kw, na=False)]

            st.caption(f"Pronađeno artikala: **{len(db_filtered)}**")

            if not db_filtered.empty:
                col_sel1, col_sel2, col_sel3, col_sel4 = st.columns([3.5, 1, 1.5, 1.5])
                with col_sel1:
                    selected_naziv = st.selectbox("Izaberi artikal:", db_filtered["Naziv"].unique(), key="sel_mat")
                
                item_info = db_filtered[db_filtered["Naziv"] == selected_naziv].iloc[0]
                default_jm = str(item_info["JM"])
                default_cena_rsd = float(item_info["Cena"])
                default_cena_display = default_cena_rsd if valuta == "RSD" else round(default_cena_rsd / kurs_eur, 2)
                
                with col_sel2:
                    jedinica = st.text_input("J.M.", value=default_jm, key="jm_mat_auto")
                with col_sel3:
                    kolicina = st.number_input("Količina", min_value=0.01, value=1.0, step=1.0, key="qty_mat_auto")
                with col_sel4:
                    cena_input = st.number_input(f"Cena ({valuta})", min_value=0.0, value=default_cena_display, step=1.0, key="price_mat_auto")
                    cena_rsd = cena_input if valuta == "RSD" else cena_input * kurs_eur

                if st.button("➕ Dodaj materijal u specifikaciju", type="primary"):
                    st.session_state["lista_stavki"].append({
                        "R.b.": len(st.session_state["lista_stavki"]) + 1,
                        "Tip": "Materijal",
                        "Naziv stavke": selected_naziv,
                        "Jedinica mere": jedinica,
                        "Količina": float(kolicina),
                        "Cena bez PDV (RSD)": float(cena_rsd)
                    })
                    st.toast(f"Dodato: {selected_naziv}", icon="✅")
                    st.rerun()

    # --- TAB 2: DODAVANJE RADOVA / UGRADNJE ---
    with tab_rad:
        db_radovi = db[db.get("Tip", "") == "Radovi"]

        col_r1, col_r2 = st.columns([2, 2])
        with col_r1:
            rad_izbor_tip = st.radio("Način dodavanja radova:", ["Iz baze radova", "Paušalni procenat na materijal", "Ručni unos rada"])

        if rad_izbor_tip == "Paušalni procenat na materijal":
            trenutni_mat_rsd = sum(s["Količina"] * s["Cena bez PDV (RSD)"] for s in st.session_state["lista_stavki"] if s.get("Tip") == "Materijal")
            trenutni_mat_valuta = trenutni_mat_rsd if valuta == "RSD" else trenutni_mat_rsd / kurs_eur

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                procenat_ruke = st.slider("Procenat za ugradnju/ruke (% od materijala)", min_value=5, max_value=50, value=20, step=1)
            with col_p2:
                iznos_radova = (trenutni_mat_valuta * (procenat_ruke / 100))
                st.metric("Proračunat iznos radova", f"{iznos_radova:,.2f} {valuta}")

            if st.button("➕ Dodaj paušalne radove u specifikaciju", type="primary"):
                st.session_state["lista_stavki"].append({
                    "R.b.": len(st.session_state["lista_stavki"]) + 1,
                    "Tip": "Radovi",
                    "Naziv stavke": f"Montažni radovi i ugradnja ({procenat_ruke}% na materijal)",
                    "Jedinica mere": "paušal",
                    "Količina": 1.0,
                    "Cena bez PDV (RSD)": iznos_radova if valuta == "RSD" else iznos_radova * kurs_eur
                })
                st.toast("Dodati paušalni radovi!", icon="✅")
                st.rerun()

        elif rad_izbor_tip == "Ručni unos rada":
            col_u1, col_u2, col_u3, col_u4 = st.columns([3, 1, 1.5, 1.5])
            with col_u1:
                naziv_rada = st.text_input("Naziv radova / pozicije")
            with col_u2:
                jm_rada = st.selectbox("J.M.", ["paušal", "kom", "m", "m2", "čas"], key="jm_rad_manual")
            with col_u3:
                kol_rada = st.number_input("Količina", min_value=0.01, value=1.0, step=1.0, key="qty_rad_manual")
            with col_u4:
                cena_rad_input = st.number_input(f"Cena po J.M. ({valuta})", min_value=0.0, value=0.0, step=500.0, key="price_rad_manual")
                cena_rad_rsd = cena_rad_input if valuta == "RSD" else cena_rad_input * kurs_eur

            if st.button("➕ Dodaj radove u specifikaciju", type="primary"):
                if naziv_rada.strip():
                    st.session_state["lista_stavki"].append({
                        "R.b.": len(st.session_state["lista_stavki"]) + 1,
                        "Tip": "Radovi",
                        "Naziv stavke": naziv_rada,
                        "Jedinica mere": jm_rada,
                        "Količina": float(kol_rada),
                        "Cena bez PDV (RSD)": float(cena_rad_rsd)
                    })
                    st.toast(f"Dodato: {naziv_rada}", icon="✅")
                    st.rerun()

        else: # Iz baze radova
            if not db_radovi.empty:
                col_b1, col_b2, col_b3, col_b4 = st.columns([3.5, 1, 1.5, 1.5])
                with col_b1:
                    sel_rad_naziv = st.selectbox("Izaberi uslugu/rad:", db_radovi["Naziv"].unique())
                
                item_rad = db_radovi[db_radovi["Naziv"] == sel_rad_naziv].iloc[0]
                def_rad_jm = str(item_rad["JM"])
                def_rad_cena_rsd = float(item_rad["Cena"])
                def_rad_cena_disp = def_rad_cena_rsd if valuta == "RSD" else round(def_rad_cena_rsd / kurs_eur, 2)

                with col_b2:
                    jm_rada_b = st.text_input("J.M.", value=def_rad_jm, key="jm_rad_b")
                with col_b3:
                    kol_rada_b = st.number_input("Količina", min_value=0.01, value=1.0, step=1.0, key="qty_rad_b")
                with col_b4:
                    cena_rad_b = st.number_input(f"Cena ({valuta})", min_value=0.0, value=def_rad_cena_disp, step=100.0, key="price_rad_b")
                    cena_rad_rsd_b = cena_rad_b if valuta == "RSD" else cena_rad_b * kurs_eur

                if st.button("➕ Dodaj izabrani rad u specifikaciju", type="primary"):
                    st.session_state["lista_stavki"].append({
                        "R.b.": len(st.session_state["lista_stavki"]) + 1,
                        "Tip": "Radovi",
                        "Naziv stavke": sel_rad_naziv,
                        "Jedinica mere": jm_rada_b,
                        "Količina": float(kol_rada_b),
                        "Cena bez PDV (RSD)": float(cena_rad_rsd_b)
                    })
                    st.toast(f"Dodato: {sel_rad_naziv}", icon="✅")
                    st.rerun()

    st.divider()

    # --- 4. TABELA I PRORAČUNI ---
    st.subheader("📊 Pregled ponude (Materijal + Radovi)")

    if len(st.session_state["lista_stavki"]) > 0:
        df = pd.DataFrame(st.session_state["lista_stavki"])
        df["R.b."] = range(1, len(df) + 1)
        
        df["Cena"] = df["Cena bez PDV (RSD)"] if valuta == "RSD" else (df["Cena bez PDV (RSD)"] / kurs_eur).round(2)
        df["Ukupno"] = (df["Količina"] * df["Cena"]).round(2)
        
        edited_df = st.data_editor(
            df[["R.b.", "Tip", "Naziv stavke", "Jedinica mere", "Količina", "Cena", "Ukupno"]],
            num_rows="dynamic",
            use_container_width=True,
            key="editor_specifikacija",
            column_config={
                "R.b.": st.column_config.NumberColumn(disabled=True),
                "Tip": st.column_config.SelectboxColumn("Tip", options=["Materijal", "Radovi"]),
                "Ukupno": st.column_config.NumberColumn(disabled=True, format=f"%.2f {valuta}")
            }
        )
        
        # Razdvajanje ukupnih suma za Materijal i Radove
        df_mat_only = edited_df[edited_df["Tip"] == "Materijal"]
        df_rad_only = edited_df[edited_df["Tip"] == "Radovi"]

        ukupno_mat = float(df_mat_only["Ukupno"].sum()) if not df_mat_only.empty else 0.0
        ukupno_rad = float(df_rad_only["Ukupno"].sum()) if not df_rad_only.empty else 0.0
        
        ukupno_bez_pdv = ukupno_mat + ukupno_rad
        pdv_stopa = st.slider("Stopa PDV-a (%)", min_value=0, max_value=30, value=20)
        pdv_iznos = ukupno_bez_pdv * (pdv_stopa / 100)
        ukupno_sa_pdv = ukupno_bez_pdv + pdv_iznos
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric(f"Ukupno Materijal ({valuta})", f"{ukupno_mat:,.2f} {valuta}")
        col_m2.metric(f"Ukupno Radovi ({valuta})", f"{ukupno_rad:,.2f} {valuta}")
        col_m3.metric(f"Ukupno BEZ PDV ({valuta})", f"{ukupno_bez_pdv:,.2f} {valuta}")
        col_m4.metric(f"UKUPNO SA PDV-om", f"{ukupno_sa_pdv:,.2f} {valuta}")
        
        st.divider()

        # --- 5. TEHNIČKA NAPOMENA ZA RADNI NALOG ---
        st.subheader("📝 Napomena za Radni Nalog Montera")
        radni_nalog_napomena = st.text_area(
            "Uputstva za montažu",
            value="Obavezno izvršiti pritisnu probu pre zatvaranja kanala i estriha."
        )

        st.divider()

        # --- 6. IZVOZ PODATAKA ---
        st.subheader("📥 Preuzimanje Dokumenata")
        col_exp1, col_exp2, col_exp3 = st.columns([1, 1, 1])
        
        pdf_ponuda = create_pdf(investitor, objekat, datum, edited_df, ukupno_mat, ukupno_rad, ukupno_bez_pdv, pdv_stopa, pdv_iznos, ukupno_sa_pdv, valuta, logo_file)
        with col_exp1:
            st.download_button(
                label="📄 PDF Ponuda (Materijal + Radovi)",
                data=pdf_ponuda,
                file_name=f"Ponuda_{investitor.replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        pdf_nalog = create_work_order_pdf(investitor, objekat, datum, edited_df, radni_nalog_napomena, logo_file)
        with col_exp2:
            st.download_button(
                label="🔧 Radni Nalog za Montere",
                data=pdf_nalog,
                file_name=f"Radni_Nalog_{investitor.replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        excel_output = BytesIO()
        with pd.ExcelWriter(excel_output, engine='xlsxwriter') as writer:
            edited_df.to_excel(writer, sheet_name="Ponuda", index=False)

        with col_exp3:
            st.download_button(
                label=f"📊 Excel (.xlsx)",
                data=excel_output.getvalue(),
                file_name=f"Ponuda_{investitor.replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        st.divider()
        if st.button("🗑️ Očisti celu tabelu", use_container_width=True):
            st.session_state["lista_stavki"] = []
            st.rerun()

    else:
        st.info("Specifikacija je trenutno prazna. Dodajte materijal ili radove preko gornjih tabova.")