"""
Agent 3 - Résumeur / Rédacteur
Prend les items filtrés et produit un briefing Markdown structuré via l'API OpenAI.
C'est ici qu'on itère sur le prompt pour améliorer la qualité au fil du temps.
"""
import os
import json
from openai import OpenAI

# gpt-4o-mini : largement suffisant pour un résumé structuré, très économique.
# Pour plus de qualité rédactionnelle plus tard : gpt-4.1-mini (un peu plus cher).
MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """Tu es un analyste veille technologique spécialisé en Intelligence Artificielle \
et en cybersécurité. Tu rédiges un briefing quotidien clair, direct, sans blabla, pour quelqu'un \
qui a 5 minutes le matin et veut l'essentiel.

Règles :
- Commence par une section "🎯 À retenir aujourd'hui" : 2-3 phrases sur ce qui compte vraiment, \
s'il y a un signal fort dans les items du jour.
- Puis une section "🤖 IA" et une section "🔒 Cybersécurité" (ignore une section si aucun item \
pertinent de cette catégorie).
- Pour chaque item : un titre court, 2-3 lignes de résumé qui expliquent CE QUE C'EST et \
POURQUOI ÇA COMPTE (pas juste reformuler le titre), puis le lien.
- Pas de flatterie, pas d'intro type "voici votre briefing". Va droit au but.
- Format Markdown, prêt à être envoyé tel quel."""


def build_user_prompt(items):
    items_text = "\n\n".join(
        f"- Titre: {it['title']}\n  Source: {it['source']}\n  Lien: {it['link']}\n  Extrait: {it.get('excerpt', '')[:300]}"
        for it in items
    )
    return f"Voici les items collectés aujourd'hui ({len(items)} items) :\n\n{items_text}\n\nRédige le briefing."


def summarize(items):
    if not items:
        return "Aucune actualité pertinente aujourd'hui (ou tout a déjà été vu récemment)."

    client = OpenAI()  # lit OPENAI_API_KEY depuis l'environnement
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=1500,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(items)},
        ],
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    from collector import collect_all
    from filter_dedup import filter_and_dedup

    raw = collect_all()
    final_items = filter_and_dedup(raw)
    briefing = summarize(final_items)
    print(briefing)