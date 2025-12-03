console.log("indexscript.js chargé ✅");

const form = document.querySelector('form');
if (!form) {
    console.error("Formulaire introuvable !");
} else {
    const loadingContainer = document.getElementById('loading-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const submitButton = form.querySelector('input[type="submit"]');

    let isSubmitting = false;
    let keepPolling = false;

    // Petite fonction utilitaire pour le délai
    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Fonction de polling avec délai entre chaque requête
    async function pollProgress(delayMs = 500) {
        keepPolling = true;

        while (keepPolling) {
            try {
                const res = await fetch('/progress');
                if (res.ok) {
                    const data = await res.json();
                    const current = data.current ?? 0;
                    const total = data.total ?? 0;

                    if (total > 0 && progressBar && progressText) {
                        const percent = Math.round((current / total) * 100);
                        progressBar.style.width = percent + '%';
                        progressText.textContent = `(${current} / ${total})`;
                    }
                }
            } catch (err) {
                console.error("Erreur polling /progress :", err);
            }

            // 👉 délai entre chaque requête
            await sleep(delayMs);
        }
    }

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        if (isSubmitting) return;
        isSubmitting = true;

        const formData = new FormData(form);

        // ➜ afficher la barre seulement quand on clique sur "Analyser"
        if (loadingContainer) {
            loadingContainer.style.display = 'block';
        }
        if (progressBar) {
            progressBar.style.width = '0%';
        }
        if (progressText) {
            progressText.textContent = '(0 / 0)';
        }
        if (submitButton) {
            submitButton.disabled = true;
        }

        // ➜ lancement du polling avec délai entre chaque requête
        pollProgress(10000); // <-- ajuste ici (en ms) la pause entre les requêtes

        // ➜ envoi réel du formulaire
        fetch('/', {
            method: 'POST',
            body: formData
        })
        .then(r => r.text())
        .then(html => {
            keepPolling = false;         // on arrête le polling
            if (progressBar) {
                progressBar.style.width = '100%';
            }

            // on affiche resultat.html renvoyé par Flask
            document.open();
            document.write(html);
            document.close();
        })
        .catch(err => {
            keepPolling = false;
            console.error("Erreur lors de l'analyse :", err);
            alert("Erreur lors de l'analyse.");
            isSubmitting = false;
            if (submitButton) {
                submitButton.disabled = false;
            }
        });
    });
}
