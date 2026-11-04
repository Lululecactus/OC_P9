/* Django vérifie les identifiants. JavaScript ajoute seulement le passage de page. */
(() => {
    const book = document.querySelector('.account-layout');
    const panel = document.querySelector('.account-panel');
    const content = document.querySelector('.account-content');
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (!book || !panel || !content || !window.fetch || !panel.animate) return;

    let busy = false;

    function showMessage(message) {
        content.querySelector('.login-status').textContent = message;
    }

    let turningSheet;
    let exitVeil;

    function resetBook() {
        turningSheet?.remove();
        exitVeil?.remove();
        panel.style.visibility = '';
        book.classList.remove('is-turning');
    }

    function makeFlexibleSheet() {
        const width = panel.offsetWidth;
        const height = panel.offsetHeight;
        const count = 24;
        const stripWidth = width / count;
        const sheet = document.createElement('div');
        sheet.className = 'turning-sheet';
        sheet.setAttribute('aria-hidden', 'true');
        sheet.inert = true;
        Object.assign(sheet.style, {
            left: `${panel.offsetLeft}px`, top: `${panel.offsetTop}px`,
            width: `${width}px`, height: `${height}px`,
        });
        const strips = [];

        // Chaque bande montre une petite tranche du même formulaire.
        // Elles restent jointes mais peuvent prendre des angles différents.
        for (let index = 0; index < count; index++) {
            const strip = document.createElement('div');
            strip.className = 'paper-strip';
            // Un petit recouvrement évite les filets clairs dus à l’anticrénelage.
            strip.style.width = `${stripWidth + 1.5}px`;
            const front = document.createElement('div');
            front.className = 'paper-front';
            const copy = panel.cloneNode(true);
            copy.classList.add('paper-copy');
            copy.removeAttribute('aria-labelledby');
            copy.querySelectorAll('[id]').forEach((element) => element.removeAttribute('id'));
            copy.querySelectorAll('input').forEach((input) => {
                input.removeAttribute('name');
                input.removeAttribute('autofocus');
                // Aucune copie du mot de passe ou du jeton CSRF dans le décor.
                if (input.type === 'password') input.value = '••••••••';
                if (input.type === 'hidden') input.value = '';
            });
            Object.assign(copy.style, {
                width: `${width}px`, height: `${height}px`, left: `${-index * stripWidth}px`,
            });
            front.append(copy);
            const back = document.createElement('div');
            back.className = 'paper-back';
            strip.append(front, back);
            sheet.append(strip);
            strips.push(strip);
        }
        book.append(sheet);
        turningSheet = sheet;
        panel.style.visibility = 'hidden';
        return { strips, stripWidth };
    }

    async function turnPage() {
        if (reducedMotion.matches) return;
        const mobile = window.matchMedia('(max-width: 720px)').matches;
        book.classList.add('is-turning');
        const { strips, stripWidth } = makeFlexibleSheet();
        const duration = mobile ? 1050 : 1450;

        await new Promise((resolve) => {
            const start = performance.now();
            function frame(now) {
                const elapsed = Math.min((now - start) / duration, 1);
                if (reducedMotion.matches) { resolve(); return; }
                // Démarrage et arrivée progressifs. Le bord libre devance la reliure.
                const progress = elapsed * elapsed * (3 - 2 * elapsed);
                const bend = Math.sin(progress * Math.PI) * 1.15;
                let x = 0;
                let z = 0;
                strips.forEach((strip, index) => {
                    const position = (index + .5) / strips.length;
                    const angle = -Math.PI * progress + bend * (1 - 2 * position);
                    strip.style.transform = `translate3d(${x}px, 0, ${z}px) rotateY(${angle}rad)`;
                    // La lumière suit la courbe du papier, sans une ombre par bande.
                    strip.style.setProperty('--paper-shade', .13 * Math.abs(Math.sin(angle)));
                    x += stripWidth * Math.cos(angle);
                    z -= stripWidth * Math.sin(angle);
                });
                if (elapsed < 1) requestAnimationFrame(frame);
                else resolve();
            }
            requestAnimationFrame(frame);
        });
    }

    async function fadeToReader(destination) {
        if (reducedMotion.matches) return;
        // Un repère éphémère permet au document suivant de reprendre le même fondu.
        // Il ne contient que l’adresse et l’heure, jamais les identifiants.
        try {
            sessionStorage.setItem('litrevu-reader-entry', JSON.stringify({
                path: destination.pathname + destination.search, time: Date.now(),
            }));
        } catch { return; }
        exitVeil = document.createElement('div');
        exitVeil.className = 'reader-transition-veil';
        exitVeil.setAttribute('aria-hidden', 'true');
        document.body.append(exitVeil);
        await exitVeil.animate([{ opacity: 0 }, { opacity: 1 }], {
            duration: 380, easing: 'ease-in-out', fill: 'forwards',
        }).finished;
    }

    // La délégation conserve le comportement même après l’affichage d’une erreur.
    content.addEventListener('submit', async (event) => {
        const form = event.target;
        if (!form.matches('[data-book-login]') || reducedMotion.matches) return;
        event.preventDefault();
        if (busy) return;
        busy = true;
        const button = form.querySelector('button[type="submit"]');
        button.disabled = true;
        form.setAttribute('aria-busy', 'true');
        showMessage('Vérification de vos identifiants…');

        try {
            // Le formulaire conserve son jeton CSRF et la redirection « next ».
            const response = await fetch(form.action, {
                method: 'POST', body: new FormData(form), credentials: 'same-origin',
            });

            if (response.ok && response.redirected) {
                const destination = new URL(response.url);
                if (destination.origin !== window.location.origin) {
                    throw new Error('Destination inattendue.');
                }
                showMessage('Connexion réussie. Ouverture de votre espace…');
                // Un souci d’animation ne doit jamais empêcher une connexion réussie.
                try {
                    await turnPage();
                    await fadeToReader(destination);
                } catch { /* La navigation reste prioritaire. */ }
                window.location.assign(destination.href);
                return;
            }

            if (response.ok) {
                const page = new DOMParser().parseFromString(await response.text(), 'text/html');
                const updatedContent = page.querySelector('.account-content');
                if (updatedContent?.querySelector('[data-book-login]')) {
                    content.replaceChildren(...updatedContent.childNodes);
                    const error = content.querySelector('.errorlist');
                    if (error) {
                        error.tabIndex = -1;
                        error.focus();
                    }
                    return;
                }
            }
            showMessage(response.status === 403
                ? 'Le formulaire a expiré. Rechargez la page avant de réessayer.'
                : 'Le serveur ne peut pas répondre pour le moment. Réessayez dans un instant.');
        } catch {
            showMessage('La connexion au serveur a été interrompue. Vous pouvez réessayer.');
        } finally {
            busy = false;
            button.disabled = false;
            form.removeAttribute('aria-busy');
        }
    });

    // Le bouton Retour du navigateur ne doit pas retrouver une page déjà tournée.
    window.addEventListener('pageshow', resetBook);
})();
