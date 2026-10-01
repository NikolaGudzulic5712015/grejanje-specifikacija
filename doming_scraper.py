import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import urllib.parse
import re

def fetch_oprema_za_grejanje_products(search_query="radijator", max_pages=2):
    """
    Pretražuje opremazagrejanje.rs kroz više stranica paginacije.
    """
    query_encoded = urllib.parse.quote(search_query.strip())
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "sr-RS,sr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://opremazagrejanje.rs/"
    }

    proizvodi = []
    logs = []
    session = requests.Session()

    for page in range(1, max_pages + 1):
        # Za 1. stranicu koristi osnovni URL, a za ostale /page/N/
        if page == 1:
            url = f"https://opremazagrejanje.rs/?s={query_encoded}&post_type=product&type_aws=true"
        else:
            url = f"https://opremazagrejanje.rs/page/{page}/?s={query_encoded}&post_type=product&type_aws=true"

        logs.append(f"🌐 Učitavanje Stranice {page}: {url}")

        try:
            response = session.get(url, headers=headers, timeout=12)
            logs.append(f"📡 Stranica {page} HTTP Status: {response.status_code}")

            if response.status_code != 200:
                logs.append(f"⚠️ Stranica {page} nije vraćena uspešno, prekidam dalje učitavanje.")
                break

            soup = BeautifulSoup(response.text, "html.parser")
            li_products = soup.find_all("li", class_="product")
            
            logs.append(f"🔍 Stranica {page} pronađeno artikala na strani: {len(li_products)}")

            # Ako nema više artikala na ovoj stranici, prekidamo petlju
            if not li_products:
                logs.append(f"ℹ️ Nema više artikala na stranici {page}, završavam pretragu.")
                break

            for item in li_products:
                try:
                    # 1. NAZIV ARTIKLA
                    title_tag = (
                        item.find("h2", class_="woocommerce-loop-product__title") 
                        or item.find("h2") 
                        or item.find("h3")
                        or item.find("a", class_="woocommerce-LoopProduct-link")
                    )
                    
                    if not title_tag:
                        a_tag = item.find("a")
                        naziv = a_tag.text.strip() if a_tag else None
                    else:
                        naziv = title_tag.text.strip()

                    # 2. CENA ARTIKLA
                    bdi_tags = item.find_all("bdi")
                    cena_text = None
                    if bdi_tags:
                        cena_text = bdi_tags[-1].text.strip()
                    else:
                        price_container = item.find("span", class_="price") or item.find("span", class_="woocommerce-Price-amount")
                        if price_container:
                            cena_text = price_container.text.strip()

                    if naziv and cena_text:
                        cena_clean = (
                            cena_text.replace("RSD", "")
                            .replace("rsd", "")
                            .replace("din", "")
                            .replace(".", "")
                            .replace(",", ".")
                            .replace("\xa0", "")
                            .strip()
                        )
                        
                        match = re.search(r'\d+\.?\d*', cena_clean)
                        if match:
                            cena_float = float(match.group())

                            if cena_float > 0:
                                proizvodi.append({
                                    "Kategorija": "Oprema za grejanje Uvoz",
                                    "Podkategorija": search_query.capitalize(),
                                    "Naziv": naziv,
                                    "JM": "kom",
                                    "Cena": cena_float
                                })
                except Exception:
                    continue

        except Exception as e:
            logs.append(f"❌ Greška na stranici {page}: {str(e)}")
            break

    logs.append(f"✅ Ukupno uspešno iščupano artikala sa cenom: {len(proizvodi)}")

    if proizvodi:
        df_temp = pd.DataFrame(proizvodi).drop_duplicates(subset=["Naziv"])
        return df_temp.to_dict('records'), logs

    return [], logs


def render_doming_sync_ui():
    """
    Korisnički interfejs sa opcijom izbora broja stranica za pretragu.
    """
    st.subheader("🌐 Preuzimanje artikala sa OpremaZaGrejanje.rs")
    st.markdown("Unesite pojam za pretragu i izaberite koliko stranica želiš da aplikacija automatski povuče.")

    col1, col2, col3 = st.columns([3, 1.5, 1])
    with col1:
        pojam = st.text_input("Pojam za pretragu", value="radijator")
    with col2:
        broj_stranica = st.number_input("Broj stranica", min_value=1, max_value=10, value=3, step=1)
    with col3:
        st.write(" ")
        st.write(" ")
        pokreni = st.button("🔍 Pretraži", type="primary")

    if pokreni and pojam:
        with st.spinner(f"Preuzimanje artikala sa {broj_stranica} stranica..."):
            rezultati, logs = fetch_oprema_za_grejanje_products(pojam, max_pages=broj_stranica)
            
            with st.expander("🛠️ Dijagnostički Dnevnik (Logs)", expanded=False):
                for log in logs:
                    st.text(log)

            if rezultati:
                df_novi = pd.DataFrame(rezultati)
                st.success(f"Pronađeno i preuzeto ukupno {len(rezultati)} artikala sa {broj_stranica} stranica!")
                st.dataframe(df_novi, use_container_width=True)

                if st.button("➕ Dodaj sve ove artikle u moju stalnu bazu"):
                    if "custom_db" in st.session_state:
                        st.session_state["custom_db"] = pd.concat([st.session_state["custom_db"], df_novi], ignore_index=True).drop_duplicates(subset=["Naziv"])
                        st.success("Artikli su uspešno dodati u vašu bazu materijala!")
                        st.rerun()
            else:
                st.warning("Nije pronađena cena unutar kartica proizvoda.")