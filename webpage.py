"""
Agent 5 - Générateur de page web
Convertit le briefing Markdown en une page HTML statique, à héberger
gratuitement via GitHub Pages. Génère :
  - docs/index.html              -> toujours le briefing du jour
  - docs/archive/YYYY-MM-DD.html -> historique, jamais écrasé
  - docs/archive.json            -> manifeste des dates archivées (menu latéral)
  - docs/icon-*.png              -> icône pour l'ajout à l'écran d'accueil (générée une fois, statique)
"""
import os
import json
from datetime import date
import markdown as md

DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
ARCHIVE_DIR = os.path.join(DOCS_DIR, "archive")
ARCHIVE_MANIFEST = os.path.join(DOCS_DIR, "archive.json")
MAX_SIDEBAR_ITEMS = 14  # nombre de jours affichés dans le menu latéral
SITE_TITLE = "Veille IA"  # nom court affiché sous l'icône sur l'écran d'accueil
THEME_COLOR = "#0d6e56"

STYLE = """
:root{color-scheme:light dark;--bg:#0f1115;--card:#171a21;--text:#e8e8e6;--muted:#9a9a94;--accent:#3ddba0;--accent-soft:#173c30;--border:#262a33;--chip:#1c2027}
@media (prefers-color-scheme: light){:root{--bg:#f5f4ef;--card:#ffffff;--text:#1c1c19;--muted:#68675f;--accent:#0d6e56;--accent-soft:#e4f4ee;--border:#e7e4da;--chip:#f0efe8}}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--text);line-height:1.65;-webkit-font-smoothing:antialiased}
header.hero{background:linear-gradient(135deg,#0d6e56,#18a885);color:#fff;padding:36px 16px 28px}
header.hero .hero-inner{max-width:920px;margin:0 auto}
header.hero h1{margin:0 0 6px;font-size:24px;display:flex;align-items:center;gap:10px}
header.hero .subtitle{opacity:.92;font-size:13.5px}
header.hero .subtitle a{color:#fff;text-decoration:underline}
.wrap{max-width:920px;margin:0 auto;padding:24px 16px 60px;display:flex;gap:28px;align-items:flex-start}
main{flex:1;min-width:0}
aside{width:190px;flex-shrink:0;position:sticky;top:24px}
aside h3{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:0 0 10px;font-weight:700}
aside ul{list-style:none;padding:0;margin:0}
aside li{margin-bottom:6px}
aside a{color:var(--text);text-decoration:none;font-size:13px;display:block;padding:6px 10px;border-radius:8px}
aside a:hover{background:var(--chip)}
aside a.active{color:var(--accent);font-weight:700;background:var(--accent-soft)}
.card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:8px 26px 26px;box-shadow:0 1px 2px rgba(0,0,0,.04)}
.card h2{font-size:15px;letter-spacing:.02em;margin:26px 0 14px;padding-top:18px;border-top:1px solid var(--border);display:flex;align-items:center;gap:8px}
.card h2:first-child{margin-top:20px;padding-top:0;border-top:none}
.card p{margin:6px 0 14px;color:var(--text)}
.card p strong{display:block;font-size:15.5px;margin-bottom:4px;color:var(--text)}
.card ul{padding-left:20px;margin:8px 0}
.card hr{border:none;border-top:1px dashed var(--border);margin:18px 0}
.card a{color:var(--accent);text-decoration:none;font-weight:600;font-size:13px;display:inline-flex;align-items:center;gap:4px;background:var(--accent-soft);padding:4px 12px;border-radius:999px;margin-top:2px}
.card a:hover{filter:brightness(1.08)}
.card a::after{content:"→";font-weight:700}
.empty{color:var(--muted);padding:30px 0;text-align:center;font-size:14px}
footer{max-width:920px;margin:0 auto;padding:0 16px 40px;color:var(--muted);font-size:12px;text-align:center}
@media (max-width:640px){.wrap{flex-direction:column}aside{position:static;width:100%}aside ul{display:flex;flex-wrap:wrap;gap:6px}aside li{margin:0}}
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
    icon_prefix = "../" if is_archive else ""
    home_link = '<a href="../index.html">← Retour à aujourd\'hui</a>' if is_archive else ""
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="theme-color" content="{THEME_COLOR}">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="{SITE_TITLE}">
<link rel="apple-touch-icon" href="{icon_prefix}icon-180.png">
<link rel="icon" type="image/png" sizes="192x192" href="{icon_prefix}icon-192.png">
<style>{STYLE}</style>
</head>
<body>
<header class="hero">
  <div class="hero-inner">
    <h1>📰 Veille IA &amp; Cybersécurité</h1>
    <div class="subtitle">{date_str}{(' · ' + home_link) if home_link else ''}</div>
  </div>
</header>
<div class="wrap">
<main>
<div class="card">{body_html}</div>
</main>
{_sidebar_html(manifest, current_date, base_prefix)}
</div>
<footer>Généré automatiquement chaque matin · pipeline perso</footer>
</body>
</html>"""


def generate_page(briefing_markdown):
    today = date.today().isoformat()
    today_display = date.today().strftime("%d/%m/%Y")
    body_html = md.markdown(briefing_markdown, extensions=["extra", "nl2br"])

    os.makedirs(ARCHIVE_DIR, exist_ok=True)

    manifest = _load_manifest()
    manifest = [e for e in manifest if e["date"] != today]
    manifest.insert(0, {"date": today, "file": f"{today}.html"})
    manifest = manifest[:60]
    _save_manifest(manifest)

    archive_html = _page_html(
        f"Veille du {today_display}", today_display, body_html,
        manifest, today, base_prefix="", is_archive=True,
    )
    with open(os.path.join(ARCHIVE_DIR, f"{today}.html"), "w", encoding="utf-8") as f:
        f.write(archive_html)

    index_html = _page_html(
        f"Veille IA & Cybersécurité — {today_display}", today_display, body_html,
        manifest, today, base_prefix="archive/", is_archive=False,
    )
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"[webpage] Page générée pour {today}, historique de {len(manifest)} jour(s).")


if __name__ == "__main__":
    generate_page(
        "## 🎯 À retenir aujourd'hui\nUn test de rendu visuel de la page.\n\n"
        "## 🤖 IA\n**Un premier exemple d'article**\nCeci est un résumé de test sur deux lignes pour vérifier l'espacement.\n[Lire plus](https://example.com)\n\n"
        "**Un second exemple**\nAutre résumé de test.\n[Lire plus](https://example.com)\n\n"
        "## 🔒 Cybersécurité\n**Une faille de test**\nDescription de la faille fictive pour vérifier le rendu.\n[Lire plus](https://example.com)"
    )
