# Identité visuelle de LITRevu

## Direction retenue pour cette proposition

Un livre ouvert posé sur un fond grège : deux pages ivoire légèrement bombées,
une reliure ombrée, une photographie imprimée sur la page gauche et le formulaire
sur la page droite. La typographie à empattements et les couleurs sobres donnent
une identité de revue littéraire. Une page se tourne après une connexion réussie.
Le contour brun a été remplacé par une couverture de cuir anthracite discrète,
visible surtout sous les feuilles et sur les côtés. Huit feuillets décoratifs,
chacun décalé un peu plus vers l’extérieur et vers le bas, forment la pente des tranches.
Leur papier recouvre la couverture au centre pour éviter une zone sombre en haut
de la reliure. Les textures du cuir et du papier sont en SVG ; les courbes, les
décalages et les ombres restent en CSS. Sur téléphone, le décalage latéral est réduit.
Le sommet des deux pages descend doucement vers la reliure. Le fond du conteneur
est transparent et la page située dessous suit la même courbe : aucun rectangle
ne dépasse au sommet du pli. Les feuillets et la couverture commencent plus bas.
Une ombre diffuse autour d’un pli sombre, accompagnée de reflets sur chaque page,
accentue le creux central et le bombé du papier sans déformer les textes.

L’espace connecté reprend le papier chaud, avec une encre sombre et des accents
bordeaux. Le fil occupe la colonne principale, accompagné d’une note « En marge ».
Le nom du lecteur apparaît en calligraphie. Cette présentation conserve un fil vide
en attendant l’implémentation des publications ; les liens de navigation sont fonctionnels.

## Organisation du code

- `accounts/templates/accounts/base.html` contient les deux pages du livre de connexion.
- `reader_base.html` contient le cadre de l’espace connecté : navigation, déconnexion et pied de page.
- `login.html` hérite de `base.html` ; `home.html` hérite de `reader_base.html`.
- L’accueil présente pour le moment un état vide statique. Le flux de publications sera implémenté à son étape dédiée.
- `accounts/static/accounts/style.css` définit la présentation et les adaptations mobiles.
- `accounts/static/accounts/book.js` ajoute la transition après validation des identifiants.
- `accounts/static/accounts/reader-entry.js` assure le fondu d’arrivée dans l’espace lecteur.
- `accounts/static/accounts/fonts/Allura-Regular.ttf` fournit la calligraphie localement,
  accompagnée de sa licence `OFL-Allura.txt`.
- `accounts/static/accounts/images/paper-grain.svg` produit le grain du papier.
- `accounts/static/accounts/images/leather-grain.svg` produit le grain du cuir.
- `accounts/static/accounts/images/reading-editorial.png` est une image générée,
  décorative (attribut `alt` vide), conservée dans le projet et servie localement.

Les textes courants utilisent les polices du système. La calligraphie Allura est
servie depuis le projet ; aucun service de polices externe n’est appelé par le navigateur.
Source : https://github.com/google/fonts/tree/main/ofl/allura — licence SIL Open Font License 1.1.
Le formulaire conserve les étiquettes,
les erreurs et le fonctionnement natif de Django. Un lien d'évitement permet
d'accéder au contenu principal avec le clavier.

## Comprendre le livre et sa transition

1. **HTML : le contenu.** Deux sections représentent la page gauche et la page droite.
   Le formulaire reste un vrai formulaire Django, avec ses étiquettes et son jeton CSRF.
2. **CSS : la matière.** Les dégradés simulent la lumière sur le papier. Les ombres
   sous le livre évoquent l’épaisseur des feuilles. Le texte reste plat pour être lisible.
3. **JavaScript : le mouvement.** Le script envoie le formulaire à Django avec `fetch`.
   Django vérifie les identifiants et ouvre la session. Seulement si la réponse est une
   redirection réussie, une copie décorative de la page se découpe en 24 bandes jointives.
   Leur angle varie progressivement : le bord extérieur devance la reliure, ce qui
   simule une feuille souple. `perspective` donne de la profondeur au mouvement.
   La copie est cachée aux lecteurs d’écran et ne contient ni mot de passe réel ni jeton CSRF.
4. **Le fondu entre les documents.** Un voile ivoire apparaît après le passage de page.
   Le navigateur ouvre la destination renvoyée par Django, puis le même voile s’efface
   en 800 ms. Un repère temporaire dans `sessionStorage` transmet uniquement l’adresse
   attendue et l’heure : il est consommé à l’arrivée et expire après 15 secondes.
   Une visite normale ou un rechargement de l’accueil ne rejoue donc pas le fondu.

Un mot de passe incorrect laisse le livre ouvert : le script affiche le formulaire
et les erreurs renvoyés par Django, puis place le focus sur l’erreur. Le bouton est
désactivé pendant l’envoi pour éviter plusieurs clics. Une erreur réseau affiche un
message et permet de réessayer, sans renvoi automatique du mot de passe.

Sans JavaScript, ou si la préférence système de réduction des animations est activée,
le formulaire suit son fonctionnement HTML habituel. Sur téléphone, le livre conserve
son en-tête et le formulaire ; la photographie et les textes décoratifs sont masqués
pour garder des champs confortables dans la hauteur disponible. Le mouvement est plus court.
Le bouton Retour remet la feuille dans sa position de départ.

La hauteur du livre dépend de celle de la fenêtre (`100dvh`), avec une marge réservée
pour la couverture et les tranches. Les deux légendes extérieures ont été retirées.
Les espacements diminuent sur les fenêtres basses pour éviter un défilement de la page.
En cas de très fort zoom ou de hauteur exceptionnellement réduite, seul l’intérieur
du formulaire peut défiler afin de conserver l’accès aux champs et aux erreurs.

Le bouton de connexion reprend le bordeaux de l’espace lecteur, avec un texte ivoire
à empattements. Au survol et au focus clavier, la teinte s’éclaircit progressivement
et la flèche avance légèrement. Le focus reste matérialisé par un contour visible.
La préférence de réduction des animations supprime ces mouvements.

L’espace connecté conserve son propre cadre : le livre est la porte d’entrée,
le fil de lecture est l’espace d’utilisation. Cette étape ne crée pas encore de publications.

## La signature d’accueil

Le titre reste du texte HTML et affiche le véritable nom d’utilisateur, échappé
automatiquement par Django. La police Allura dessine les lettres liées.
Une animation CSS `clip-path` révèle progressivement la phrase de gauche à droite,
puis le nom : c’est une illusion d’écriture par dévoilement, pas un tracé des traits
individuels de chaque lettre. La révélation démarre après le fondu de connexion.
Le lecteur d’écran dispose immédiatement du titre complet via `aria-label`.
La préférence `prefers-reduced-motion` désactive le mouvement. Les noms très longs
peuvent revenir à la ligne et s’affichent directement pour conserver leur lisibilité.

## Origine de l'image

Créée avec l'outil intégré ImageGen, sans CLI ni clé API personnelle.
Il s'agit d'une image synthétique photoréaliste, et non d'une photographie documentaire.

Prompt exact utilisé :

```text
Use case: photorealistic-natural. Asset type: photographic hero background for an understated luxury French literary journal website, portrait 2:3. A masterfully art-directed real studio still-life photograph: one large open ivory art book with sculptural curved fanned paper pages, resting diagonally on two closed thin linen-bound books on a warm charcoal dark brown stone plinth. Camera at table height at a three-quarter angle. The open book fills the lower center of the image, its ivory pages catching a shaft of warm natural side light from upper left, deep realistic shadows, delicate paper grain and worn page edges. Dark warm espresso plaster background, nearly black at top third; large clean negative space in upper half for a headline to be overlaid later by HTML. Architectural, tactile, sophisticated collectible art magazine photography, medium-format lens, subtle analog film grain, restrained gallery lighting, exceptionally realistic. Palette exclusively deep warm charcoal, tobacco shadow, ivory paper and desaturated stone. No legible writing, no text overlay, no logos, no UI, no frames, no people, no plants, no coffee, no candles, no floating objects, no cartoons, no illustration, no colored gradients, no glossy CGI, no gold ornaments. Books occupy lower 55 percent, all critical paper details within central 70 percent for responsive cropping.
```
