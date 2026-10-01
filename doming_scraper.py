import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st

def fetch_doming_products(search_query="radijator"):
    """
    Pretražuje doming.rs i vraća listu pronađenih artikala sa cenama.
    """
    url = f"https://doming.rs/catalogsearch/result/?q={search_query}"
    
    # Zaglavlja kako bi zahtev izgledao kao da dolazi iz pravog veb pregledača
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "sr,en-US;q=0.7,en;q=0.3",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            st.error(f"Greška pri pristupu Doming.rs (Status: {response.status_code})")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        proizvodi = []

        # Pronalaženje elemenata proizvoda na stranici
        items = soup.find_all("li", class_="product-item")
        
        for item in items:
            try:
                # Naziv artikla
                title_tag = item.find("a", class_="product-item-link")
                naziv = title_tag.text.strip() if title_tag else None

                # Cena artikla
                price_tag = item.find("span", class_="price")
                cena_text = price_tag.text.strip() if price_tag else None

                if naziv and cena_text:
                    # Čišćenje cene i pretvaranje u broj
                    cena_čista = cena_text.replace("RSD", "").replace(".", "").replace(",", ".").replace("\xa0", "").strip()
                    cena_float = float(cena_čista)

                    proizvodi.append({
                        "Kategorija": "Doming.rs Uvoz",
                        "Podkategorija": search_query.capitalize(),
                        "Naziv": naziv,
                        "JM": "kom",
                        "Cena": cena_float
                    })
            except Exception:
                continue

        return proizvodi

    except Exception as e:
        st.error(f"Povezivanje sa Doming.rs nije uspelo: {e}")
        return []


def render_doming_sync_ui():
    """
    Korisnički interfejs za sinhronizaciju artikala sa Doming.rs unutar Streamlit-a.
    """
    st.subheader("🌐 Preuzimanje artikala sa Doming.rs")
    st.markdown("Unesite pojam za pretragu (npr. *radijator, cev, kotao, pumpa*) da povučete najnovije artikle i cene.")

    col1, col2 = st.columns([3, 1])
    with col1:
        pojam = st.text_input("Pojam za pretragu na Doming.rs", value="radijator")
    with col2:
        st.write(" ")
        st.write(" ")
        pokreni = st.button("🔍 Pretraži i Uvezi", type="primary")

    if pokreni and pojam:
        with st.spinner("Preuzimanje podataka sa Doming.rs..."):
            rezultati = fetch_doming_products(pojam)
            
            if rezultati:
                df_novi = pd.DataFrame(rezultati)
                st.success(f"Pronađeno i preuzeto {len(rezultati)} artikala sa Doming.rs!")
                st.dataframe(df_novi, use_container_width=True)

                if st.button("➕ Dodaj ove artikle u moju stalnu bazu"):
                    if "custom_db" in st.session_state:
                        # Spajanje novih artikala sa postojećom bazom
                        st.session_state["custom_db"] = pd.concat([st.session_state["custom_db"], df_novi], ignore_index=True).drop_duplicates(subset=["Naziv"])
                        st.success("Artikli su uspešno dodati u vašu bazu materijala!")
                        st.rerun()
            else:
                st.warning("Nije pronađen nijedan artikal za uneseni pojam ili je sajt privremeno blokirao pristup.")