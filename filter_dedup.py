"""
Agent 2 - Filtre / Dédoublonneur
- Supprime les doublons internes (titres très similaires).
- Supprime les items déjà envoyés lors des N derniers jours (via state.json).
- Limite le nombre d'items final pour ne pas surcharger l'Agent 3 (économie de quota LLM).
"""
import json
import os
from difflib import SequenceMatcher
from datetime import datetime, timedelta, timezone

STATE_FILE = os.path.join(os.path.dirname(__file__), "state.json")
MEMORY_DAYS = 3       # on évite de re-signaler un item déjà vu dans les 3 derniers jours
MAX_ITEMS_OUT = 20    # nombre max d'items transmis à l'Agent 3 (résumeur)


def _load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"sent_links": {}}  # {link: iso_date}


def _save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def _titles_similar(a, b, threshold=0.82):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() >= threshold


def _dedup_internal(items):
    kept = []
    for item in items:
        if not item.get("title"):
            continue
        if any(_titles_similar(item["title"], k["title"]) for k in kept):
            continue
        kept.append(item)
    return kept


def _remove_already_sent(items, state):
    cutoff = datetime.now(timezone.utc) - timedelta(days=MEMORY_DAYS)
    sent_links = state.get("sent_links", {})

    # nettoyage : on purge les entrées trop vieilles du state pour qu'il ne grossisse pas indéfiniment
    fresh_sent = {}
    for link, date_str in sent_links.items():
        try:
            d = datetime.fromisoformat(date_str)
            if d >= cutoff:
                fresh_sent[link] = date_str
        except ValueError:
            continue
    state["sent_links"] = fresh_sent

    return [item for item in items if item.get("link") not in fresh_sent]


def filter_and_dedup(raw_items):
    state = _load_state()

    items = _dedup_internal(raw_items)
    items = _remove_already_sent(items, state)

    # Tri simple : on met en avant les items qui ont une date connue (plus fiable), puis on tronque
    items.sort(key=lambda x: x.get("published") or "", reverse=True)
    items = items[:MAX_ITEMS_OUT]

    # On marque ces items comme "envoyés" dès maintenant (optimiste : on suppose que le pipeline ira au bout)
    now_iso = datetime.now(timezone.utc).isoformat()
    for item in items:
        if item.get("link"):
            state["sent_links"][item["link"]] = now_iso
    _save_state(state)

    print(f"[filter] {len(items)} items retenus après dédup et filtrage mémoire.")
    return items


if __name__ == "__main__":
    from collector import collect_all
    raw = collect_all()
    final = filter_and_dedup(raw)
    print(json.dumps(final, indent=2, ensure_ascii=False))