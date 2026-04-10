console.log("indexscript.js charge");

const form = document.querySelector('form');
const choicePanel = document.getElementById('analysis-choice-panel');
const workspace = document.getElementById('analysis-workspace');
const modeLabel = document.getElementById('analysis-mode-label');
const modeTitle = document.getElementById('analysis-mode-title');
const modeDescription = document.getElementById('analysis-mode-description');
const backToChoiceButton = document.getElementById('back-to-choice');
const choiceButtons = document.querySelectorAll('[data-analysis-mode]');

function openWorkspace(button) {
    if (!workspace || !choicePanel || !button) return;

    const title = button.dataset.analysisTitle || 'Deposez vos documents';
    const description = button.dataset.analysisDescription || "Ajoutez les pieces de votre projet, puis lancez l'analyse.";
    const mode = button.dataset.analysisMode || 'analyse';

    if (modeLabel) {
        modeLabel.textContent = mode === 'module' ? "Creation d'un module" : 'Nouvelle analyse';
    }
    if (modeTitle) {
        modeTitle.textContent = title;
    }
    if (modeDescription) {
        modeDescription.textContent = description;
    }

    choicePanel.classList.add('hidden');
    workspace.classList.remove('hidden');
    workspace.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function closeWorkspace() {
    if (!workspace || !choicePanel) return;
    workspace.classList.add('hidden');
    choicePanel.classList.remove('hidden');
    choicePanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

choiceButtons.forEach((button) => {
    button.addEventListener('click', () => openWorkspace(button));
});

if (backToChoiceButton) {
    backToChoiceButton.addEventListener('click', closeWorkspace);
}

if (!form) {
    console.error("Formulaire introuvable");
} else {
    const loadingContainer = document.getElementById('loading-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const submitButton = form.querySelector('input[type="submit"]');

    let isSubmitting = false;
    let keepPolling = false;

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

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

            await sleep(delayMs);
        }
    }

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        if (isSubmitting) return;
        isSubmitting = true;

        const formData = new FormData(form);

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

        pollProgress(10000);

        fetch('/', {
            method: 'POST',
            body: formData
        })
        .then(r => r.text())
        .then(html => {
            keepPolling = false;
            if (progressBar) {
                progressBar.style.width = '100%';
            }

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
