/* Le livre suit l’ordre inscription (1–2), connexion (3–4), bienvenue (5–6).
   Django reste responsable des comptes ; sans animation, les liens et formulaires fonctionnent. */
(() => {
    const book = document.querySelector('.account-layout');
    const panel = book?.querySelector('.account-panel');
    const editorial = book?.querySelector('.editorial');
    const content = panel?.querySelector('.account-content');
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (!book || !panel || !content || !window.fetch || !panel.animate) return;
    let busy = false;
    let turningSheet;
    let castShadow;
    let exitVeil;

    function showMessage(message) {
        const status = content.querySelector('.login-status');
        if (status) status.textContent = message;
    }

    function resetBook() {
        turningSheet?.remove();
        castShadow?.remove();
        exitVeil?.remove();
        book.classList.remove('is-turning');
        book.removeAttribute('aria-busy');
        busy = false;
        book.querySelectorAll('button[type="submit"]').forEach(button => button.disabled = false);
    }

    // On lit le HTML renvoyé par Django pour en extraire les deux pages du livre.
    function readSpread(html) {
        const page = new DOMParser().parseFromString(html, 'text/html');
        const left = page.querySelector('.editorial');
        const right = page.querySelector('.account-panel');
        if (!left || !right) throw new Error('Page du livre indisponible.');
        return { left, right, signup: page.body.classList.contains('signup-page'), title: page.title };
    }

    // async/await permet d’attendre le serveur sans bloquer tout le navigateur.
    async function fetchSpread(url) {
        const response = await fetch(url, { credentials: 'same-origin' });
        if (!response.ok || new URL(response.url).origin !== location.origin) {
            throw new Error('Page du livre indisponible.');
        }
        return readSpread(await response.text());
    }

    function setLeft(spread) { editorial.innerHTML = spread.left.innerHTML; }
    function setRight(spread) {
        // Conserver le conteneur permet de conserver les écouteurs d’événements.
        content.innerHTML = spread.right.querySelector('.account-content').innerHTML;
        panel.querySelector('.panel-footer').innerHTML = spread.right.querySelector('.panel-footer').innerHTML;
        document.body.classList.toggle('signup-page', spread.signup);
        content.scrollTop = 0;
        document.dispatchEvent(new Event('account-form-updated'));
    }

    function applySpread(spread) { setLeft(spread); setRight(spread); }

    // Ces copies servent seulement à dessiner la feuille pendant son mouvement.
    function decorativeCopy(source, width, height, offset) {
        const copy = source.cloneNode(true);
        copy.classList.add('paper-copy');
        copy.removeAttribute('aria-labelledby');
        copy.querySelectorAll('[id]').forEach(element => element.removeAttribute('id'));
        copy.querySelectorAll('label[for]').forEach(label => label.removeAttribute('for'));
        copy.querySelectorAll('[aria-controls], [aria-describedby]').forEach(element => {
            element.removeAttribute('aria-controls');
            element.removeAttribute('aria-describedby');
        });
        copy.querySelectorAll('input').forEach(input => {
            // Même un mot de passe révélé ne doit pas être copié dans les feuilles.
            if (input.type === 'password' || input.closest('.password-control')) {
                input.type = 'password';
                input.value = input.value ? '••••••••' : '';
                input.removeAttribute('value');
            }
            if (input.type === 'hidden') { input.value = ''; input.removeAttribute('value'); }
            input.removeAttribute('name');
            input.removeAttribute('autofocus');
        });
        copy.querySelectorAll('.password-toggle').forEach(button => {
            button.hidden = false;
            button.closest('.password-control').classList.add('has-toggle');
        });
        Object.assign(copy.style, { width: `${width}px`, height: `${height}px`, left: `${offset}px` });
        return copy;
    }

    async function turnTo(spread, direction = 'forward') {
        if (reducedMotion.matches) { applySpread(spread); return; }
        const backwards = direction === 'backward';
        const mobile = window.matchMedia('(max-width: 720px)').matches;
        const source = backwards && !mobile ? editorial : panel;
        const destination = backwards ? spread.right : spread.left;
        const width = source.offsetWidth;
        const height = source.offsetHeight;
        // Plusieurs bandes tournent avec des angles différents : la feuille paraît souple.
        const count = 24;
        const stripWidth = width / count;
        const sheet = document.createElement('div');
        sheet.className = 'turning-sheet';
        sheet.setAttribute('aria-hidden', 'true');
        sheet.inert = true;
        Object.assign(sheet.style, {
            left: `${source.offsetLeft + (backwards ? width : 0)}px`,
            top: `${source.offsetTop}px`, width: `${width}px`, height: `${height}px`,
        });
        const strips = [];
        for (let index = 0; index < count; index++) {
            const strip = document.createElement('div');
            strip.className = 'paper-strip';
            strip.style.width = `${stripWidth + 1.5}px`;
            const front = document.createElement('div');
            front.className = 'paper-front';
            front.append(decorativeCopy(source, width, height, -index * stripWidth));
            const back = document.createElement('div');
            back.className = 'paper-back';
            back.append(decorativeCopy(destination, width, height, -(count - 1 - index) * stripWidth));
            strip.append(front, back);
            sheet.append(strip);
            strips.push(strip);
        }
        turningSheet = sheet;
        // La lumière vient du haut à gauche : l’ombre tombe à droite et un peu plus bas.
        // Elle reste sur le plan du livre, sous la feuille qui tourne.
        const shadow = document.createElement('div');
        shadow.className = 'page-cast-shadow';
        shadow.setAttribute('aria-hidden', 'true');
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('viewBox', `0 0 ${book.clientWidth} ${book.clientHeight}`);
        svg.setAttribute('preserveAspectRatio', 'none');
        const silhouette = document.createElementNS(svg.namespaceURI, 'polygon');
        svg.append(silhouette);
        shadow.append(svg);
        castShadow = shadow;
        book.classList.add('is-turning');
        book.append(shadow, sheet);
        // La nouvelle page se dévoile sous la feuille ; l’autre reste visible jusqu’à l’arrivée.
        if (backwards && !mobile) setLeft(spread);
        else setRight(spread);
        const duration = mobile ? 950 : 1300;
        try {
            await new Promise(resolve => {
                const start = performance.now();
                // À chaque image, on calcule l’avancement et la courbure de la feuille.
                function frame(now) {
                    const elapsed = Math.min((now - start) / duration, 1);
                    if (reducedMotion.matches) { resolve(); return; }
                    const progress = elapsed * elapsed * (3 - 2 * elapsed);
                    const bend = Math.sin(progress * Math.PI) * .95;
                    let x = 0;
                    let z = 0;
                    const hinge = source.offsetLeft + (backwards ? width : 0);
                    const topEdge = [[hinge, source.offsetTop]];
                    const bottomEdge = [[hinge, source.offsetTop + height]];
                    for (let n = 0; n < count; n++) {
                        const index = backwards ? count - 1 - n : n;
                        const angle = (backwards ? 1 : -1) * (Math.PI * progress - bend * (1 - 2 * (n + .5) / count));
                        if (backwards) { x -= stripWidth * Math.cos(angle); z += stripWidth * Math.sin(angle); }
                        strips[index].style.transform = `translate3d(${x}px, 0, ${z}px) rotateY(${angle}rad)`;
                        strips[index].style.setProperty('--paper-shade', .13 * Math.abs(Math.sin(angle)));
                        if (!backwards) { x += stripWidth * Math.cos(angle); z -= stripWidth * Math.sin(angle); }
                        // Projection des mêmes sommets que ceux de la feuille souple.
                        const lift = Math.max(0, z);
                        const shadowX = hinge + x + lift * .22;
                        const shadowY = source.offsetTop + lift * .045;
                        topEdge.push([shadowX, shadowY]);
                        bottomEdge.push([shadowX, shadowY + height]);
                    }
                    const elevation = Math.sin(progress * Math.PI);
                    silhouette.setAttribute('points', [...topEdge, ...bottomEdge.reverse()]
                        .map(point => point.join(',')).join(' '));
                    silhouette.style.filter = `blur(${2 + 14 * elevation}px)`;
                    shadow.style.opacity = .24 * Math.pow(elevation, .65);
                    if (elapsed < 1) requestAnimationFrame(frame);
                    else resolve();
                }
                frame(start);
            });
            applySpread(spread);
        } finally {
            sheet.remove();
            shadow.remove();
            book.classList.remove('is-turning');
        }
    }

    // On synchronise le contenu, l’adresse, le titre et le focus clavier.
    function openSpread(spread, destination) {
        applySpread(spread);
        history.pushState(null, '', destination);
        document.title = spread.title;
        const heading = content.querySelector('h1');
        heading.tabIndex = -1;
        heading.focus({ preventScroll: true });
    }

    function readerSpread() {
        // Une page de seuil, uniquement décorative, avant l’accueil réel.
        const spread = { left: editorial.cloneNode(true), right: panel.cloneNode(true), signup: false };
        spread.left.querySelector('.editorial-copy').innerHTML = '<p class="eyebrow">Au fil des lectures</p><h2 id="editorial-title">Le prochain chapitre<br><em>vous appartient.</em></h2>';
        spread.left.querySelector('.editorial-footer > span:last-child').textContent = '5';
        spread.right.querySelector('.account-content').innerHTML = '<p class="section-label">Votre espace de lecture</p><h1>Bienvenue<br><em>parmi les lecteurs.</em></h1><p class="form-intro">Les livres nous rassemblent.</p>';
        spread.right.querySelector('.panel-footer > span:last-child').textContent = '6';
        return spread;
    }

    // Le marqueur relie le fondu de départ à celui de la page d’accueil.
    async function fadeToReader(destination) {
        if (reducedMotion.matches) return;
        try {
            sessionStorage.setItem('litrevu-reader-entry', JSON.stringify({
                path: destination.pathname + destination.search, time: Date.now(),
            }));
        } catch { /* La navigation reste possible sans stockage. */ }
        exitVeil = document.createElement('div');
        exitVeil.className = 'reader-transition-veil';
        exitVeil.setAttribute('aria-hidden', 'true');
        document.body.append(exitVeil);
        await exitVeil.animate([{ opacity: 0 }, { opacity: 1 }], {
            duration: 750, easing: 'ease-in-out', fill: 'forwards',
        }).finished;
    }

    book.addEventListener('click', async event => {
        const link = event.target.closest('a[data-book-direction]');
        if (!link || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || reducedMotion.matches) return;
        const destination = new URL(link.href);
        if (destination.origin !== location.origin) return;
        event.preventDefault();
        if (busy || destination.pathname === location.pathname) return;
        busy = true;
        book.setAttribute('aria-busy', 'true');
        try {
            const spread = await fetchSpread(destination.href);
            await turnTo(spread, link.dataset.bookDirection);
            openSpread(spread, destination.href);
        } catch { location.assign(destination.href); }
        finally { busy = false; book.removeAttribute('aria-busy'); }
    });

    content.addEventListener('submit', async event => {
        const form = event.target;
        if (!form.matches('[data-book-login], [data-book-signup]') || reducedMotion.matches) return;
        // On gère ici l’envoi pour jouer l’animation après la réponse de Django.
        event.preventDefault();
        if (busy) return;
        busy = true;
        book.setAttribute('aria-busy', 'true');
        const signup = form.hasAttribute('data-book-signup');
        const button = form.querySelector('button[type="submit"]');
        button.disabled = true;
        showMessage(signup ? 'Création de votre compte…' : 'Vérification de vos identifiants…');
        try {
            // FormData inclut les champs et le jeton CSRF du formulaire.
            // Le serveur reste responsable de toutes les validations.
            const response = await fetch(form.action, {
                method: 'POST', body: new FormData(form), credentials: 'same-origin',
            });
            const destination = new URL(response.url);
            if (destination.origin !== location.origin) throw new Error('Destination inattendue.');
            if (response.ok && response.redirected) {
                if (signup) {
                    // Utiliser la réponse reçue conserve le message de confirmation Django.
                    const spread = readSpread(await response.text());
                    try { await turnTo(spread, 'forward'); } catch { turningSheet?.remove(); }
                    openSpread(spread, destination.href);
                } else {
                    try {
                        await turnTo(readerSpread());
                        // Laisser la double page de bienvenue se lire avant le fondu.
                        if (!reducedMotion.matches) {
                            await content.animate([{ opacity: .65 }, { opacity: 1 }], {
                                duration: 700, easing: 'ease-out',
                            }).finished;
                        }
                        await fadeToReader(destination);
                    } catch { /* Une panne du décor ne bloque jamais une connexion réussie. */ }
                    location.assign(destination.href);
                }
                return;
            }
            if (response.ok) {
                const spread = readSpread(await response.text());
                applySpread(spread);
                const error = content.querySelector('.errorlist');
                if (error) { error.tabIndex = -1; error.focus(); }
                return;
            }
            showMessage(response.status === 403
                ? 'Le formulaire a expiré. Rechargez la page avant de réessayer.'
                : 'Le serveur ne peut pas répondre pour le moment. Réessayez dans un instant.');
        } catch {
            showMessage('La connexion au serveur a été interrompue. Réessayez dans un instant.');
        } finally {
            busy = false;
            button.disabled = false;
            book.classList.remove('is-turning');
            book.removeAttribute('aria-busy');
        }
    });

    window.addEventListener('pageshow', resetBook);
    // L’historique recharge l’adresse réelle : aucun ancien formulaire n’est conservé.
    window.addEventListener('popstate', () => location.reload());
})();
