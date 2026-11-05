/* Lu avant le premier affichage pour éviter un éclair entre les deux pages. */
(() => {
    try {
        const key = 'litrevu-reader-entry';
        // Le marqueur a été déposé après une connexion réussie.
        const entry = JSON.parse(sessionStorage.getItem(key));
        // On le consomme une seule fois : un rechargement ne rejoue pas le fondu.
        sessionStorage.removeItem(key);
        const age = entry ? Date.now() - entry.time : Infinity;
        if (entry?.path === location.pathname + location.search && age >= 0 && age < 15000
            && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
            document.documentElement.classList.add('reader-arriving');
        }
    } catch { /* Le contenu reste accessible si le stockage est désactivé. */ }
    window.addEventListener('pageshow', (event) => {
        if (event.persisted) document.documentElement.classList.remove('reader-arriving');
    });
})();
