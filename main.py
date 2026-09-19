"""
Orchestrateur principal du pipeline de veille quotidienne.
Collecteur -> Filtre/Dédup -> Résumeur -> Publieur
"""
from datetime import date
from collector import collect_all
from filter_dedup import filter_and_dedup
from summarizer import summarize
from publisher import send_telegram
from webpage import generate_page


def run():
    print(f"=== Pipeline veille du {date.today().isoformat()} ===")

    raw_items = collect_all()
    filtered_items = filter_and_dedup(raw_items)
    briefing = summarize(filtered_items)

    header = f"📰 *Veille IA & Cybersécurité — {date.today().strftime('%d/%m/%Y')}*\n\n"
    send_telegram(header + briefing)

    # Agent 5 : ne doit jamais faire planter l'envoi Telegram déjà réussi
    try:
        generate_page(briefing)
    except Exception as e:
        print(f"[main] La génération de la page web a échoué (non bloquant): {e}")

    print("=== Pipeline terminé avec succès ===")


if __name__ == "__main__":
    run()