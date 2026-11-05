# LITRevu — projet OpenClassrooms P9

Application Django de critiques littéraires, exécutée en local.

## État actuel

Étapes 1 et 2 : initialisation, modèle utilisateur personnalisé, administration,
inscription, connexion et déconnexion. L’accueil est réservé aux personnes connectées.
Les billets, critiques, abonnements et le véritable flux restent à développer.
La zone d’inscription de la connexion reste à repositionner à gauche pour reprendre
l’organisation du wireframe 1.

## Installation (macOS / Linux)

Le projet a été testé avec Python 3.14 et Django 5.2.18.

```bash
git clone https://github.com/Lululecactus/OC_P9.git
cd OC_P9
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Ouvrir http://127.0.0.1:8000/ : la page d’entrée est la connexion.
Créer un compte depuis « Créer un compte », puis se connecter.
Arrêter le serveur avec Ctrl+C.

SQLite est utilisé. `db.sqlite3` est conservé dans le dépôt conformément à la mission.
Ne pas y placer de données personnelles réelles : cette base est destinée au projet
et à sa démonstration. Les identifiants de démonstration de la livraison finale
restent à documenter ; aucun mot de passe existant n’est supposé connu ici.

## Administration

Pour disposer de son propre accès administrateur :

```bash
python manage.py createsuperuser
```

Ouvrir http://127.0.0.1:8000/admin/ avec ce compte. Les comptes créés par
l’inscription publique ne reçoivent pas de droits d’administration.

## Configuration locale

Au premier démarrage, Django crée `.django-secret-key`, exclu de Git.
Cette clé reste stable entre les démarrages. La variable d’environnement
`DJANGO_SECRET_KEY`, si définie, est prioritaire. Ne pas partager cette clé.
Une ancienne clé de développement figure dans l’historique Git : elle n’est plus
utilisée par défaut. Changer la clé peut invalider les sessions existantes.

Les réglages actuels (`DEBUG=True`) sont réservés au développement local.
Le déploiement public ne fait pas partie de cette étape.

## Vérifications

```bash
python manage.py check
python manage.py showmigrations
python manage.py makemigrations --check --dry-run
python manage.py test accounts
```

Les tests utilisent une base temporaire distincte de `db.sqlite3`.

## Organisation

- `config/` : réglages et routes principales.
- `accounts/` : modèle utilisateur, formulaires, vues, routes et tests.
- `accounts/templates/accounts/` : pages produites par Django.
- `accounts/static/accounts/` : CSS, JavaScript, images et police.

Les formulaires fonctionnent sans les animations JavaScript. Les mouvements
respectent la préférence système de réduction des animations.

## Ressources visuelles

Les deux illustrations de livres sont des images synthétiques générées pour le projet.
Les textures sont réalisées en SVG. La police Allura est accompagnée de sa licence
SIL Open Font License dans `accounts/static/accounts/fonts/OFL-Allura.txt`.
