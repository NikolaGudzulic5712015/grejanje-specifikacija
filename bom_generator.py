import streamlit as st
import pandas as pd

def get_radiator_kit(num_radiators, valve_type="straight"):
    """
    Generates required installation accessories for a given number of radiators.
    """
    valve_label = "Radijatorski ventil prav 1/2\"" if valve_type == "straight" else "Radijatorski ventil ugaoni 1/2\""
    valve_price = 850.0 if valve_type == "straight" else 920.0
    
    kit = [
        {"Kategorija": "Armatura i ventili", "Naziv": valve_label, "JM": "kom", "Količina": num_radiators, "Cena": valve_price},
        {"Kategorija": "Armatura i ventili", "Naziv": "Navijak 1/2\"", "JM": "kom", "Količina": num_radiators, "Cena": 650.0},
        {"Kategorija": "Armatura i ventili", "Naziv": "Termostatska glava M30x1.5", "JM": "kom", "Količina": num_radiators, "Cena": 1400.0},
        {"Kategorija": "Radijatori i oprema", "Naziv": "Konzole za panelne radijatore (par)", "JM": "set", "Količina": num_radiators, "Cena": 450.0},
        {"Kategorija": "Radijatori i oprema", "Naziv": "Slavina za punjenje i pražnjenje 1/2\"", "JM": "kom", "Količina": num_radiators, "Cena": 380.0},
        {"Kategorija": "Cevi i fitinzi", "Naziv": "Bakarne cevi Ø15x1mm (procenjeno)", "JM": "m", "Količina": round(num_radiators * 8.0, 1), "Cena": 450.0},
        {"Kategorija": "Cevi i fitinzi", "Naziv": "Cevna izolacija Ø15", "JM": "m", "Količina": round(num_radiators * 8.0, 1), "Cena": 85.0}
    ]
    return kit


def get_underfloor_kit(area_m2, pipe_spacing_cm=15):
    """
    Generates items required for underfloor heating based on square meters and spacing.
    """
    # Pipe requirement rule of thumb: spacing 15cm = ~6.7m pipe per m2
    m_per_m2 = 100 / pipe_spacing_cm
    pipe_length = round(area_m2 * m_per_m2, 1)
    circuits = max(1, int(round(pipe_length / 80.0))) # Max loop ~80-100m
    
    kit = [
        {"Kategorija": "Podno grejanje", "Naziv": f"Pert-Al-Pert cev Ø16x2mm ({pipe_spacing_cm}cm raster)", "JM": "m", "Količina": pipe_length, "Cena": 110.0},
        {"Kategorija": "Podno grejanje", "Naziv": f"Razdelnik sa protokomerima {circuits} kruga", "JM": "set", "Količina": 1, "Cena": 14500.0 + (circuits * 1200.0)},
        {"Kategorija": "Podno grejanje", "Naziv": "Raster ploča sa izolacijom 30mm", "JM": "m2", "Količina": round(area_m2 * 1.05, 1), "Cena": 850.0}, # 5% waste
        {"Kategorija": "Podno grejanje", "Naziv": "Dilataciona traka", "JM": "m", "Količina": round(area_m2 * 0.8, 1), "Cena": 65.0},
        {"Kategorija": "Podno grejanje", "Naziv": "Aditiv za beton / estrih", "JM": "l", "Količina": round(area_m2 * 0.2, 1), "Cena": 420.0},
        {"Kategorija": "Armatura i ventili", "Naziv": "Eurokonus spojnica Ø16x2 - 3/4\"", "JM": "kom", "Količina": circuits * 2, "Cena": 320.0}
    ]
    return kit


def get_boiler_room_kit(boiler_type, boiler_power_kw):
    """
    Generates boiler room safety & hydraulic expansion kit based on system capacity.
    """
    exp_tank_size = max(18, int(boiler_power_kw * 1.5)) # approx 1.5L per kW
    
    kit = [
        {"Kategorija": "Kotlarnica i pumpe", "Naziv": f"Cirkulaciona pumpa 25-60/180", "JM": "kom", "Količina": 1, "Cena": 12500.0},
        {"Kategorija": "Kotlarnica i pumpe", "Naziv": f"Ekspanzona posuda {exp_tank_size}L", "JM": "kom", "Količina": 1, "Cena": 3200.0 + (exp_tank_size * 80.0)},
        {"Kategorija": "Armatura i ventili", "Naziv": "Sigurnosni ventil 1/2\" 3 bar", "JM": "kom", "Količina": 1, "Cena": 750.0},
        {"Kategorija": "Armatura i ventili", "Naziv": "Automatsko odzračno lonče 1/2\"", "JM": "kom", "Količina": 2, "Cena": 620.0},
        {"Kategorija": "Armatura i ventili", "Naziv": "Loptasti slavina sa holenderom 1\"", "JM": "kom", "Količina": 4, "Cena": 1150.0},
        {"Kategorija": "Armatura i ventili", "Naziv": "Hvatač nečistoće (kosi hvatač) 1\"", "JM": "kom", "Količina": 1, "Cena": 980.0}
    ]
    
    if boiler_type == "Električni kotao":
        kit.append({"Kategorija": "Kotlarnica i pumpe", "Naziv": f"Električni kotao {boiler_power_kw}kW", "JM": "kom", "Količina": 1, "Cena": 45000.0 + (boiler_power_kw * 1200.0)})
    elif boiler_type == "Pelet kotao":
        kit.append({"Kategorija": "Kotlarnica i pumpe", "Naziv": f"Kotao na pelet {boiler_power_kw}kW sa spremnikom", "JM": "kom", "Količina": 1, "Cena": 180000.0 + (boiler_power_kw * 2500.0)})
    elif boiler_type == "Toplotna pumpa":
        kit.append({"Kategorija": "Kotlarnica i pumpe", "Naziv": f"Toplotna pumpa vazduh-voda {boiler_power_kw}kW", "JM": "kom", "Količina": 1, "Cena": 320000.0 + (boiler_power_kw * 15000.0)})
        
    return kit


def render_bom_page():
    """
    Streamlit interface renderer for the BOM Generator module.
    """
    st.header("⚡ Automatski Generator Specifikacije (BOM)")
    st.markdown("Izaberite komponente sistema da biste automatski generisali kompletnu listu materijala i pribora.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Radijatorsko Grejanje")
        enable_radiators = st.checkbox("Uključi radijatorsko grejanje", value=True)
        if enable_radiators:
            num_rads = st.number_input("Ukupan broj radijatora", min_value=1, max_value=50, value=6, step=1)
            valve_type = st.selectbox("Tip ventila", ["straight", "angled"], format_func=lambda x: "Pravi ventili" if x == "straight" else "Ugaoni ventili")
            
        st.subheader("2. Podno Grejanje")
        enable_underfloor = st.checkbox("Uključi podno grejanje", value=False)
        if enable_underfloor:
            uf_area = st.number_input("Površina podnog grejanja (m²)", min_value=5.0, max_value=500.0, value=40.0, step=5.0)
            uf_spacing = st.select_slider("Raster polaganja cevi (cm)", options=[10, 15, 20], value=15)

    with col2:
        st.subheader("3. Kotlarnica i Izvor Toplote")
        enable_boiler = st.checkbox("Uključi kotlarnicu", value=True)
        if enable_boiler:
            b_type = st.selectbox("Tip izvora toplote", ["Električni kotao", "Pelet kotao", "Toplotna pumpa"])
            b_power = st.number_input("Snaga kotla/pumpe (kW)", min_value=6, max_value=100, value=12, step=2)

    st.divider()
    
    if st.button("🚀 Generiši Kompletnu Specifikaciju", type="primary", use_container_width=True):
        generated_items = []
        
        if enable_radiators:
            generated_items.extend(get_radiator_kit(num_rads, valve_type))
            
        if enable_underfloor:
            generated_items.extend(get_underfloor_kit(uf_area, uf_spacing))
            
        if enable_boiler:
            generated_items.extend(get_boiler_room_kit(b_type, b_power))

        if generated_items:
            # Convert kit to structured table format matching main app
            formatted_list = []
            for idx, item in enumerate(generated_items, start=1):
                formatted_list.append({
                    "R.b.": idx,
                    "Naziv materijala": item["Naziv"],
                    "Jedinica mere": item["JM"],
                    "Količina": float(item["Količina"]),
                    "Cena bez PDV (RSD)": float(item["Cena"]),
                    "Ukupno bez PDV (RSD)": round(float(item["Količina"]) * float(item["Cena"]), 2)
                })
            
            # Store in session state for integration with app.py
            st.session_state["lista_stavki"] = formatted_list
            st.success(f"Uspeto generisano {len(formatted_list)} stavki u glavnu specifikaciju!")
            st.dataframe(pd.DataFrame(formatted_list), use_container_width=True)
        else:
            st.warning("Molimo označite bar jednu opciju za generisanje.")

if __name__ == "__main__":
    st.set_page_config(page_title="BOM Generator Test", layout="wide")
    render_bom_page()