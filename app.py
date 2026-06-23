import streamlit as st
import os, re, json
from datetime import datetime, date
import calendar
from urllib.parse import quote, unquote

st.set_page_config(
    page_title="Reporter",
    page_icon="📚",
    layout="wide",
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

/* ── Pill buttons per le categorie ── */
div[data-testid="stHorizontalBlock"] .stButton > button {
    font-size: 0.55rem !important;
    padding: 0 10px !important;
    max-width: 140px !important;
    height: 18px !important;
    min-height: unset !important;
    border-radius: 20px !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    line-height: 1 !important;
}

/* ── Pulsanti azione (Schermo intero, Condividi): riempiono la colonna ── */
/* Selettore più specifico della regola "pillola" qui sopra, così vince lui. */
div[data-testid="stHorizontalBlock"] [class*="st-key-app_fs"] .stButton > button,
div[data-testid="stHorizontalBlock"] [class*="st-key-app_fs"] button,
div[data-testid="stHorizontalBlock"] [class*="st-key-app_share"] .stButton > button,
div[data-testid="stHorizontalBlock"] [class*="st-key-app_share"] button {
    width: 100% !important;
    max-width: 100% !important;
    height: 40px !important;
    min-height: 40px !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    letter-spacing: normal !important;
    text-transform: none !important;
    line-height: 1.2 !important;
    padding: 0 12px !important;
    white-space: nowrap !important;
}

/* ── Pulsantoni navigazione globale ── */
.global-nav-btn button {
    height: 56px !important;
    font-size: 1.4rem !important;
    font-weight: 700 !important;
    border-radius: 14px !important;
    letter-spacing: 0.04em !important;
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

# Pulsante "schermo intero" (Fullscreen API) iniettato dentro l'articolo.
# Prova il fullscreen reale del browser; se il contesto non lo permette,
# avvisa l'utente (la modalità schermo intero di Streamlit è comunque attiva).
FS_BUTTON = """
<div style="position:fixed;top:12px;right:18px;z-index:99999;">
  <button onclick="(function(){var e=document.documentElement;if(!document.fullscreenElement){if(e.requestFullscreen){e.requestFullscreen().catch(function(){alert('Schermo intero del browser non disponibile in questo riquadro: premi F11 per la modalita a tutto schermo.');});}else{alert('Premi F11 per la modalita a tutto schermo.');}}else{document.exitFullscreen();}})()"
    style="font-family:system-ui,sans-serif;font-size:0.78rem;font-weight:700;padding:8px 14px;border:none;border-radius:10px;background:#0f172a;color:#fff;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.25);">
    ⛶ Schermo intero
  </button>
</div>
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

def _article_id(full_path: str) -> str:
    """ID stabile e leggibile dell'articolo: percorso relativo a articoli/."""
    rel = os.path.relpath(full_path, ARTICOLI_DIR)
    return rel.replace(os.sep, "/")

def _base_url() -> str:
    """Prova a ricostruire l'URL base del sito dagli header (se disponibili)."""
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

def inject_fs_button(html: str) -> str:
    if "</body>" in html:
        return html.replace("</body>", FS_BUTTON + "</body>", 1)
    return html + FS_BUTTON

def _copy_component(text: str) -> str:
    """Mini componente che copia 'text' negli appunti appena viene renderizzato
    (con fallback execCommand) e mostra una conferma verde."""
    t = json.dumps(text)
    return f"""
    <div style="font-family:system-ui,sans-serif;font-size:0.82rem;font-weight:600;color:#16a34a;padding:2px 0;">
      <span id="copymsg">Copia in corso…</span>
    </div>
    <script>
    (function(){{
      const t = {t};
      const msg = document.getElementById('copymsg');
      function ok(){{ if(msg) msg.textContent = '✓ Link copiato negli appunti'; }}
      function ko(){{ if(msg) msg.textContent = '⚠ Copia automatica non riuscita: usa l\\'icona 📋 nel box sotto'; if(msg) msg.style.color = '#b45309'; }}
      function fallback(){{
        try {{
          const ta = document.createElement('textarea');
          ta.value = t; ta.style.position = 'fixed'; ta.style.opacity = '0';
          document.body.appendChild(ta); ta.focus(); ta.select();
          const done = document.execCommand('copy');
          document.body.removeChild(ta);
          done ? ok() : ko();
        }} catch(e) {{ ko(); }}
      }}
      try {{
        if (navigator.clipboard && navigator.clipboard.writeText) {{
          navigator.clipboard.writeText(t).then(ok).catch(fallback);
        }} else {{ fallback(); }}
      }} catch(e) {{ fallback(); }}
    }})();
    </script>
    """

@st.cache_data(show_spinner=False)
def _extract_text(html_path: str) -> str:
    """Estrae testo plain dall'HTML per la ricerca nel contenuto (cached)."""
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
        html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
        return text.lower()
    except:
        return ""

def scan_articoli(root: str) -> dict:
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
                "date_label": d.strftime("%d %b %y") if d else "—",  # anno a 2 cifre
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


def render_fullscreen(doc: dict):
    """Modalità schermo intero: nasconde sidebar/header e mostra l'articolo
    a tutta larghezza. Pulsante per uscire + pulsante fullscreen reale dentro
    l'articolo."""
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
            f"""<div style="font-family:'Fraunces',serif;font-size:1.05rem;color:#0f172a;">
                <b>{doc['title']}</b>
                <span style="color:#64748b;font-size:0.8rem;"> &nbsp;·&nbsp; {doc['category']} &nbsp;·&nbsp; {doc['date_label']}</span>
            </div>""",
            unsafe_allow_html=True
        )
    with top2:
        if st.button("✕ Esci", key="fs_exit", use_container_width=True):
            st.session_state.fs_mode = False
            st.rerun()

    try:
        with open(doc["full_path"], "r", encoding="utf-8") as f:
            html = f.read()
        html = inject_viewer_css(html)
        html = inject_fs_button(html)
        st.components.v1.html(html, height=1500, scrolling=True)
    except Exception as e:
        st.error(f"Errore durante il caricamento: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────────────────────
def main():
    st.markdown(NAV_CSS, unsafe_allow_html=True)

    # ── Scan Articoli ─────────────────────────────────────────────────────
    catalog = scan_articoli(ARTICOLI_DIR)

    if not catalog:
        st.title("📰 Archivio Notizie")
        st.error(f"Cartella **articoli/** non trovata o vuota.\n\nPercorso cercato: `{ARTICOLI_DIR}`")
        st.info("Crea la cartella `articoli/` con sottocartelle come:\n`politica/`, `scienza/`, `economia/`, `esteri/`, ecc.")
        return

    categories = list(catalog.keys())

    # ── Lista globale ordinata per data (più recente prima) ───────────────
    all_docs_sorted = sorted(
        [doc for docs in catalog.values() for doc in docs],
        key=lambda d: d["date"] or date.min,
        reverse=True
    )

    # Session State
    ss = st.session_state

    # ── Gestione redirect da pagina articoli (pulsante APRI) ──────────────
    if "open_article_path" in ss and ss["open_article_path"]:
        target_path = ss.pop("open_article_path")
        found_idx = next(
            (i for i, d in enumerate(all_docs_sorted) if d["full_path"] == target_path),
            None
        )
        if found_idx is not None:
            ss.global_idx = found_idx
        ss["_deep_done"] = True  # la navigazione esplicita ha la priorità

    # ── Deep link: ?article=<categoria>/<file>.html ───────────────────────
    # Apre direttamente l'articolo condiviso (una sola volta per sessione,
    # così l'utente può poi navigare liberamente).
    if "article" in st.query_params and not ss.get("_deep_done"):
        aid = unquote(st.query_params["article"]).replace("/", os.sep)
        target_full = os.path.normpath(os.path.join(ARTICOLI_DIR, aid))
        found_idx = next(
            (i for i, d in enumerate(all_docs_sorted)
             if os.path.normpath(d["full_path"]) == target_full),
            None
        )
        if found_idx is not None:
            ss.global_idx = found_idx
        ss["_deep_done"] = True

    # global_idx: indice nella lista globale cronologica (0 = più recente)
    if "global_idx" not in ss:
        ss.global_idx = 0  # apre sull'articolo più recente

    # Clamp per sicurezza
    ss.global_idx = max(0, min(ss.global_idx, len(all_docs_sorted) - 1))

    # L'articolo corrente è sempre determinato dall'indice globale
    doc = all_docs_sorted[ss.global_idx]
    cat = doc["category"]

    # ── MODALITÀ SCHERMO INTERO ────────────────────────────────────────────
    if ss.get("fs_mode"):
        render_fullscreen(doc)
        return

    # ── Sidebar: Filtri ────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### 🔍 Filtri")

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
        query = st.text_input(label, key="search_query").strip().lower()

        st.divider()

        all_docs_flat = [doc for docs in catalog.values() for doc in docs]

        if query:
            if search_mode == "Titolo":
                matched = [d for d in all_docs_flat if query in d["title"].lower()]
            else:
                with st.spinner("Ricerca nel testo..."):
                    matched = [d for d in all_docs_flat if query in _extract_text(d["full_path"])]
            st.markdown(f"📋 **{len(matched)} articoli** trovati")
        else:
            matched = None
            st.markdown(f"📊 **{len(all_docs_flat)} articoli totali** trovati")

    # ── Header ─────────────────────────────────────────────────────────────
    st.markdown('<h1 style="margin-bottom:0; margin-top:0;">📰 Archivio Notizie</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748b; margin-top:2px; margin-bottom:6px;">Politica • Scienza • Economia • Esteri • Approfondimenti</p>', unsafe_allow_html=True)

    # ── PULSANTONI NAVIGAZIONE GLOBALE ─────────────────────────────────────
    total = len(all_docs_sorted)
    g = ss.global_idx

    btn_left, btn_info, btn_right = st.columns([1, 3, 1])

    with btn_left:
        st.markdown('<div class="global-nav-btn">', unsafe_allow_html=True)
        if st.button(
            "← Più recente",
            key="gbtn_prev",
            use_container_width=True,
            disabled=(g == 0),
            help="Articolo più recente"
        ):
            ss.global_idx = g - 1
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with btn_info:
        st.markdown(
            f"""<div style="
                text-align:center; padding:10px 0 4px 0;
                font-family:'IBM Plex Mono',monospace;
                font-size:0.7rem; color:#64748b; letter-spacing:0.06em;
            ">
                <span style="font-size:1rem; font-weight:700; color:#0f172a;">{g+1}</span>
                &nbsp;/&nbsp;{total}&nbsp;&nbsp;·&nbsp;&nbsp;
                <span style="
                    background:#F5CC27; color:#000; border-radius:6px;
                    padding:2px 8px; font-weight:700; letter-spacing:0.1em;
                ">{cat}</span>
                &nbsp;&nbsp;·&nbsp;&nbsp;{doc['date_label']}
            </div>""",
            unsafe_allow_html=True
        )

    with btn_right:
        st.markdown('<div class="global-nav-btn">', unsafe_allow_html=True)
        if st.button(
            "Più vecchio →",
            key="gbtn_next",
            use_container_width=True,
            disabled=(g == total - 1),
            help="Articolo più vecchio"
        ):
            ss.global_idx = g + 1
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # ── Category Pills ─────────────────────────────────────────────────────
    cols = st.columns(len(categories))
    for i, c in enumerate(categories):
        is_active = (c == cat)
        if matched is not None:
            n = len([d for d in matched if d["category"] == c])
            pill_label = f"{c} ({n})"
        else:
            pill_label = c
        if cols[i].button(
            pill_label,
            key=f"cat_{c}",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            for gi, gd in enumerate(all_docs_sorted):
                if gd["category"] == c:
                    ss.global_idx = gi
                    break
            st.rerun()

    st.divider()

    # ── Navigator Bar (info dettaglio) ─────────────────────────────────────
    docs_in_cat = catalog[cat]
    idx_in_cat = next((i for i, d in enumerate(docs_in_cat) if d["full_path"] == doc["full_path"]), 0)

    st.markdown(f"""
    <div class="bnav" style="margin-bottom:10px;">
        <div class="bnav-date">{doc['date_label']}</div>
        <div class="bnav-sep"></div>
        <div class="bnav-cat">{cat}</div>
        <div class="bnav-sep"></div>
        <div class="bnav-title">{doc['title']}</div>
        <div class="bnav-sep"></div>
        <div class="bnav-counter">{idx_in_cat+1} / {len(docs_in_cat)} in categoria</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── Azioni: Scarica HTML · (PDF) · Schermo intero · Condividi ──────────
    # Tutti i pulsanti su un'unica riga. La colonna PDF compare solo se esiste.
    has_pdf = bool(doc["pdf_path"])
    action_cols = st.columns(4 if has_pdf else 3)
    ci = 0

    # 1) Scarica HTML
    try:
        with open(doc["full_path"], "rb") as f:
            html_bytes = f.read()
        action_cols[ci].download_button(
            label=f"⬇️ Scarica HTML ({doc['size_html']})",
            data=html_bytes,
            file_name=doc["fname"],
            mime="text/html",
            use_container_width=True
        )
    except:
        pass
    ci += 1

    # 2) Scarica PDF (solo se presente)
    if has_pdf:
        try:
            with open(doc["pdf_path"], "rb") as f:
                pdf_bytes = f.read()
            action_cols[ci].download_button(
                label=f"⬇️ Scarica PDF ({doc['size_pdf']})",
                data=pdf_bytes,
                file_name=re.sub(r"\.html$", ".pdf", doc["fname"], flags=re.I),
                mime="application/pdf",
                use_container_width=True
            )
        except:
            pass
        ci += 1

    # 3) Schermo intero
    if action_cols[ci].button("⛶ Schermo intero", key="app_fs", use_container_width=True):
        ss.fs_mode = True
        st.rerun()
    ci += 1

    # 4) Condividi → copia subito il link negli appunti + avviso (toast)
    if action_cols[ci].button("🔗 Condividi articolo", key="app_share", use_container_width=True):
        aid = _article_id(doc["full_path"])
        base = _base_url()
        ss["share_url"] = f"{base}/?article={quote(aid)}" if base else f"?article={quote(aid)}"
        ss["_do_copy"] = True
        st.toast("📋 Link copiato negli appunti!", icon="✅")

    # Pannello copia (compare subito dopo il click, sparisce all'interazione dopo)
    if ss.get("_do_copy") and ss.get("share_url"):
        st.components.v1.html(_copy_component(ss["share_url"]), height=40)
        st.code(ss["share_url"], language=None)
        ss["_do_copy"] = False

    # ── Visualizza Articolo ────────────────────────────────────────────────
    try:
        with open(doc["full_path"], "r", encoding="utf-8") as f:
            html_content = f.read()

        html_content = inject_viewer_css(html_content)
        st.components.v1.html(html_content, height=IFRAME_HEIGHT, scrolling=True)

    except Exception as e:
        st.error(f"Errore durante il caricamento: {e}")


if __name__ == "__main__":
    main()