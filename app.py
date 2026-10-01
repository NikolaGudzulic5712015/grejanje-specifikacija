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
    st.sidebar.error(f"Greska u bom_generator: {e}")

try:
    import room_calculator
except Exception as e:
    room_calculator = None
    st.sidebar.error(f"Greska u room_calculator: {e}")

try:
    import doming_scraper
except Exception as e:
    doming_scraper = None
    st.sidebar.error(f"Greska u doming_scraper: {e}")

# --- PODEŠAVANJE APLIKACIJE ---
st.set_page_config(page_title="Specifikacija Grejnih Instalacija Pro", layout="wide", page_icon="🔥")

st.title("🔥 Specifikacija Materijala za Grejne Instalacije (Pro)")

# --- SIDEBAR CONFIGURATION ---
st.sidebar.title("⚙️ Podešavanja & Meni")
mode = st.sidebar.radio(
    "Izaberi režim rada:", 
    [
        "📋 Ručni unos / Specifikacija", 
        "⚡ Automatski BOM Generator", 
        "🌡️ Proračun Soba & Radijatora",
        "🌐 Uvoz sa Doming.rs"
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
        {"Kategorija": "Cevi i fitinzi", "Podkategorija": "Sve", "Naziv": "Bakarne cevi Ø15x1mm", "JM": "m", "Cena": 450.0},
        {"Kategorija": "Cevi i fitinzi", "Podkategorija": "Sve", "Naziv": "Bakarne cevi Ø18x1mm", "JM": "m", "Cena": 580.0},
        {"Kategorija": "Cevi i fitinzi", "Podkategorija": "Sve", "Naziv": "Alpex cev Ø16x2mm", "JM": "m", "Cena": 120.0},
        {"Kategorija": "Armatura i ventili", "Podkategorija": "Sve", "Naziv": "Radijatorski ventil prav 1/2\"", "JM": "kom", "Cena": 850.0},
        {"Kategorija": "Armatura i ventili", "Podkategorija": "Sve", "Naziv": "Termostatska glava M30x1.5", "JM": "kom", "Cena": 1400.0},
        {"Kategorija": "Radijatori i oprema", "Podkategorija": "Panelni radijatori", "Naziv": "Panelni radijator Tip 22 600x800", "JM": "kom", "Cena": 8200.0},
        {"Kategorija": "Radijatori i oprema", "Podkategorija": "Panelni radijatori", "Naziv": "Panelni radijator Tip 22 600x1000", "JM": "kom", "Cena": 9500.0},
        {"Kategorija": "Kotlarnica i pumpe", "Podkategorija": "Sve", "Naziv": "Cirkulaciona pumpa 25-60/180", "JM": "kom", "Cena": 12500.0},
        {"Kategorija": "Kotlarnica i pumpe", "Podkategorija": "Sve", "Naziv": "Električni kotao 9kW", "JM": "kom", "Cena": 48000.0},
    ])

# --- KLASA ZA PDF GENERISANJE ---
class PDF(FPDF):
    def __init__(self, title_text='SPECIFIKACIJA MATERIJALA ZA GREJANJE', logo_bytes=None):
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
        self.set_font('Helvetica', 'B', 15)
        self.set_text_color(26, 54, 93)
        self.cell(0, 10, clean_text(self.title_text), border=0, ln=True, align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, clean_text(f'Strana {self.page_no()}'), align='C')

# --- PDF KLIJENTSKA PONUDA ---
def create_pdf(investitor, objekat, datum, df, ukupno_bez_pdv, pdv_stopa, pdv_iznos, ukupno_sa_pdv, curr_label, logo_b):
    pdf = PDF(title_text='SPECIFIKACIJA MATERIJALA ZA GREJANJE', logo_bytes=logo_b)
    pdf.add_page()
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(100, 6, clean_text(f"Investitor: {investitor}"), ln=0)
    pdf.cell(0, 6, clean_text(f"Datum: {datum.strftime('%d.%m.%Y.')}"), ln=1, align='R')
    pdf.cell(0, 6, clean_text(f"Objekat: {objekat}"), ln=1)
    pdf.ln(8)
    
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_fill_color(26, 54, 93)
    pdf.set_text_color(255, 255, 255)
    
    pdf.cell(10, 8, clean_text("R.b."), border=1, align='C', fill=True)
    pdf.cell(82, 8, clean_text("Naziv materijala / opreme"), border=1, align='L', fill=True)
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
        pdf.cell(82, 6, clean_text(str(row['Naziv materijala'])), border=1, align='L', fill=fill)
        pdf.cell(15, 6, clean_text(str(row['Jedinica mere'])), border=1, align='C', fill=fill)
        pdf.cell(18, 6, f"{row['Količina']:,.2f}", border=1, align='R', fill=fill)
        pdf.cell(30, 6, f"{row['Cena']:,.2f}", border=1, align='R', fill=fill)
        pdf.cell(35, 6, f"{row['Ukupno']:,.2f}", border=1, align='R', fill=fill)
        pdf.ln()
        fill = not fill
        
    pdf.ln(5)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(115)
    pdf.cell(40, 6, clean_text("Ukupno bez PDV:"), align='L')
    pdf.cell(35, 6, f"{ukupno_bez_pdv:,.2f} {curr_label}", align='R', ln=1)
    
    pdf.cell(115)
    pdf.cell(40, 6, clean_text(f"PDV ({pdv_stopa}%):"), align='L')
    pdf.cell(35, 6, f"{pdv_iznos:,.2f} {curr_label}", align='R', ln=1)
    
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(115)
    pdf.cell(40, 7, clean_text("UKUPNO SA PDV:"), border='T', align='L')
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
    pdf.cell(130, 8, clean_text("Naziv opreme / Pozicija ugradnje"), border=1, align='L', fill=True)
    pdf.cell(20, 8, clean_text("J.M."), border=1, align='C', fill=True)
    pdf.cell(25, 8, clean_text("Kolicina"), border=1, align='R', fill=True)
    pdf.ln()
    
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(0, 0, 0)
    fill = False
    
    for _, row in df.iterrows():
        pdf.set_fill_color(245, 247, 250)
        pdf.cell(15, 7, clean_text(str(int(row['R.b.']))), border=1, align='C', fill=fill)
        pdf.cell(130, 7, clean_text(str(row['Naziv materijala'])), border=1, align='L', fill=fill)
        pdf.cell(20, 7, clean_text(str(row['Jedinica mere'])), border=1, align='C', fill=fill)
        pdf.cell(25, 7, f"{row['Količina']:,.2f}", border=1, align='R', fill=fill)
        pdf.ln()
        fill = not fill
        
    pdf.ln(10)
    
    if napomena:
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 6, clean_text("Tehnicke napomene i instrukcije:"), ln=1)
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
elif mode == "🌐 Uvoz sa Doming.rs":
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

    # --- 3. UNOS STAVKI ---
    st.subheader("➕ Dodavanje materijala")
    db = st.session_state["custom_db"]
    kategorije = ["Ručni unos"] + sorted(list(db["Kategorija"].dropna().unique()))

    col_k1, col_k2 = st.columns(2)
    with col_k1:
        kategorija_sel = st.selectbox("1. Kategorija", kategorije)

    podkategorija_sel = "Sve"
    if kategorija_sel != "Ručni unos":
        sub_db = db[db["Kategorija"] == kategorija_sel]
        podkategorije = sorted(list(sub_db["Podkategorija"].dropna().unique()))
        if len(podkategorije) > 1 or (len(podkategorije) == 1 and podkategorije[0] != "Sve"):
            with col_k2:
                podkategorija_sel = st.selectbox("2. Tip / Podkategorija", podkategorije)

    col1, col2, col3, col4 = st.columns([3, 1, 1.5, 1.5])
    if kategorija_sel == "Ručni unos":
        with col1:
            naziv = st.text_input("Naziv materijala / opreme")
        with col2:
            jedinica = st.selectbox("J.M.", ["m", "kom", "set", "kg", "l", "paušal"])
        with col4:
            cena_input = st.number_input(f"Cena po J.M. ({valuta})", min_value=0.0, value=0.0, step=50.0)
            cena_rsd = cena_input if valuta == "RSD" else cena_input * kurs_eur
    else:
        filtered_db = db[(db["Kategorija"] == kategorija_sel) & (db["Podkategorija"] == podkategorija_sel)]
        if filtered_db.empty:
            filtered_db = db[db["Kategorija"] == kategorija_sel]

        with col1:
            naziv = st.selectbox("3. Izaberi stavku / dimenziju", filtered_db["Naziv"].unique())
        
        item_info = filtered_db[filtered_db["Naziv"] == naziv].iloc[0]
        default_jm = str(item_info["JM"])
        default_cena_rsd = float(item_info["Cena"])
        default_cena_display = default_cena_rsd if valuta == "RSD" else round(default_cena_rsd / kurs_eur, 2)
        
        with col2:
            jedinica = st.text_input("J.M.", value=default_jm)
        with col4:
            cena_input = st.number_input(f"Cena po J.M. ({valuta})", min_value=0.0, value=default_cena_display, step=1.0)
            cena_rsd = cena_input if valuta == "RSD" else cena_input * kurs_eur

    with col3:
        kolicina = st.number_input("Količina", min_value=0.01, value=1.0, step=1.0)

    if st.button("Dodaj u specifikaciju", use_container_width=True, type="primary"):
        if not naziv or str(naziv).strip() == "":
            st.error("Unesite validan naziv materijala.")
        else:
            nova_stavka = {
                "R.b.": len(st.session_state["lista_stavki"]) + 1,
                "Kategorija": kategorija_sel,
                "Naziv materijala": naziv,
                "Jedinica mere": jedinica,
                "Količina": float(kolicina),
                "Cena bez PDV (RSD)": float(cena_rsd),
            }
            st.session_state["lista_stavki"].append(nova_stavka)
            st.toast(f"Dodato: {naziv}", icon="✅")
            st.rerun()

    st.divider()

    # --- 4. TABELA I PRORAČUNI ---
    st.subheader("📊 Pregled specifikacije")

    if len(st.session_state["lista_stavki"]) > 0:
        df = pd.DataFrame(st.session_state["lista_stavki"])
        df["R.b."] = range(1, len(df) + 1)
        
        df["Cena"] = df["Cena bez PDV (RSD)"] if valuta == "RSD" else (df["Cena bez PDV (RSD)"] / kurs_eur).round(2)
        df["Ukupno"] = (df["Količina"] * df["Cena"]).round(2)
        
        edited_df = st.data_editor(
            df[["R.b.", "Naziv materijala", "Jedinica mere", "Količina", "Cena", "Ukupno"]],
            num_rows="dynamic",
            use_container_width=True,
            key="editor_specifikacija",
            column_config={
                "R.b.": st.column_config.NumberColumn(disabled=True),
                "Ukupno": st.column_config.NumberColumn(disabled=True, format=f"%.2f {valuta}")
            }
        )
        
        ukupno_bez_pdv = float(edited_df["Ukupno"].sum())
        pdv_stopa = st.slider("Stopa PDV-a (%)", min_value=0, max_value=30, value=20)
        pdv_iznos = ukupno_bez_pdv * (pdv_stopa / 100)
        ukupno_sa_pdv = ukupno_bez_pdv + pdv_iznos
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric(f"Ukupno BEZ PDV ({valuta})", f"{ukupno_bez_pdv:,.2f} {valuta}")
        col_m2.metric(f"PDV ({pdv_stopa}%)", f"{pdv_iznos:,.2f} {valuta}")
        col_m3.metric(f"UKUPNO SA PDV-om", f"{ukupno_sa_pdv:,.2f} {valuta}")
        
        st.divider()

        # --- 5. TEHNIČKA NAPOMENA ZA RADNI NALOG ---
        st.subheader("📝 Napomena za Radni Nalog Montera")
        radni_nalog_napomena = st.text_area(
            "Uputstva za montažu (npr. 'Ispitati pritisak na 6 bar', 'Montirati razdelnik u hodniku na visini 60cm')",
            value="Obavezno izvršiti pritisnu probu pre zatvaranja kanala i estriha."
        )

        st.divider()

        # --- 6. IZVOZ PODATAKA ---
        st.subheader("📥 Preuzimanje Dokumenata")
        col_exp1, col_exp2, col_exp3 = st.columns([1, 1, 1])
        
        pdf_ponuda = create_pdf(investitor, objekat, datum, edited_df, ukupno_bez_pdv, pdv_stopa, pdv_iznos, ukupno_sa_pdv, valuta, logo_file)
        with col_exp1:
            st.download_button(
                label="📄 PDF Ponuda (sa cenama)",
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
            edited_df.to_excel(writer, sheet_name="Specifikacija", index=False)

        with col_exp3:
            st.download_button(
                label=f"📊 Excel (.xlsx)",
                data=excel_output.getvalue(),
                file_name=f"Specifikacija_{investitor.replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        st.divider()
        if st.button("🗑️ Očisti celu tabelu", use_container_width=True):
            st.session_state["lista_stavki"] = []
            st.rerun()

    else:
        st.info("Specifikacija je trenutno prazna. Dodajte stavke ručno ili generišite preko BOM / Room / Doming kalkulatora.")