/* Amélioration facultative : sans JavaScript, les mots de passe restent masqués. */
(() => {
    // Les boutons ne deviennent visibles que si JavaScript fonctionne.
    function prepareButtons() {
        document.querySelectorAll('.password-toggle').forEach((button) => {
            button.hidden = false;
            button.closest('.password-control').classList.add('has-toggle');
        });
    }

    function hidePasswords() {
        document.querySelectorAll('.password-control').forEach((control) => {
            const input = control.querySelector('input');
            const button = control.querySelector('.password-toggle');
            const label = input.labels?.[0]?.textContent.replace(/\s*:\s*$/, '') || '';
            input.type = 'password';
            button.textContent = 'Afficher';
            button.setAttribute('aria-label', `Afficher le mot de passe — ${label}`);
        });
    }

    document.addEventListener('click', (event) => {
        const button = event.target.closest('.password-toggle');
        if (!button) return;
        const input = document.getElementById(button.getAttribute('aria-controls'));
        // Changer le type modifie l’affichage, pas le stockage du mot de passe.
        const reveal = input.type === 'password';
        input.type = reveal ? 'text' : 'password';
        const action = reveal ? 'Masquer' : 'Afficher';
        const label = input.labels?.[0]?.textContent.replace(/\s*:\s*$/, '') || '';
        button.textContent = action;
        button.setAttribute('aria-label', `${action} le mot de passe — ${label}`);
    });

    // Remasquer avant l’envoi et lors d’un retour dans l’historique du navigateur.
    document.addEventListener('submit', hidePasswords, true);
    window.addEventListener('pageshow', hidePasswords);
    document.addEventListener('account-form-updated', prepareButtons);
    prepareButtons();
})();
