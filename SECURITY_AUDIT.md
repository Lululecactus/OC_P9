# Audit de sécurité — LITRevu

Date : 17 novembre 2026.

## Conclusion

Aucune injection SQL ni exécution de script par les champs texte n’a été mise
en évidence dans les parcours examinés. Les protections Django sont utilisées
correctement pour les requêtes, l’échappement HTML, les mots de passe et CSRF.
Des corrections ont été apportées aux médias et aux dépendances.

**L’application reste destinée à une démonstration locale. Cet audit ne valide
pas un déploiement public ni une absence absolue de vulnérabilités.** La base
versionnée contient des données d’authentification et les tentatives de connexion
ne sont pas limitées. Ces points restent ouverts.

## Périmètre et méthode

- Lecture des modèles, formulaires, vues, routes, templates, JavaScript,
  administration, paramètres Django et règles Git.
- Tests HTTP avec le client Django sur une base temporaire, dont un client avec
  les contrôles CSRF réellement activés.
- Saisies SQL hostiles, XSS stockée et réfléchie, tentatives de changement
  d’auteur, accès aux objets d’autrui, fichiers invalides et traversée de chemins.
- Vérification des versions installées, `pip check`, `pip-audit 2.10.1` sur les
  quatre dépendances épinglées, contrôles système et de déploiement Django.
- Lecture de nombres agrégés dans une copie temporaire de la base du dernier
  commit. Aucun mot de passe, hash, nom de compte ou jeton de session n’est publié
  dans ce rapport. La base de travail n’a pas été modifiée.

Ce travail n’inclut pas de test d’intrusion sur un serveur distant, de test de
charge, d’audit du système d’exploitation, ni d’exécution des charges XSS dans
un navigateur. Les tests XSS vérifient les réponses HTML échappées.

## Constats et corrections

### 1. Images accessibles sans contrôle d’accès — corrigé

Avant correction, `config/urls.py` exposait directement le dossier `media/` via
le serveur statique de développement. Connaître l’URL d’une image suffisait à
la consulter, sans appliquer les règles du fil de lecture.

La route passe maintenant par `reviews.views.ticket_image` : connexion exigée,
image liée à un billet ou à une critique visible, réponse 404 pour un tiers.
Une critique personnelle reste visible après un désabonnement, image comprise.
La réponse utilise un type MIME lu dans l’image, `nosniff`, une politique CSP
restrictive et l’interdiction de mise en cache. Aucun chemin reçu n’est ouvert
directement : il doit correspondre à une image autorisée en base.

**Pour tout hébergement ultérieur, ne pas exposer `MEDIA_ROOT` par un alias
public qui contournerait cette vue.** Les anciennes images hors PNG/JPEG/WebP
ne sont plus servies par cette route et doivent être converties si nécessaire.

### 2. Validation des fichiers insuffisamment bornée — renforcée

`ImageField` vérifiait déjà que le fichier était une image ; un simple script
renommé `.png` et une extension `.html` n’étaient pas acceptés par ce champ.
Il n’y avait cependant pas de limite métier explicite de taille/dimensions,
ni de réencodage supprimant les données ajoutées au fichier.

Le champ partagé `CoverImageField` accepte désormais PNG/JPEG/WebP, limite
l’entrée à 5 Mo et 12 millions de pixels, décode l’image puis réencode uniquement
ses pixels en PNG sous un nom aléatoire. Le résultat est également limité à 5 Mo.
Métadonnées, animations et contenu ajouté ne sont pas conservés. Le formulaire
de l’administration utilise le même champ. Les modifications sans nouvelle
image et la suppression explicite d’une image sont testées.

Il s’agit d’une réduction du risque, pas d’un antivirus ni d’une protection
complète contre le déni de service : la taille totale des requêtes doit aussi
être limitée en amont du serveur Django.

### 3. Django sans le dernier correctif de sécurité — corrigé

Django est passé de 5.2.18 à 5.2.19 dans `requirements.txt` et l’environnement
local. Cette version corrige notamment un risque de consommation mémoire lors
d’envois multipart encodés en base64, pertinent pour les formulaires avec images.
Les autres avis de cette publication ne signifient pas que tous leurs scénarios
sont exploitables dans cette application.
Source : [publication officielle du 3 novembre 2026](https://www.djangoproject.com/weblog/2026/nov/03/security-releases/).

Après correction, `pip-audit` ne relève aucune vulnérabilité connue pour
asgiref 3.13.0, Django 5.2.19, Pillow 13.0.0 et sqlparse 0.6.0.
Le résultat brut est conservé dans `security/dependency-audit.json`.
Ce résultat dépend des avis disponibles à la date du contrôle, et ne concerne
pas les bibliothèques système ou les versions futures.

### 4. Autres durcissements

- Les formulaires d’inscription et de billet refusent les méthodes autres que
  GET et POST ; les suppressions restent effectuées uniquement par POST.
- Retrait de deux filtres `safe` inutiles sur les textes d’aide. Aucune donnée
  utilisateur n’y arrivait actuellement : c’est un durcissement préventif.

## Protections vérifiées

| Domaine | Résultat et preuves |
| --- | --- |
| Injection SQL | Aucun SQL brut construit depuis les entrées dans le code applicatif. Les chaînes SQL hostiles sont des valeurs de l’ORM ; elles ne suppriment pas de table et ne permettent pas de se connecter. |
| XSS | Les titres, descriptions, critiques et noms saisis sont échappés dans les pages et attributs HTML examinés. Tests dans le fil, les formulaires, les confirmations et l’authentification. |
| JavaScript | Les `innerHTML` du livre animé reçoivent du HTML issu des templates Django de même origine ou des chaînes constantes. Aucun passage direct d’une saisie brute vers ces insertions n’a été trouvé. |
| CSRF | Middleware actif, jetons dans les formulaires, aucun `csrf_exempt`. Toutes les mutations des publications/abonnements refusent un jeton absent ou une origine étrangère, même avec un jeton valide. Tests existants pour inscription, connexion et déconnexion. |
| Autorisations | Modifications/suppressions filtrées par auteur connecté ; un auteur de billet ne peut pas supprimer la critique d’un autre lecteur. Auteur et billet liés ne sont pas remplaçables par des champs POST forgés. |
| Authentification | Hachage Django, validation des mots de passe, refus des comptes inactifs, absence de droits admin à l’inscription ; tests existants et nouveaux tests SQL. |
| Sessions et redirections | Cookie de session HttpOnly et SameSite=Lax ; déconnexion POST ; redirection externe de connexion refusée par Django. |
| En-têtes | Hôte étranger refusé, `X-Frame-Options: DENY` et `X-Content-Type-Options: nosniff` vérifiés. |
| Exécution de code | Pas d’`eval`, de désérialisation pickle, de commande shell ou de requête réseau construite depuis les formulaires dans le code applicatif examiné. |

L’ORM utilise des requêtes paramétrées. Il n’est pas nécessaire d’interdire les
apostrophes ou les mots SQL dans un titre : on sépare les données des commandes.
L’échappement HTML empêche de traiter les textes comme des balises.
Référence : [protections et limites de Django](https://docs.djangoproject.com/en/5.2/topics/security/).

## Points ouverts

### Priorité haute : base de données dans Git

La base du dernier commit contient **1 compte avec un hash de mot de passe
utilisable et 3 lignes de session**. La validité actuelle des sessions n’a pas
été établie. Un hash n’est pas un mot de passe en clair, mais sa diffusion permet
des tentatives de cassage hors ligne ; les données de session sont également
sensibles. Le caractère public ou privé du dépôt distant n’a pas été vérifié.

La mission demande une base de démonstration : livrer une copie préparée avec
des comptes fictifs dédiés, sans sessions, sans coordonnées réelles, et sans mot
de passe réutilisé. Si les données versionnées sont réelles ou ont été exposées,
changer les mots de passe concernés, invalider les sessions et traiter
l’historique Git avec le propriétaire du dépôt. Un simple nouveau commit ne
retire pas les anciennes données. Aucune suppression de données ni réécriture
d’historique n’a été réalisée pendant cet audit.

### Priorité haute avant publication : configuration locale

`check --deploy` conserve six avertissements : `security.W004`, `W008`, `W012`,
`W016`, `W018`, `W020`. Ils correspondent à l’absence d’HSTS, de redirection HTTPS,
de cookies Secure, à `DEBUG=True` et aux hôtes de production non configurés.
Ils n’ont pas été masqués. Laisser le serveur de développement sur l’interface
locale ; avant une mise en ligne, préparer et tester une configuration de
production avec HTTPS, des hôtes explicites, une clé secrète dédiée et DEBUG
désactivé. Activer HSTS seulement après validation de HTTPS.

### Priorité moyenne avant publication : force brute et abus

Il n’existe pas de limitation persistante des tentatives sur `/connexion/`,
`/admin/login/` et `/inscription/`. Prévoir une limitation adaptée avec un stockage
partagé ou au niveau du serveur frontal, puis tester le blocage, l’expiration
et les utilisateurs partageant une IP. Django ne fournit pas cette limitation
par défaut. Aucun mécanisme de limitation n’a été ajouté dans cet audit.

Limiter également le corps HTTP avant son traitement, les volumes de fichiers
et la fréquence des publications. Le fil charge et trie actuellement toutes les
publications visibles : une pagination sera utile pour maîtriser la charge.
Les anciens fichiers remplacés/supprimés et un échec SQL après écriture d’une
image peuvent laisser des fichiers orphelins ; prévoir leur nettoyage contrôlé.

### Secrets

La clé locale actuelle est exclue de Git et n’a pas été affichée. Le README
signale une ancienne clé de développement dans l’historique ; ne jamais la
réutiliser. L’audit n’a pas effectué de recherche exhaustive de secrets sur
tous les commits ni inspecté les secrets d’un hébergement distant.

## Vérifications et reproduction

Résultats obtenus après corrections : **75 tests réussis**, aucun problème
signalé par les contrôles système ordinaires, aucune migration à générer,
aucune incohérence de dépendances, aucun défaut d’espacement dans le diff.
Les tests de sécurité utilisent une base temporaire et des dossiers médias
temporaires ; ils n’injectent aucune charge dans la base de démonstration.

```bash
python manage.py test
python manage.py test accounts.test_security reviews.test_security
python manage.py check
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
python -m pip check
git diff --check
```

Pour reproduire l’audit des dépendances, installer `pip-audit` dans un
environnement d’outillage séparé puis exécuter depuis le projet :

```bash
pip-audit -r requirements.txt --no-deps --disable-pip --format json
```

Les quatre dépendances d’exécution sont épinglées dans ce fichier. Refaire cet
audit à chaque mise à jour ; un résultat sans vulnérabilité connue n’est pas
une certification de sécurité.
