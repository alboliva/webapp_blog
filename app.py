import streamlit as st
import os, re
from datetime import datetime, date
import calendar

# Configurazione pagina (deve essere la prima cosa)
st.set_page_config(
    page_title="Reporter",  
    page_icon="📚",                       # ← Qui metti l'icona
    layout="wide",                        # o "centered"
    initial_sidebar_state="expanded"
)


# ─────────────────────────────────────────────────────────────────────────────
# COSTANTI
# ─────────────────────────────────────────────────────────────────────────────
ARTICOLI_DIR = os.path.join(os.getcwd(), "articoli")
IFRAME_HEIGHT = 920

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
NAV_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Fraunces:ital,opsz,wght@0,9..144,300;1,9..144,300&display=swap');

/* ── Compressione verticale generale ── */
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 0.5rem !important;
}
div[data-testid="stVerticalBlock"] > div {
    gap: 0.3rem !important;
}
hr {
    margin: 0.4rem 0 !important;
}
.stButton > button {
    padding-top: 0.25rem !important;
    padding-bottom: 0.25rem !important;
    height: 36px !important;
}

/* ── Navigator bar ── */
.bnav {
    display: flex; align-items: center; gap: 0;
    background: #F5CC27;
    border-radius: 12px; overflow: hidden; height: 44px;
    font-family: 'IBM Plex Mono', monospace;
    box-shadow: 0 4px 24px rgba(0,0,0,0.18);
    margin-top: 2px !important;
    margin-bottom: 4px !important;
}
.bnav-btn {
    width: 36px; height: 44px; border: none;
    background: transparent;
    color: #94a3b8; font-size: 13px; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: background .15s, color .15s;
    flex-shrink: 0;
}
.bnav-btn:hover { background: #1e293b; color: #f1f5f9; }
.bnav-btn:disabled { color: #334155; cursor: default; }
.bnav-sep { width: 1px; height: 22px; background: #1e293b; flex-shrink: 0; }
.bnav-date {
    padding: 0 14px;
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.06em;
    color: #000000; white-space: nowrap; flex-shrink: 0;
}
.bnav-cat {
    padding: 0 10px;
    font-size: 0.65rem; font-weight: 600; letter-spacing: 0.12em;
    color: #475569; white-space: nowrap; text-transform: uppercase; flex-shrink: 0;
}
.bnav-title {
    flex: 1; padding: 0 8px;
    font-size: 0.75rem; color: #000000;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    font-family: 'Fraunces', serif; font-style: italic; font-weight: 300;
    letter-spacing: 0.01em;
}
.bnav-counter {
    padding: 0 14px;
    font-size: 0.65rem; color: #475569;
    white-space: nowrap; flex-shrink: 0;
}
</style>
"""

# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────
def _fmt_size(path: str) -> str:
    try:
        b = os.path.getsize(path)
        return f"{b/1_048_576:.1f} MB" if b >= 1_048_576 else f"{b/1024:.0f} KB"
    except:
        return ""

def _parse_date(fname: str) -> date | None:
    m = re.match(r"(\d{4})(\d{2})(\d{2})", fname)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except:
            pass
    return None

def _human_title(fname: str) -> str:
    base = re.sub(r"\.html$", "", fname, flags=re.I)
    base = re.sub(r"^\d{8}_?", "", base)
    base = re.sub(r"[_\-]+", " ", base).strip()
    return base.title() if base else fname

def scan_articoli(root: str) -> dict:
    """
    Scansiona la cartella articoli/ con sottocartelle (politica/, scienza/, ecc.)
    """
    result: dict[str, list] = {}
    if not os.path.isdir(root):
        return result

    subdirs = sorted([
        d for d in os.listdir(root)
        if os.path.isdir(os.path.join(root, d)) and not d.startswith('.')
    ])

    for subdir in subdirs:
        cat_label = subdir.upper()
        subdir_path = os.path.join(root, subdir)

        files = sorted(
            [f for f in os.listdir(subdir_path) if f.lower().endswith(".html")],
            reverse=True
        )

        docs = []
        for fname in files:
            full_path = os.path.join(subdir_path, fname)
            d = _parse_date(fname)

            pdf_fname = re.sub(r"\.html$", ".pdf", fname, flags=re.I)
            pdf_path = os.path.join(subdir_path, pdf_fname)
            pdf_path = pdf_path if os.path.isfile(pdf_path) else None

            docs.append({
                "fname": fname,
                "full_path": full_path,
                "pdf_path": pdf_path,
                "date": d,
                "date_label": d.strftime("%d %b %Y") if d else "—",
                "title": _human_title(fname),
                "size_html": _fmt_size(full_path),
                "size_pdf": _fmt_size(pdf_path) if pdf_path else None,
                "category": cat_label,
            })

        if docs:
            result[cat_label] = docs

    return result


def inject_viewer_css(html: str) -> str:
    overrides = """
    <style>
    body { max-width:100%!important; padding:25px 35px!important;
           font-size:0.96rem; line-height:1.75; }
    img { max-width:100%!important; height:auto!important; border-radius:8px; }
    h1, h2, h3 { margin-top:1.8em; }
    </style>"""
    tag = "</head>" if "</head>" in html else "<body>"
    return html.replace(tag, overrides + "\n" + tag, 1)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="Notizie",
        layout="wide",
        page_icon="📰",
        initial_sidebar_state="expanded",
    )

    st.markdown(NAV_CSS, unsafe_allow_html=True)

    # ── Scan Articoli ─────────────────────────────────────────────────────
    catalog = scan_articoli(ARTICOLI_DIR)

    if not catalog:
        st.title("📰 Archivio Notizie")
        st.error(f"Cartella **articoli/** non trovata o vuota.\n\nPercorso cercato: `{ARTICOLI_DIR}`")
        st.info("Crea la cartella `articoli/` con sottocartelle come:\n`politica/`, `scienza/`, `economia/`, `esteri/`, ecc.")
        return

    categories = list(catalog.keys())

    # Session State
    ss = st.session_state
    if "nav_cat" not in ss or ss.nav_cat not in catalog:
        ss.nav_cat = categories[0]
    if "nav_idx" not in ss:
        ss.nav_idx = 0

    cat = ss.nav_cat
    docs = catalog[cat]
    idx = min(ss.nav_idx, len(docs) - 1)
    doc = docs[idx]

    # ── Header ─────────────────────────────────────────────────────────────
    st.markdown('<h1 style="margin-bottom:0; margin-top:0;">📰 Archivio Notizie</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748b; margin-top:2px; margin-bottom:6px;">Politica • Scienza • Economia • Esteri • Approfondimenti</p>', unsafe_allow_html=True)

    # ── Category Tabs ─────────────────────────────────────────────────────
    cols = st.columns(len(categories) + 1)
    for i, c in enumerate(categories):
        is_active = (c == cat)
        if cols[i].button(
            f"{'●' if is_active else '○'} {c}",
            key=f"cat_{c}",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            ss.nav_cat = c
            ss.nav_idx = 0
            st.rerun()

    st.divider()

    # ── Navigator Bar compatto ─────────────────────────────────────────────
    st.markdown(f"""
    <div class="bnav" style="margin-bottom:10px;">
        <div class="bnav-date">{doc['date_label']}</div>
        <div class="bnav-sep"></div>
        <div class="bnav-cat">{cat}</div>
        <div class="bnav-sep"></div>
        <div class="bnav-title">{doc['title']}</div>
        <div class="bnav-sep"></div>
        <div class="bnav-counter">{idx+1} / {len(docs)}</div>
    </div>
    """, unsafe_allow_html=True)

    # Pulsanti di navigazione compatti
    nc1, nc2, nc3, nc4 = st.columns(4)
    with nc1:
        if st.button("‹ Precedente", use_container_width=True, disabled=(idx >= len(docs)-1), key="btn_prev"):
            ss.nav_idx = idx + 1
            st.rerun()
    with nc2:
        if st.button("↑ Più recente", use_container_width=True, disabled=(idx == 0), key="btn_top"):
            ss.nav_idx = 0
            st.rerun()
    with nc3:
        if st.button("↓ Più vecchio", use_container_width=True, disabled=(idx == len(docs)-1), key="btn_bot"):
            ss.nav_idx = len(docs) - 1
            st.rerun()
    with nc4:
        if st.button("Successivo ›", use_container_width=True, disabled=(idx <= 0), key="btn_next"):
            ss.nav_idx = idx - 1
            st.rerun()

    st.divider()

    # ── Download Buttons ──────────────────────────────────────────────────
    col_dl1, col_dl2 = st.columns(2)
    try:
        with open(doc["full_path"], "rb") as f:
            html_bytes = f.read()
        col_dl1.download_button(
            label=f"⬇️ Scarica HTML ({doc['size_html']})",
            data=html_bytes,
            file_name=doc["fname"],
            mime="text/html",
            use_container_width=True
        )
    except:
        pass

    if doc["pdf_path"]:
        try:
            with open(doc["pdf_path"], "rb") as f:
                pdf_bytes = f.read()
            col_dl2.download_button(
                label=f"⬇️ Scarica PDF ({doc['size_pdf']})",
                data=pdf_bytes,
                file_name=re.sub(r"\.html$", ".pdf", doc["fname"], flags=re.I),
                mime="application/pdf",
                use_container_width=True
            )
        except:
            pass

    # ── Visualizza Articolo ───────────────────────────────────────────────
    try:
        with open(doc["full_path"], "r", encoding="utf-8") as f:
            html_content = f.read()

        html_content = inject_viewer_css(html_content)
        st.components.v1.html(html_content, height=IFRAME_HEIGHT, scrolling=True)

    except Exception as e:
        st.error(f"Errore durante il caricamento: {e}")


if __name__ == "__main__":
    main()