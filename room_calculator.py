import streamlit as st
import pandas as pd

def get_recommended_radiator(required_watts, radiator_type="Panelni"):
    """
    Predlaže radijator na osnovu potrebne snage u Vatima (W).
    """
    # Standardne procenjene snage za panelne radijatore Tip 22 (režim 75/65/20°C)
    panel_models = [
        {"Naziv": "Panelni radijator Tip 22 600x800", "Watts": 1350, "Cena": 8200.0},
        {"Naziv": "Panelni radijator Tip 22 600x1000", "Watts": 1680, "Cena": 9500.0},
        {"Naziv": "Panelni radijator Tip 22 600x1200", "Watts": 2010, "Cena": 11000.0},
        {"Naziv": "Panelni radijator Tip 22 600x1400", "Watts": 2350, "Cena": 13200.0},
    ]
    
    # Ako je snaga veća od najvećeg radijatora, spaja više komada ili bira najveći
    for rad in panel_models:
        if rad["Watts"] >= required_watts:
            return rad["Naziv"], rad["Cena"], 1, rad["Watts"]
            
    # Ako treba više od 2350W, predlaže 2 manja radijatora
    half_watt = required_watts / 2
    for rad in panel_models:
        if rad["Watts"] >= half_watt:
            return rad["Naziv"], rad["Cena"], 2, rad["Watts"] * 2

    return panel_models[-1]["Naziv"], panel_models[-1]["Cena"], 1, panel_models[-1]["Watts"]


def render_room_calculator():
    st.header("🌡️ Proračun Toplotnih Gubitaka po Sobama")
    st.markdown("Izračunajte zapreminu i toplotne gubitke po prostorijama i automatski izaberite radijatore.")

    if "sobe_lista" not in st.session_state:
        st.session_state["sobe_lista"] = []

    # FORMA ZA UNOS PROSTORIJE
    with st.form("forma_soba", clear_on_submit=True):
        st.subheader("➕ Dodaj novu prostoriju")
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            naziv_sobe = st.text_input("Naziv prostorije", value="Dnevna soba")
            izolacija = st.selectbox(
                "Kvalitet izolacije i objekta",
                [
                    "Dobra izolacija / Nova gradnja (50 W/m³)",
                    "Standardna izolacija / Demit fasada (80 W/m³)",
                    "Bez izolacije / Starija gradnja (120 W/m³)"
                ]
            )
        
        with col_s2:
            c1, c2, c3 = st.columns(3)
            with c1:
                duzina = st.number_input("Dužina (m)", min_value=1.0, value=5.0, step=0.5)
            with c2:
                sirina = st.number_input("Širina (m)", min_value=1.0, value=4.0, step=0.5)
            with c3:
                visina = st.number_input("Visina (m)", min_value=2.0, value=2.6, step=0.1)

        submit_soba = st.form_submit_button("Sačuvaj i Izračunaj Sobu", type="primary", use_container_width=True)

    if submit_soba:
        # Određivanje koeficijenta
        if "50 W" in izolacija:
            w_per_m3 = 50
        elif "80 W" in izolacija:
            w_per_m3 = 80
        else:
            w_per_m3 = 120

        zapremina = duzina * sirina * visina
        potrebna_snaga = zapremina * w_per_m3
        
        rad_naziv, rad_cena, rad_kom, rad_snaga = get_recommended_radiator(potrebna_snaga)

        nova_soba = {
            "Soba": naziv_sobe,
            "Površina (m²)": round(duzina * sirina, 2),
            "Zapremina (m³)": round(zapremina, 2),
            "Potrebno (W)": round(potrebna_snaga, 0),
            "Preporučeni Radijator": rad_naziv,
            "Količina": rad_kom,
            "Cena (RSD)": rad_cena,
            "Ukupno (RSD)": rad_cena * rad_kom
        }
        
        st.session_state["sobe_lista"].append(nova_soba)
        st.toast(f"Dodata soba: {naziv_sobe}", icon="🔥")
        st.rerun()

    # TABELA PROSTORIJA
    if len(st.session_state["sobe_lista"]) > 0:
        st.divider()
        st.subheader("📊 Pregled proračuna po prostorijama")
        
        df_sobe = pd.DataFrame(st.session_state["sobe_lista"])
        st.dataframe(df_sobe, use_container_width=True)

        ukupno_w = df_sobe["Potrebno (W)"].sum()
        ukupno_m2 = df_sobe["Površina (m²)"].sum()
        
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Ukupna površina objekta", f"{ukupno_m2:.1f} m²")
        col_m2.metric("Ukupna potrebna snaga sistema", f"{ukupno_w:,.0f} W ({ukupno_w/1000:.1f} kW)")

        st.divider()

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("🚀 Prebaci izabrane radijatore u Glavnu Specifikaciju", type="primary", use_container_width=True):
                # Generisanje stavki za glavnu specifikaciju
                dodate_stavke = []
                for idx, row in df_sobe.iterrows():
                    dodate_stavke.append({
                        "R.b.": len(st.session_state.get("lista_stavki", [])) + idx + 1,
                        "Kategorija": "Radijatori i oprema",
                        "Naziv materijala": f"{row['Preporučeni Radijator']} ({row['Soba']})",
                        "Jedinica mere": "kom",
                        "Količina": float(row["Količina"]),
                        "Cena bez PDV (RSD)": float(row["Cena (RSD)"])
                    })
                
                if "lista_stavki" not in st.session_state:
                    st.session_state["lista_stavki"] = []
                    
                st.session_state["lista_stavki"].extend(dodate_stavke)
                st.success(f"Uspešno preneto {len(dodate_stavke)} radijatora u glavnu specifikaciju!")
        
        with col_b2:
            if st.button("🗑️ Očisti sve sobe", use_container_width=True):
                st.session_state["sobe_lista"] = []
                st.rerun()