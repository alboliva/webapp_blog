import streamlit as st
import os
import re
import pandas as pd
from datetime import datetime
from pathlib import Path

st.set_page_config(
    page_title="Articoli",
    layout="wide",
    page_icon="📰",
    initial_sidebar_state="expanded"
)

# ─── CSS elegante (stile identico al tuo dashboard) ─────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500;600&display=swap');

.main-header {
    font-family: 'DM Serif Display', serif;
    font-size: 2.6rem; 
    color: #0f172a;
    letter-spacing: -0.02em;
    margin-bottom: 0;
}
.sub-header {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.82rem; 
    font-weight: 500; 
    color: #94a3b8;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

.metric-card {
    background: #f8fafc; 
    border: 1px solid #e2e8f0;
    border-radius: 14px; 
    padding: 18px 20px;
    text-align: center;
}
.metric-label { font-size: 0.68rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; }
.metric-value { font-family: 'DM Serif Display', serif; font-size: 2.1rem; font-weight: 400; }

.badge {
    display: inline-block; 
    font-size: 0.55rem; 
    padding: 2px 8px; 
    border-radius: 20px; 
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📰 Archivio Articoli</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Politica · Scienza · Economia · Esteri · Cultura · Approfondimenti</div>', unsafe_allow_html=True)

ARTICOLI_DIR = os.path.join(os.getcwd(), "articoli")

# ─── SCANSIONE INTELLIGENTE ───────────────────────────────────────────────────
def scan_articoli(root_dir):
    articles = []
    root_path = Path(root_dir)
    
    if not root_path.exists():
        st.error(f"❌ Cartella `articoli/` non trovata in: {root_dir}")
        st.info("Crea la cartella `articoli/` con dentro le sottocartelle (politica/, scienza/, ecc.)")
        return pd.DataFrame()
    
    for html_file in root_path.rglob("*.html"):
        # Categoria = nome della prima sottocartella
        parts = html_file.relative_to(root_dir).parts
        categoria = parts[0].upper() if len(parts) > 1 else "GENERALE"
        
        # Estrazione data dal nome file
        date_match = re.match(r"^(\d{4})(\d{2})(\d{2})", html_file.name)
        data_obj = None
        data_str = "—"
        if date_match:
            try:
                data_obj = datetime(int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3)))
                data_str = data_obj.strftime("%d %b %Y")
            except:
                pass
        
        # Titolo leggibile
        titolo = re.sub(r"^\d{8}_?", "", html_file.name)
        titolo = re.sub(r"\.html$", "", titolo, flags=re.I)
        titolo = re.sub(r"[-_]+", " ", titolo).strip().title()
        
        size_kb = round(html_file.stat().st_size / 1024, 1)
        
        articles.append({
            "Data": data_obj,
            "Data_str": data_str,
            "Titolo": titolo,
            "Categoria": categoria,
            "File": html_file.name,
            "Dimensione": f"{size_kb} KB",
            "Percorso": str(html_file)
        })
    
    df = pd.DataFrame(articles)
    if not df.empty:
        df = df.sort_values("Data", ascending=False).reset_index(drop=True)
    return df

# Carica una sola volta
if "df_articoli" not in st.session_state:
    with st.spinner("🔎 Scansionando tutti gli articoli e sottocartelle..."):
        st.session_state.df_articoli = scan_articoli(ARTICOLI_DIR)

df = st.session_state.df_articoli

if df.empty:
    st.stop()

# ─── SIDEBAR FILTRI ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔎 Filtri")
    
    search = st.text_input("Cerca nel titolo o contenuto", placeholder="es. riforma, clima, elezioni...")
    
    categorie = sorted(df["Categoria"].unique())
    selected_cats = st.multiselect("Argomenti", options=categorie, default=categorie)
    
    st.divider()
    st.caption(f"📊 **{len(df)} articoli totali** trovati")

# ─── APPLICA FILTRI ───────────────────────────────────────────────────────────
filtered = df.copy()
if search:
    filtered = filtered[filtered["Titolo"].str.contains(search, case=False, na=False)]
if selected_cats:
    filtered = filtered[filtered["Categoria"].isin(selected_cats)]

# ─── METRIC CARDS (conteggio per argomento) ───────────────────────────────────
if not filtered.empty:
    counts = filtered["Categoria"].value_counts().head(6)
    cols = st.columns(min(len(counts), 6))
    for i, (cat, count) in enumerate(counts.items()):
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{cat}</div>
                <div class="metric-value">{count}</div>
            </div>
            """, unsafe_allow_html=True)

# ─── TABELLA PRINCIPALE ───────────────────────────────────────────────────────
st.subheader(f"📋 Articoli trovati: **{len(filtered)}**")

col_table, col_viewer = st.columns([3, 2])

with col_table:
    # Tabella interattiva (ordinabile, ricercabile)
    display_df = filtered[["Data_str", "Titolo", "Categoria", "Dimensione"]].copy()
    display_df = display_df.rename(columns={"Data_str": "Data"})
    
    selected_row = st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=650,
        on_select="rerun",
        selection_mode="single-row"
    )

# ─── VISUALIZZATORE ARTICOLO (drill-down) ─────────────────────────────────────
with col_viewer:
    if len(selected_row["selection"]["rows"]) > 0:
        idx = selected_row["selection"]["rows"][0]
        selected_file = filtered.iloc[idx]
        
        st.markdown(f"### 📄 {selected_file['Titolo']}")
        st.caption(f"{selected_file['Data_str']} · {selected_file['Categoria']}")
        
        try:
            with open(selected_file["Percorso"], "r", encoding="utf-8") as f:
                html_content = f.read()
            
            # Inietta CSS per adattare l'articolo
            inject = """
            <style>
            body { max-width:100% !important; padding:25px 30px !important; font-size:0.97rem; }
            img { max-width:100% !important; height:auto !important; }
            </style>
            """
            html_content = html_content.replace("</head>", inject + "</head>")
            
            st.components.v1.html(html_content, height=780, scrolling=True)
            
            st.download_button(
                "⬇️ Scarica HTML",
                data=html_content.encode("utf-8"),
                file_name=selected_file["File"],
                mime="text/html",
                use_container_width=True
            )
            
        except Exception as e:
            st.error(f"Errore caricamento: {e}")
    else:
        st.info("👈 Seleziona una riga dalla tabella per leggere l’articolo")

st.divider()
st.caption("💡 Consiglio: i file devono avere nome `YYYYMMDD_titolo-articolo.html` per avere data e titolo automatici")