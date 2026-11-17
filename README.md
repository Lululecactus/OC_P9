# LITRevu — projet OpenClassrooms P9

Application Django de critiques littéraires, exécutée en local.

## État actuel

L’application propose l’inscription, la connexion et la déconnexion, ainsi qu’un
espace réservé aux lecteurs connectés. Ils peuvent créer, modifier et supprimer
leurs demandes de critique, publier une critique en réponse à une demande visible,
puis modifier ou supprimer leurs propres critiques depuis le fil de lecture.
Ils peuvent aussi créer un billet et sa critique en une seule publication,
avec une image facultative pour le livre ou l’article.
La suppression d’une critique conserve le billet associé.

Le fil réunit les publications du lecteur, celles des personnes suivies et les
critiques répondant à ses propres billets, des plus récentes aux plus anciennes.
La page Abonnements permet de suivre un lecteur actif par son nom d’utilisateur
exact, de se désabonner et de consulter ses abonnements et ses abonnés.
La page des publications personnelles reste à développer.

## Installation (macOS / Linux)

Le projet a été testé avec Python 3.14 et Django 5.2.19.

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
python manage.py test
```

Les tests utilisent une base temporaire distincte de `db.sqlite3`.

## Sécurité

Le [rapport d’audit du 17 novembre 2026](SECURITY_AUDIT.md) décrit les contrôles,
les corrections et les risques restant à traiter. Les tests couvrent notamment
les injections SQL, l’échappement HTML, CSRF, les droits d’accès et les images.
Les images envoyées sont limitées à 5 Mo et 12 millions de pixels, réencodées
en PNG et accessibles uniquement aux lecteurs autorisés à voir la publication.
Les formats d’entrée acceptés sont PNG, JPEG et WebP.

Le projet reste prévu pour un usage local : la base versionnée doit être
préparée avec des données de démonstration et sans sessions avant livraison.
Une mise en ligne nécessite aussi HTTPS, des paramètres de production et une
limitation des tentatives de connexion ; ces protections ne sont pas encore
configurées.

## Organisation

- `config/` : réglages et routes principales.
- `accounts/` : modèle utilisateur, formulaires, vues, routes et tests.
- `reviews/` : billets, critiques, abonnements, formulaires, vues et tests associés.
- `accounts/templates/accounts/` : pages produites par Django.
- `accounts/static/accounts/` : CSS, JavaScript, images et police.

Les formulaires fonctionnent sans les animations JavaScript. Les mouvements
respectent la préférence système de réduction des animations.

## Ressources visuelles

Les deux illustrations de livres sont des images synthétiques générées pour le projet.
Les textures sont réalisées en SVG. La police Allura est accompagnée de sa licence
SIL Open Font License dans `accounts/static/accounts/fonts/OFL-Allura.txt`.
