console.log("indexscript.js chargé ✅");

const form = document.querySelector('form');
if (!form) {
    console.error("Formulaire introuvable !");
} else {
    const loadingContainer = document.getElementById('loading-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const submitButton = form.querySelector('input[type="submit"]');

    let progressInterval = null;
    let isSubmitting = false;

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

        // ➜ début du polling /progress
        progressInterval = setInterval(async () => {
            try {
                const res = await fetch('/progress');
                if (!res.ok) return;

                const data = await res.json();
                const current = data.current ?? 0;
                const total = data.total ?? 0;

                if (total > 0 && progressBar && progressText) {
                    const percent = Math.round((current / total) * 100);
                    progressBar.style.width = percent + '%';
                    progressText.textContent = `(${current} / ${total})`;
                }
            } catch (err) {
                console.error("Erreur polling /progress :", err);
            }
        }, 500);

        // ➜ envoi réel du formulaire
        fetch('/', {
            method: 'POST',
            body: formData
        })
        .then(r => r.text())
        .then(html => {
            clearInterval(progressInterval);
            if (progressBar) {
                progressBar.style.width = '100%';
            }

            // on affiche resultat.html renvoyé par Flask
            document.open();
            document.write(html);
            document.close();
        })
        .catch(err => {
            clearInterval(progressInterval);
            console.error("Erreur lors de l'analyse :", err);
            alert("Erreur lors de l'analyse.");
            isSubmitting = false;
            if (submitButton) {
                submitButton.disabled = false;
            }
        });
    });
}
