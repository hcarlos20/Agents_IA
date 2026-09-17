# Veille quotidienne IA & Cybersécurité

Pipeline à 4 agents qui envoie chaque jour sur Telegram un résumé structuré de
l'actualité IA et cybersécurité, agrégée depuis plusieurs sources gratuites.

```
collector.py  →  filter_dedup.py  →  summarizer.py  →  publisher.py
 (Agent 1)         (Agent 2)           (Agent 3)          (Agent 4)
```

## Setup

### 1. Tester en local

```bash
pip install -r requirements.txt

export ANTHROPIC_API_KEY="sk-ant-..."
export TELEGRAM_BOT_TOKEN="123456:AAE..."
export TELEGRAM_CHAT_ID="123456789"

python main.py
```

Si tu veux tester un agent isolément (utile pour itérer sur le prompt sans
refaire tourner tout le pipeline) :

```bash
python collector.py       # affiche les items bruts
python filter_dedup.py    # affiche les items après dédup
python summarizer.py      # affiche le briefing texte (sans l'envoyer)
python publisher.py       # envoie juste un message de test sur Telegram
```

### 2. Déployer sur GitHub Actions (gratuit, pas de serveur nécessaire)

1. Pousse ce dossier dans un repo GitHub (privé de préférence, pour ne pas
   exposer `state.json` et la logique publiquement — même si aucun secret n'y
   est stocké en clair).
2. Dans **Settings → Secrets and variables → Actions**, ajoute 3 secrets :
   - `ANTHROPIC_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
3. Le workflow `.github/workflows/veille-quotidienne.yml` est déjà configuré
   pour tourner tous les jours à 6h UTC. Tu peux aussi le lancer manuellement
   depuis l'onglet **Actions → Veille quotidienne IA & Cybersécurité → Run workflow**
   pour tester sans attendre le lendemain.

### 3. Activer la mini interface (GitHub Pages, gratuit)

Le pipeline génère automatiquement une page web dans `docs/` à chaque run
(Agent 5, `webpage.py`) : le briefing du jour + un historique cliquable.
Pour la rendre accessible via une URL publique :

1. Sur le repo GitHub : **Settings → Pages**.
2. Dans **Source**, choisis **Deploy from a branch**.
3. Branche : `main`, dossier : `/docs`. Sauvegarde.
4. Après le premier run du workflow (qui commit le dossier `docs/`), GitHub
   te donne une URL du type `https://<ton-user>.github.io/<ton-repo>/`.
5. Sur ton téléphone, ouvre cette URL dans le navigateur puis
   "Ajouter à l'écran d'accueil" — tu as une icône comme une vraie app,
   sans rien avoir eu à coder de natif ni à payer d'hébergement.

La page se met à jour toute seule chaque matin après le run du pipeline.

### 4. Environnement Docker (apprentissage + préparation du futur serveur)

Le pipeline est containerisé. Ça ne remplace pas GitHub Actions pour l'instant
(inutile de complexifier ce qui marche déjà), mais ça te permet de :
- tester en local dans un environnement identique à celui que tu auras sur ton
  futur serveur ;
- être prêt à migrer sans rien réécrire quand le serveur arrivera.

```bash
cp .env.example .env        # puis remplis tes 3 vraies clés dans .env
touch state.json            # fichier vide au premier lancement
docker compose up --build
```

Ce que ça fait concrètement :
- `docker compose build` lit le `Dockerfile`, installe Python + les dépendances
  dans une image isolée (aucun conflit avec ce qui est installé sur ta machine).
- `docker compose up` lance le conteneur, qui exécute `main.py` une fois puis
  s'arrête (comme le ferait GitHub Actions).
- Les volumes (`./state.json` et `./docs`) font le pont entre le conteneur
  (éphémère) et ton disque (persistant) — sans ça, la mémoire anti-doublons
  et l'historique de la page web repartiraient de zéro à chaque run.

**Sur le futur serveur**, tu auras le choix entre : garder GitHub Actions comme
déclencheur (le serveur exécute juste `docker compose run veille` chaque jour
via un cron système), ou passer à un scheduler intégré à Docker (voir le
service `scheduler` commenté dans `docker-compose.yml`, basé sur Ofelia) pour
devenir totalement autonome de GitHub.

### 5. Notes de fonctionnement

- `state.json` garde en mémoire les liens déjà envoyés sur les 3 derniers
  jours (`MEMORY_DAYS` dans `filter_dedup.py`), pour ne jamais répéter un item.
  Ce fichier est commité automatiquement par le workflow après chaque run.
- Si une source RSS est down un jour, elle est simplement ignorée (log dans
  la sortie du job) — le pipeline continue avec les autres sources.
- Pour ajuster les sources : édite le dict `RSS_SOURCES` dans `collector.py`.
- Pour ajuster le ton/format du briefing : édite `SYSTEM_PROMPT` dans
  `summarizer.py` — c'est le vrai levier de qualité, à itérer au fil des jours.

## Prochaines évolutions possibles

- Ajouter un scoring de pertinence plus fin dans l'Agent 2 (actuellement
  purement chronologique + dédup textuel).
- Ajouter d'autres sources (flux RSS spécifiques à tes centres d'intérêt).
- Migrer vers un environnement auto-hébergé (Hermes Agent, VPS perso) une
  fois le serveur disponible, en réutilisant ces mêmes scripts comme "Skills".
