import streamlit as st
import os
import re
import pandas as pd
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, unquote

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
    border-radius: 14px 14px 0 0;
    padding: 18px 20px 12px 20px;
    text-align: center;
}
.metric-card.metric-card-active {
    background: #eff6ff;
    border-color: #93c5fd;
}
.metric-label { font-size: 0.68rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; }
.metric-value { font-family: 'DM Serif Display', serif; font-size: 2.1rem; font-weight: 400; }

/* ── Pulsantino "Filtra" sotto ogni quadratone ─────────────────────────── */
[class*="st-key-mcard_"] button {
    height: 30px !important;
    min-height: 30px !important;
    font-size: 0.66rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    border-radius: 0 0 14px 14px !important;
    border: 1px solid #e2e8f0 !important;
    border-top: none !important;
    margin-top: -2px !important;
    color: #475569 !important;
    background: #f1f5f9 !important;
    transition: background .12s, color .12s !important;
}
[class*="st-key-mcard_"] button:hover {
    background: #2563eb !important;
    color: #ffffff !important;
    border-color: #2563eb !important;
}

/* ── Bottoni azione anteprima: stessa altezza per tutti e 4 ──────────────── */
[class*="st-key-dl_preview"] button,
[class*="st-key-art_fs"] button,
[class*="st-key-btn_apri"] button,
[data-testid="stPopover"] button {
    height: 54px !important;
    min-height: 54px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    line-height: 1.15 !important;
    font-size: 0.84rem !important;
    font-weight: 600 !important;
    padding: 4px 8px !important;
    white-space: normal !important;
    border-radius: 10px !important;
}

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

# Pulsante fullscreen (Fullscreen API) iniettato dentro l'articolo.
FS_BUTTON = """
<div style="position:fixed;top:12px;right:18px;z-index:99999;">
  <button onclick="(function(){var e=document.documentElement;if(!document.fullscreenElement){if(e.requestFullscreen){e.requestFullscreen().catch(function(){alert('Schermo intero del browser non disponibile in questo riquadro: premi F11 per la modalita a tutto schermo.');});}else{alert('Premi F11 per la modalita a tutto schermo.');}}else{document.exitFullscreen();}})()"
    style="font-family:system-ui,sans-serif;font-size:0.78rem;font-weight:700;padding:8px 14px;border:none;border-radius:10px;background:#0f172a;color:#fff;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.25);">
    ⛶ Schermo intero
  </button>
</div>
"""

# CSS di lettura iniettato nell'articolo (uguale a quello dell'anteprima).
READING_CSS = """
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


def _article_id(full_path: str) -> str:
    rel = os.path.relpath(full_path, ARTICOLI_DIR)
    return rel.replace(os.sep, "/")


def _base_url() -> str:
    try:
        h = st.context.headers
        host = h.get("Host") or h.get("host")
        proto = h.get("X-Forwarded-Proto") or h.get("x-forwarded-proto")
        if host:
            if not proto:
                proto = "http" if host.split(":")[0] in ("localhost", "127.0.0.1") else "https"
            return f"{proto}://{host}"
    except Exception:
        pass
    return ""


def inject_reading(html: str) -> str:
    if "</head>" in html:
        return html.replace("</head>", READING_CSS + "</head>", 1)
    return READING_CSS + html


def inject_fs_button(html: str) -> str:
    if "</body>" in html:
        return html.replace("</body>", FS_BUTTON + "</body>", 1)
    return html + FS_BUTTON


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
                # Anno a due cifre: %y invece di %Y
                data_str = data_obj.strftime("%d %b %y")
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
        html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
        return text.lower()
    except:
        return ""


def render_fullscreen_article(path, titolo, categoria, data_str):
    """Modalità schermo intero: nasconde sidebar/header, articolo a tutta
    larghezza + pulsante esci e pulsante fullscreen reale dentro l'articolo."""
    st.markdown("""
    <style>
    [data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"],
    header { display: none !important; }
    .block-container { padding: 0.6rem 1.2rem 0 1.2rem !important; max-width: 100% !important; }
    </style>
    """, unsafe_allow_html=True)

    top1, top2 = st.columns([6, 1])
    with top1:
        st.markdown(
            f'<div class="preview-title" style="font-size:1.15rem;">{titolo}</div>'
            f'<div class="preview-meta">{data_str} · <span class="cat-badge">{categoria}</span></div>',
            unsafe_allow_html=True
        )
    with top2:
        if st.button("✕ Esci", key="fs_exit", use_container_width=True):
            st.session_state.fs_mode = False
            st.rerun()

    try:
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        html = inject_reading(html)
        html = inject_fs_button(html)
        st.components.v1.html(html, height=1500, scrolling=True)
    except Exception as e:
        st.error(f"Errore caricamento: {e}")


# ─── CARICAMENTO DATI ─────────────────────────────────────────────────────────
if "df_articoli" not in st.session_state:
    with st.spinner("🔎 Scansionando tutti gli articoli e sottocartelle..."):
        st.session_state.df_articoli = scan_articoli(ARTICOLI_DIR)

df = st.session_state.df_articoli

if df.empty:
    st.stop()

categorie = sorted(df["Categoria"].unique())

# ─── QUERY PARAMS ────────────────────────────────────────────────────────────
# ?cat=<categoria>  → filtra per categoria (dai quadratoni o da link esterni)
if "cat" in st.query_params:
    c = st.query_params["cat"]
    if c in categorie:
        st.session_state["selected_cats_ms"] = [c]
    del st.query_params["cat"]
    st.rerun()

# Categoria scelta da una card (impostata PRIMA che il multiselect venga creato,
# altrimenti Streamlit vieta di modificare la chiave del widget).
if "_pending_cat" in st.session_state:
    pc = st.session_state.pop("_pending_cat")
    cur = list(st.session_state.get("selected_cats_ms", list(categorie)))
    if cur == [pc]:
        st.session_state["selected_cats_ms"] = list(categorie)  # già attiva → mostra tutte
    else:
        st.session_state["selected_cats_ms"] = [pc]

# ?article=<categoria>/<file>.html  → apre quell'articolo in anteprima (deep link)
if "article" in st.query_params and not st.session_state.get("_art_qp_done"):
    aid = unquote(st.query_params["article"]).replace("/", os.sep)
    full = os.path.normpath(os.path.join(ARTICOLI_DIR, aid))
    if os.path.isfile(full):
        st.session_state.selected_article_path = full
    st.session_state["_art_qp_done"] = True

# ─── MODALITÀ SCHERMO INTERO ─────────────────────────────────────────────────
if st.session_state.get("fs_mode") and st.session_state.get("fs_path"):
    render_fullscreen_article(
        st.session_state["fs_path"],
        st.session_state.get("fs_title", ""),
        st.session_state.get("fs_cat", ""),
        st.session_state.get("fs_date", ""),
    )
    st.stop()

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔎 Filtri")

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

    # Pulsante "Deseleziona tutti" affiancato al label Argomenti
    lbl_col, btn_col = st.columns([3, 1])
    lbl_col.markdown("**Argomenti**")
    if btn_col.button("✕", key="clear_cats", use_container_width=True, help="Deseleziona tutti gli argomenti"):
        st.session_state["selected_cats_ms"] = []
        st.rerun()

    ms_kwargs = {}
    if "selected_cats_ms" not in st.session_state:
        ms_kwargs["default"] = categorie

    selected_cats = st.multiselect(
        label="",
        options=categorie,
        key="selected_cats_ms",
        label_visibility="collapsed",
        **ms_kwargs
    )

    st.divider()
    st.caption(f"📊 **{len(df)} articoli totali** trovati")

# ─── FILTRO TESTO/TITOLO (senza categoria) ───────────────────────────────────
search_filtered = df.copy()
if search:
    if search_mode == "Titolo":
        search_filtered = search_filtered[search_filtered["Titolo"].str.contains(search, case=False, na=False)]
    else:
        with st.spinner("Ricerca nel testo degli articoli..."):
            mask = search_filtered["Percorso"].apply(
                lambda p: search.lower() in _extract_text(p)
            )
        search_filtered = search_filtered[mask]

# ─── FILTRO CATEGORIA ────────────────────────────────────────────────────────
filtered = search_filtered.copy()
if selected_cats:
    filtered = filtered[filtered["Categoria"].isin(selected_cats)]

# ─── METRIC CARDS (QUADRATONI CLICCABILI → FILTRO) ───────────────────────────
if not search_filtered.empty:
    counts = search_filtered["Categoria"].value_counts().head(6)
    cols = st.columns(min(len(counts), 6))
    for i, (cat, count) in enumerate(counts.items()):
        active = (list(selected_cats) == [cat])
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card {'metric-card-active' if active else ''}">
                <div class="metric-label">{cat}</div>
                <div class="metric-value">{count}</div>
            </div>
            """, unsafe_allow_html=True)
            # Click → filtra per questa categoria. Se già attiva da sola → mostra tutte.
            if st.button(
                "✓ Attivo" if active else "Filtra",
                key=f"mcard_{i}",
                use_container_width=True,
                help=f"Mostra solo gli articoli di {cat}" if not active else "Mostra tutte le categorie"
            ):
                # Non si può scrivere direttamente su 'selected_cats_ms' qui (widget
                # già creato): si usa una chiave-ponte applicata in cima allo script.
                st.session_state["_pending_cat"] = cat
                st.rerun()

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

    # La selezione nella tabella aggiorna l'articolo corrente
    if len(selected_row["selection"]["rows"]) > 0:
        idx = selected_row["selection"]["rows"][0]
        st.session_state.selected_article_path = filtered.iloc[idx]["Percorso"]

# ─── DETERMINA ARTICOLO IN ANTEPRIMA ─────────────────────────────────────────
sel_path = st.session_state.get("selected_article_path")
sel_row = None
if sel_path:
    m = df[df["Percorso"] == sel_path]
    if not m.empty:
        sel_row = m.iloc[0]

# ─── PREVIEW ─────────────────────────────────────────────────────────────────
with col_viewer:
    if sel_row is not None:
        try:
            with open(sel_row["Percorso"], "r", encoding="utf-8") as f:
                html_content = f.read()

            # ── Header: titolo + meta ────────────────────────────────────
            st.markdown(
                f'<div class="preview-title">📄 {sel_row["Titolo"]}</div>'
                f'<div class="preview-meta">{sel_row["Data_str"]} · '
                f'<span class="cat-badge">{sel_row["Categoria"]}</span></div>',
                unsafe_allow_html=True
            )

            # ── Pulsanti: Scarica · Schermo intero · Condividi · Apri ────
            b1, b2, b3, b4 = st.columns(4)

            with b1:
                st.download_button(
                    "⬇️ Scarica",
                    data=html_content.encode("utf-8"),
                    file_name=sel_row["File"],
                    mime="text/html",
                    use_container_width=True,
                    key="dl_preview"
                )

            with b2:
                if st.button("⛶ Schermo intero", use_container_width=True, key="art_fs"):
                    st.session_state.fs_mode = True
                    st.session_state.fs_path = sel_row["Percorso"]
                    st.session_state.fs_title = sel_row["Titolo"]
                    st.session_state.fs_cat = sel_row["Categoria"]
                    st.session_state.fs_date = sel_row["Data_str"]
                    st.rerun()

            with b3:
                with st.popover("🔗 Condividi", use_container_width=True):
                    aid = _article_id(sel_row["Percorso"])
                    base = _base_url()
                    share_url = f"{base}/?article={quote(aid)}" if base else f"?article={quote(aid)}"
                    st.caption("Link diretto all'articolo (si apre nell'Archivio):")
                    st.code(share_url, language=None)
                    if not base:
                        st.caption("Anteponi l'indirizzo del sito (es. `http://localhost:8501`).")

            with b4:
                if st.button("📂 Apri in Archivio", use_container_width=True, key="btn_apri"):
                    st.session_state["open_article_path"] = sel_row["Percorso"]
                    st.switch_page("app.py")

            html_content_styled = inject_reading(html_content)
            st.components.v1.html(html_content_styled, height=860, scrolling=True)

        except Exception as e:
            st.error(f"Errore caricamento: {e}")
    else:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.info("👈 Seleziona una riga dalla tabella per leggere l'articolo")

st.divider()