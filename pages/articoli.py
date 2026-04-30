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

/* ── Tabella abbellita ─────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 6px rgba(15,23,42,0.06);
}
/* header row */
[data-testid="stDataFrame"] thead tr th {
    background: #f1f5f9 !important;
    color: #475569 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    border-bottom: 2px solid #cbd5e1 !important;
    padding: 10px 14px !important;
}
/* data rows */
[data-testid="stDataFrame"] tbody tr td {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
    color: #1e293b !important;
    padding: 10px 14px !important;
    border-bottom: 1px solid #f1f5f9 !important;
    vertical-align: middle !important;
}
/* alternating rows */
[data-testid="stDataFrame"] tbody tr:nth-child(even) td {
    background: #f8fafc !important;
}
[data-testid="stDataFrame"] tbody tr:hover td {
    background: #e0f2fe !important;
    transition: background 0.15s ease;
}

/* ── Badge categoria ───────────────────────────────────────────────────── */
.cat-badge {
    display: inline-block;
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    padding: 3px 9px;
    border-radius: 20px;
    background: #e0f2fe;
    color: #0369a1;
}

/* ── Preview header ────────────────────────────────────────────────────── */
.preview-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 4px;
}
.preview-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.35rem;
    color: #0f172a;
    line-height: 1.3;
    flex: 1;
}
.preview-meta {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.78rem;
    color: #94a3b8;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📰 Archivio Articoli</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Politica · Scienza · Economia · Esteri · Cultura · Approfondimenti</div>', unsafe_allow_html=True)

ARTICOLI_DIR = os.path.join(os.getcwd(), "articoli")

# ─── SCANSIONE ───────────────────────────────────────────────────────────────
def scan_articoli(root_dir):
    articles = []
    root_path = Path(root_dir)

    if not root_path.exists():
        st.error(f"❌ Cartella `articoli/` non trovata in: {root_dir}")
        st.info("Crea la cartella `articoli/` con dentro le sottocartelle (politica/, scienza/, ecc.)")
        return pd.DataFrame()

    for html_file in root_path.rglob("*.html"):
        parts = html_file.relative_to(root_dir).parts
        categoria = parts[0].upper() if len(parts) > 1 else "GENERALE"

        date_match = re.match(r"^(\d{4})(\d{2})(\d{2})", html_file.name)
        data_obj = None
        data_str = "—"
        if date_match:
            try:
                data_obj = datetime(int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3)))
                data_str = data_obj.strftime("%d %b %Y")
            except:
                pass

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


@st.cache_data(show_spinner=False)
def _extract_text(percorso: str) -> str:
    """Estrae testo plain dall'HTML per la ricerca nel contenuto (cached)."""
    try:
        with open(percorso, "r", encoding="utf-8") as f:
            html = f.read()
        # Rimuove script e style
        html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
        # Rimuove tag HTML
        text = re.sub(r"<[^>]+>", " ", html)
        # Comprime spazi
        text = re.sub(r"\s+", " ", text).strip()
        return text.lower()
    except:
        return ""


if "df_articoli" not in st.session_state:
    with st.spinner("🔎 Scansionando tutti gli articoli e sottocartelle..."):
        st.session_state.df_articoli = scan_articoli(ARTICOLI_DIR)

df = st.session_state.df_articoli

if df.empty:
    st.stop()

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔎 Filtri")

    # Radio: dove cercare
    search_mode = st.radio(
        "Cerca in:",
        options=["Titolo", "Testo articolo"],
        index=0,
        horizontal=True,
        key="search_mode"
    )

    if search_mode == "Testo articolo":
        st.caption("⚠️ La ricerca nel testo può essere più lenta con molti articoli.")

    label = "Cerca nel titolo" if search_mode == "Titolo" else "Cerca nel testo"
    search = st.text_input(label, placeholder="es. riforma, clima, elezioni...", key="search_query")

    categorie = sorted(df["Categoria"].unique())
    selected_cats = st.multiselect("Argomenti", options=categorie, default=categorie)

    st.divider()
    st.caption(f"📊 **{len(df)} articoli totali** trovati")

# ─── FILTRI ──────────────────────────────────────────────────────────────────
filtered = df.copy()

if search:
    if search_mode == "Titolo":
        filtered = filtered[filtered["Titolo"].str.contains(search, case=False, na=False)]
    else:
        with st.spinner("Ricerca nel testo degli articoli..."):
            mask = filtered["Percorso"].apply(
                lambda p: search.lower() in _extract_text(p)
            )
        filtered = filtered[mask]

if selected_cats:
    filtered = filtered[filtered["Categoria"].isin(selected_cats)]

# ─── METRIC CARDS ─────────────────────────────────────────────────────────────
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

st.markdown("<br>", unsafe_allow_html=True)

# ─── LAYOUT PRINCIPALE ───────────────────────────────────────────────────────
col_table, col_viewer = st.columns([2, 3])

with col_table:
    st.subheader(f"📋 Articoli trovati: **{len(filtered)}**")

    display_df = filtered[["Data_str", "Titolo"]].copy()
    display_df = display_df.rename(columns={"Data_str": "Data"})

    selected_row = st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=600,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Data": st.column_config.TextColumn("📅 Data", width="small"),
            "Titolo": st.column_config.TextColumn("📄 Titolo", width="large"),
        }
    )

    if len(selected_row["selection"]["rows"]) > 0:
        idx = selected_row["selection"]["rows"][0]
        sel = filtered.iloc[idx]
        try:
            with open(sel["Percorso"], "r", encoding="utf-8") as f:
                html_dl = f.read()
            st.download_button(
                "⬇️ Scarica articolo selezionato",
                data=html_dl.encode("utf-8"),
                file_name=sel["File"],
                mime="text/html",
                use_container_width=True,
                key="dl_table"
            )
        except:
            pass

# ─── PREVIEW ─────────────────────────────────────────────────────────────────
with col_viewer:
    if len(selected_row["selection"]["rows"]) > 0:
        idx = selected_row["selection"]["rows"][0]
        selected_file = filtered.iloc[idx]

        try:
            with open(selected_file["Percorso"], "r", encoding="utf-8") as f:
                html_content = f.read()

            dl_col, btn_col = st.columns([3, 1])
            with dl_col:
                st.markdown(
                    f'<div class="preview-title">📄 {selected_file["Titolo"]}</div>'
                    f'<div class="preview-meta">{selected_file["Data_str"]} · '
                    f'<span class="cat-badge">{selected_file["Categoria"]}</span></div>',
                    unsafe_allow_html=True
                )
            with btn_col:
                st.markdown("<br>", unsafe_allow_html=True)
                st.download_button(
                    "⬇️ Scarica",
                    data=html_content.encode("utf-8"),
                    file_name=selected_file["File"],
                    mime="text/html",
                    use_container_width=True,
                    key="dl_preview"
                )

            inject = """
            <style>
            body {
                max-width: 100% !important;
                padding: 22px 28px !important;
                font-size: 1.01rem !important;
                line-height: 1.72 !important;
                font-family: 'Georgia', serif;
                color: #1e293b;
                background: #fafaf8;
            }
            h1, h2, h3 { font-family: 'Georgia', serif; color: #0f172a; }
            img { max-width: 100% !important; height: auto !important; border-radius: 8px; }
            a { color: #0369a1; }
            p { margin-bottom: 1em; }
            blockquote {
                border-left: 3px solid #cbd5e1;
                margin-left: 0;
                padding-left: 16px;
                color: #64748b;
                font-style: italic;
            }
            </style>
            """
            html_content_styled = html_content.replace("</head>", inject + "</head>")
            st.components.v1.html(html_content_styled, height=860, scrolling=True)

        except Exception as e:
            st.error(f"Errore caricamento: {e}")
    else:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.info("👈 Seleziona una riga dalla tabella per leggere l'articolo")

st.divider()