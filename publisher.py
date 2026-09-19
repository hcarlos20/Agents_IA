"""
Agent 4 - Publieur
Envoie le briefing sur Telegram. Découpe automatiquement si le message dépasse
la limite de 4096 caractères de l'API Telegram.
"""
import os
import requests

TELEGRAM_MAX_LEN = 4000  # marge de sécurité sous la limite réelle de 4096


def _chunk_message(text, max_len=TELEGRAM_MAX_LEN):
    chunks = []
    while len(text) > max_len:
        split_at = text.rfind("\n\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:]
    chunks.append(text)
    return chunks


def send_telegram(text):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    for chunk in _chunk_message(text):
        resp = requests.post(url, data={
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }, timeout=15)
        if resp.status_code != 200:
            # Si le Markdown casse l'envoi (caractères spéciaux mal échappés), on retente en texte brut
            print(f"[publisher] Échec envoi Markdown ({resp.status_code}), retry en texte brut.")
            resp2 = requests.post(url, data={
                "chat_id": chat_id,
                "text": chunk,
                "disable_web_page_preview": True,
            }, timeout=15)
            resp2.raise_for_status()

    print("[publisher] Briefing envoyé sur Telegram.")


if __name__ == "__main__":
    send_telegram("✅ Test : le pipeline de publication fonctionne.")