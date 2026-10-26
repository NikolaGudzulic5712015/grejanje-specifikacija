import streamlit as st
import pandas as pd
import json
import os
import datetime

DATA_FILE = "evidencija_poslova.json"

STATUSI = [
    "🟡 Ponuda poslata",
    "🔵 Ugovoreno / Čeka se avans",
    "🟠 U radu na terenu",
    "🟢 Završeno i naplaćeno",
    "🔴 Otkazano"
]

def load_poslovi():
    """Učitava sve poslove iz lokalnog JSON fajla."""
    if not os.path.exists(DATA_FILE):
        # Inicijalni ogledni primeri ako je fajl nov
        primeri = [
            {
                "id": 1,
                "klijent": "Petar Petrović",
                "telefon": "+381641234567",
                "objekat": "Porodična kuća, Voždovac",
                "status": "🟠 U radu na terenu",
                "rok_zavrsetka": str(datetime.date.today() + datetime.timedelta(days=7)),
                "odgovorni_majstor": "Ekipa 1 (Milan i Zoran)",
                "cena_ponude_eur": 4500.0,
                "trosak_nabavke_mat_eur": 2800.0,
                "trosak_pomocnika_eur": 400.0,
                "napomena": "Čeka se završetak košuljice na spratu."
            },
            {
                "id": 2,
                "klijent": "Marko Janković",
                "telefon": "+381639876543",
                "objekat": "Stan 85m2, Novi Beograd",
                "status": "🟢 Završeno i naplaćeno",
                "rok_zavrsetka": str(datetime.date.today() - datetime.timedelta(days=2)),
                "odgovorni_majstor": "Samostalno",
                "cena_ponude_eur": 2100.0,
                "trosak_nabavke_mat_eur": 1250.0,
                "trosak_pomocnika_eur": 150.0,
                "napomena": "Izvršena pritisna proba na 6 bar."
            }
        ]
        save_poslovi(primeri)
        return primeri

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_poslovi(poslovi):
    """Čuva listu poslova u JSON fajl."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(poslovi, f, indent=4, ensure_ascii=False)

def render_master_dashboard():
    st.subheader("👷 Majstorska Kontrolna Tabla & Evidencija Poslova")
    st.caption("Interni uvid u objekte, terenske ekipe, troškove nabavke i čistu zaradu.")

    poslovi = load_poslovi()
    df = pd.DataFrame(poslovi)

    if not df.empty:
        # Izračunavanje zarade
        df["profit_eur"] = df["cena_ponude_eur"] - (df["trosak_nabavke_mat_eur"] + df["trosak_pomocnika_eur"])
        df["profit_marza_proc"] = ((df["profit_eur"] / df["cena_ponude_eur"]) * 100).round(1)

        # --- GLAVNE FINANSIJSKE METRIKE NA VRHU ---
        ukupno_ugovoreno = df[df["status"] != "🔴 Otkazano"]["cena_ponude_eur"].sum()
        ukupni_troskovi = (df[df["status"] != "🔴 Otkazano"]["trosak_nabavke_mat_eur"] + df[df["status"] != "🔴 Otkazano"]["trosak_pomocnika_eur"]).sum()
        cist_profit = ukupno_ugovoreno - ukupni_troskovi
        aktivni_poslovi = len(df[df["status"].isin(["🔵 Ugovoreno / Čeka se avans", "🟠 U radu na terenu"])])

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Aktivna gradilišta", f"{aktivni_poslovi}")
        m2.metric("Ukupna vrednost poslova", f"{ukupno_ugovoreno:,.0f} €")
        m3.metric("Ukupni troškovi (nabavka + pomoćnici)", f"{ukupni_troskovi:,.0f} €")
        m4.metric("💰 ČIST PROFIT", f"{cist_profit:,.0f} €")

        st.divider()

    # --- TABOVI: PREGLED POSLOVA / NOVI POSAO ---
    tab_pregled, tab_novi = st.tabs(["📋 Svi Poslovi i Statusi", "➕ Otvori Novi Posao / Objekat"])

    with tab_pregled:
        if df.empty:
            st.info("Trenutno nema unetih poslova. Otvorite novi posao u susednom tabu.")
        else:
            # Filter po statusu
            izabrani_filter = st.selectbox("Filtriraj objekte po statusu:", ["Svi statusi"] + STATUSI)
            filtrirani_df = df if izabrani_filter == "Svi statusi" else df[df["status"] == izabrani_filter]

            for _, row in filtrirani_df.iterrows():
                with st.expander(f"{row['status']} | **{row['klijent']}** — {row['objekat']}", expanded=(row['status'] == "🟠 U radu na terenu")):
                    c1, c2, c3 = st.columns([2, 1.5, 1.5])

                    with c1:
                        st.markdown(f"**📞 Telefon:** [{row['telefon']}](tel:{row['telefon']})")
                        st.markdown(f"**📍 Objekat / Adresa:** {row['objekat']}")
                        st.markdown(f"**👷 Odgovorni na terenu:** {row['odgovorni_majstor']}")
                        st.markdown(f"**⏳ Rok završetka:** {row['rok_zavrsetka']}")
                        if row.get("napomena"):
                            st.info(f"📝 **Napomena:** {row['napomena']}")

                    with c2:
                        st.markdown("##### 💵 Finansijski pregled")
                        st.write(f"Cena za klijenta: **{row['cena_ponude_eur']:,.2f} €**")
                        st.write(f"Nabavka materijala: **-{row['trosak_nabavke_mat_eur']:,.2f} €**")
                        st.write(f"Isplata pomoćnika: **-{row['trosak_pomocnika_eur']:,.2f} €**")
                        profit = row['cena_ponude_eur'] - (row['trosak_nabavke_mat_eur'] + row['trosak_pomocnika_eur'])
                        st.success(f"**Čist profit:** {profit:,.2f} €")

                    with c3:
                        st.markdown("##### ⚙️ Brze akcije")
                        novi_status = st.selectbox(
                            "Promeni status:",
                            STATUSI,
                            index=STATUSI.index(row['status']) if row['status'] in STATUSI else 0,
                            key=f"status_sel_{row['id']}"
                        )
                        if st.button("Sačuvaj izmenu statusa", key=f"btn_save_{row['id']}"):
                            for p in poslovi:
                                if p["id"] == row["id"]:
                                    p["status"] = novi_status
                            save_poslovi(poslovi)
                            st.toast("Status ažuriran!", icon="✅")
                            st.rerun()

                        # WhatsApp link za brzu poruku klijentu
                        tel_cist = str(row['telefon']).replace("+", "").replace(" ", "").replace("/", "").replace("-", "")
                        wa_tekst = f"Pozdrav {row['klijent']}, javljam se u vezi radova na grejanju za objekat {row['objekat']}."
                        wa_url = f"https://wa.me/{tel_cist}?text={wa_tekst}"
                        st.link_button("💬 Pošalji WhatsApp", wa_url)

    with tab_novi:
        st.markdown("#### Unos novog klijenta i radnog naloga")
        with st.form("novi_posao_forma"):
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                klijent_novo = st.text_input("Ime i prezime klijenta *")
                telefon_novo = st.text_input("Broj telefona (npr. +38164...) *")
                objekat_novo = st.text_input("Adresa / Tip objekta (npr. Kuća 180m2, Mirijevo) *")
                odgovorni_novo = st.text_input("Dodeljena ekipa / Majstor", value="Ekipa 1")
                rok_novo = st.date_input("Planirani rok završetka", datetime.date.today() + datetime.timedelta(days=10))

            with col_u2:
                status_novo = st.selectbox("Početni status", STATUSI, index=0)
                ponuda_eur_novo = st.number_input("Ukupna cena za klijenta (€)", min_value=0.0, value=2500.0, step=100.0)
                nabavka_mat_novo = st.number_input("Procenjen trošak nabavke materijala (€)", min_value=0.0, value=1500.0, step=100.0)
                pomocnici_novo = st.number_input("Trošak pomoćne radne snage (€)", min_value=0.0, value=250.0, step=50.0)
                napomena_novo = st.text_area("Napomene sa terena", "Standardan razvod, cevi u podu.")

            submit_novi = st.form_submit_button("💾 Sačuvaj i evidentiraj posao", type="primary", use_container_width=True)

            if submit_novi:
                if not klijent_novo.strip() or not objekat_novo.strip():
                    st.error("Ime klijenta i lokacija objekta su obavezna polja.")
                else:
                    novi_id = max([p["id"] for p in poslovi], default=0) + 1
                    poslovi.append({
                        "id": novi_id,
                        "klijent": klijent_novo.strip(),
                        "telefon": telefon_novo.strip(),
                        "objekat": objekat_novo.strip(),
                        "status": status_novo,
                        "rok_zavrsetka": str(rok_novo),
                        "odgovorni_majstor": odgovorni_novo.strip(),
                        "cena_ponude_eur": float(ponuda_eur_novo),
                        "trosak_nabavke_mat_eur": float(nabavka_mat_novo),
                        "trosak_pomocnika_eur": float(pomocnici_novo),
                        "napomena": napomena_novo.strip()
                    })
                    save_poslovi(poslovi)
                    st.success(f"Posao za '{klijent_novo}' je uspešno upisan u evidenciju!")
                    st.rerun()