"""
Agent 5 - Générateur de page web
Convertit le briefing Markdown en une page HTML statique, à héberger
gratuitement via GitHub Pages. Génère :
  - docs/index.html          -> toujours le briefing du jour
  - docs/archive/YYYY-MM-DD.html -> historique, jamais écrasé
  - docs/archive.json        -> manifeste des dates archivées (utilisé pour le menu)
"""
import os
import json
from datetime import date
import markdown as md

DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
ARCHIVE_DIR = os.path.join(DOCS_DIR, "archive")
ARCHIVE_MANIFEST = os.path.join(DOCS_DIR, "archive.json")
MAX_SIDEBAR_ITEMS = 14  # nombre de jours affichés dans le menu latéral

STYLE = """
:root{color-scheme:light dark;--bg:#0f1115;--card:#171a21;--text:#e8e8e6;--muted:#9a9a94;--accent:#5dcaa5;--border:#2a2d35}
@media (prefers-color-scheme: light){:root{--bg:#f7f6f2;--card:#ffffff;--text:#20201d;--muted:#6b6a64;--accent:#0f6e56;--border:#e2e0d8}}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--text);line-height:1.6}
.wrap{max-width:920px;margin:0 auto;padding:24px 16px;display:flex;gap:28px;align-items:flex-start}
main{flex:1;min-width:0}
aside{width:190px;flex-shrink:0;position:sticky;top:24px}
h1{font-size:22px;margin:0 0 4px}
.subtitle{color:var(--muted);font-size:13px;margin-bottom:20px}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px 24px;margin-bottom:16px}
.card h2{font-size:17px;margin-top:0}
.card a{color:var(--accent)}
aside h3{font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin-bottom:10px}
aside ul{list-style:none;padding:0;margin:0}
aside li{margin-bottom:8px}
aside a{color:var(--text);text-decoration:none;font-size:13px;display:block;padding:4px 0}
aside a:hover{color:var(--accent)}
aside a.active{color:var(--accent);font-weight:600}
@media (max-width:640px){.wrap{flex-direction:column}aside{position:static;width:100%}}
"""


def _load_manifest():
    if os.path.exists(ARCHIVE_MANIFEST):
        with open(ARCHIVE_MANIFEST, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_manifest(manifest):
    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(ARCHIVE_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def _sidebar_html(manifest, current_date=None, base_prefix=""):
    items = ""
    for entry in manifest[:MAX_SIDEBAR_ITEMS]:
        is_active = entry["date"] == current_date
        cls = ' class="active"' if is_active else ""
        items += f'<li><a href="{base_prefix}{entry["file"]}"{cls}>{entry["date"]}</a></li>\n'
    return f'<aside><h3>Historique</h3><ul>{items}</ul></aside>'


def _page_html(title, date_str, body_html, manifest, current_date, base_prefix, is_archive=False):
    home_link = '<a href="../index.html">← Retour à aujourd\'hui</a>' if is_archive else ""
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{STYLE}</style>
</head>
<body>
<div class="wrap">
<main>
<h1>📰 Veille IA &amp; Cybersécurité</h1>
<div class="subtitle">{date_str} {(' — ' + home_link) if home_link else ''}</div>
<div class="card">{body_html}</div>
</main>
{_sidebar_html(manifest, current_date, base_prefix)}
</div>
</body>
</html>"""


def generate_page(briefing_markdown):
    today = date.today().isoformat()
    today_display = date.today().strftime("%d/%m/%Y")
    body_html = md.markdown(briefing_markdown, extensions=["extra", "nl2br"])

    os.makedirs(ARCHIVE_DIR, exist_ok=True)

    manifest = _load_manifest()
    # évite les doublons si le pipeline tourne 2x le même jour
    manifest = [e for e in manifest if e["date"] != today]
    manifest.insert(0, {"date": today, "file": f"{today}.html"})
    manifest = manifest[:60]  # on garde 60 jours d'historique max
    _save_manifest(manifest)

    # Page archive (jamais écrasée après coup, servira de lien permanent)
    archive_html = _page_html(
        f"Veille du {today_display}", today_display, body_html,
        manifest, today, base_prefix="", is_archive=True,
    )
    with open(os.path.join(ARCHIVE_DIR, f"{today}.html"), "w", encoding="utf-8") as f:
        f.write(archive_html)

    # Page d'accueil (toujours le briefing du jour)
    index_html = _page_html(
        f"Veille IA & Cybersécurité — {today_display}", today_display, body_html,
        manifest, today, base_prefix="archive/", is_archive=False,
    )
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"[webpage] Page générée pour {today}, historique de {len(manifest)} jour(s).")


if __name__ == "__main__":
    generate_page("## À retenir\nTest de génération de page.\n\n## IA\n- Item de test")