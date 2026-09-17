# Image de base légère : Python sans tout l'OS complet
FROM python:3.11-slim

# Bonne pratique : ne pas tourner en root dans le conteneur
RUN useradd --create-home --shell /bin/bash veille
WORKDIR /app

# On copie d'abord uniquement requirements.txt : Docker met cette étape en cache
# et ne réinstalle les dépendances que si ce fichier change (build plus rapide).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Puis le reste du code
COPY collector.py filter_dedup.py summarizer.py publisher.py webpage.py main.py ./

# state.json et docs/ doivent survivre entre les runs -> voir docker-compose.yml (volumes)
RUN mkdir -p docs && chown -R veille:veille /app
USER veille

CMD ["python", "main.py"]
