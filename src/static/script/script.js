const sourceColors = {
  F1: '#d9485f',
  FIC: '#2f9e99',
  outilsRecrutement: '#c08a00',
  financement: '#6c91bf',
  rechercheMilieu: '#7a63b8',
  questionnaires: '#d17d6f',
  guideEntrevue: '#7b6fd6',
  guideDiscussions: '#db7aa8',
  guideObservation: '#3f8f9c',
  instrumentsMesure: '#d17f36',
  autorisationDonneesSecondaires: '#257a74',
  descriptionCollecte: '#bf5e46',
  preuveCGRB: '#35505b',
  'N/A': '#8c8c8c',
  '': '#8c8c8c'
};

function getSourceColor(source) {
  return sourceColors[source] || '#7d7d7d';
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function escapeJsString(value) {
  return String(value ?? '')
    .replace(/\\/g, '\\\\')
    .replace(/'/g, "\\'")
    .replace(/\n/g, ' ')
    .replace(/\r/g, ' ');
}

function statusConfig(value) {
  if (value === true) {
    return { className: 'valide', label: 'Conforme', preview: 'La reponse indique que le dossier satisfait a cette exigence.' };
  }
  if (value === null) {
    return { className: 'NA', label: 'Non applicable', preview: "La question ne s'applique pas au dossier selon les documents fournis." };
  }
  return { className: 'nonValide', label: 'A corriger', preview: "La reponse indique qu'une correction ou une precision est necessaire." };
}

function isSystemMessage(text) {
  const normalized = String(text || '').toLowerCase();
  return normalized.includes('aucun json') ||
    normalized.includes('erreur groq') ||
    normalized.includes("une erreur est survenu") ||
    normalized.includes("aucune justification exploitable");
}

function updateSummary(data) {
  const total = data.length;
  const valid = data.filter(item => item.reponse.Reponse === true).length;
  const invalid = data.filter(item => item.reponse.Reponse === false).length;
  const notApplicable = data.filter(item => item.reponse.Reponse === null).length;

  const totalNode = document.getElementById('summary-total');
  const validNode = document.getElementById('summary-valid');
  const invalidNode = document.getElementById('summary-invalid');
  const naNode = document.getElementById('summary-na');

  if (totalNode) totalNode.textContent = total;
  if (validNode) validNode.textContent = valid;
  if (invalidNode) invalidNode.textContent = invalid;
  if (naNode) naNode.textContent = notApplicable;
}

async function loadReponse() {
  try {
    const res = await fetch('/give_json');
    const data = await res.json();

    updateSummary(data);

    const sectionQuestion = document.getElementById('questionContainer');
    data.forEach((element) => {
      const article = document.createElement('article');
      const source = element.reponse.Source || 'N/A';
      const sourceColor = getSourceColor(source);
      const status = statusConfig(element.reponse.Reponse);
      const justification = element.reponse.Justification || 'Aucune justification fournie.';
      const systemMessage = isSystemMessage(justification);

      article.classList.add(status.className);
      article.dataset.justification = justification;
      article.dataset.recommandation = element.reponse.Recommandation || '';
      article.dataset.source = source;
      article.dataset.validation = status.label;
      article.dataset.question = element.question;

      article.innerHTML = `
        <div class="result-topline">
          <span class="status-pill ${status.className}">${status.label}</span>
          <span class="source-badge" style="background-color: ${sourceColor}">${escapeHtml(source)}</span>
        </div>
        <h2>${escapeHtml(element.question)}</h2>
        <div class="article-preview ${systemMessage ? 'is-system-message' : ''}">
          ${systemMessage ? '<span class="system-note">Attention systeme</span>' : ''}
          <p>${escapeHtml(justification)}</p>
        </div>
        <div class="article-footer">
          <span class="article-link">Voir le detail</span>
        </div>
      `;

      article.addEventListener('click', () => openOverlay(article));
      sectionQuestion.appendChild(article);
    });
  } catch (err) {
    console.error(err);
  }
}

function openOverlay(article) {
  const sourceColor = getSourceColor(article.dataset.source);
  const systemMessage = isSystemMessage(article.dataset.justification);
  const recommendation = article.dataset.recommandation
    ? `
      <section class="modal-section">
        <h3>Recommandation</h3>
        <div class="content-box">
          <p>${escapeHtml(article.dataset.recommandation)}</p>
        </div>
      </section>
    `
    : '';

  const overlay = document.createElement('div');
  overlay.className = 'overlay';
  overlay.innerHTML = `
    <div class="modal-card ${article.classList.contains('valide')
      ? 'valide'
      : article.classList.contains('NA')
        ? 'NA'
        : 'nonValide'
    }">
      <button class="modal-close" aria-label="Fermer">&times;</button>
      <header class="modal-header">
        <h2>${escapeHtml(article.dataset.question)}</h2>
        <div class="modal-meta">
          <span class="status-pill ${article.classList.contains('valide')
            ? 'valide'
            : article.classList.contains('NA')
              ? 'NA'
              : 'nonValide'
          }">${escapeHtml(article.dataset.validation)}</span>
          <span class="source-badge" style="background-color: ${sourceColor}">${escapeHtml(article.dataset.source || 'N/A')}</span>
        </div>
      </header>

      <section class="modal-section">
        <h3>Justification</h3>
        <div class="content-box ${systemMessage ? 'is-system-message' : ''}">
          ${systemMessage ? '<span class="system-note">Attention systeme</span>' : ''}
          <p>${escapeHtml(article.dataset.justification)}</p>
        </div>
      </section>

      ${recommendation}

      <div class="thumbs-section">
        <h3>Pensez-vous que cette reponse est correcte ?</h3>
        <div class="thumbs-buttons">
          <button class="btn-thumb btn-thumb-up" onclick="submitThumbsVote(event, '${escapeJsString(article.dataset.question)}', 'up')">Correcte</button>
          <button class="btn-thumb btn-thumb-down" onclick="submitThumbsVote(event, '${escapeJsString(article.dataset.question)}', 'down')">Incorrecte</button>
        </div>
      </div>
    </div>
  `;

  overlay.addEventListener('click', (e) => {
    const isBackdrop = e.target.classList.contains('overlay');
    const isCloseBtn = e.target.classList.contains('modal-close');
    if (isBackdrop || isCloseBtn) {
      overlay.remove();
      document.body.classList.remove('modal-open');
    }
  });

  document.body.classList.add('modal-open');
  document.body.appendChild(overlay);
}

async function submitThumbsVote(event, question, vote) {
  event.preventDefault();

  try {
    const overlay = document.querySelector('.overlay');
    const validation = overlay?.querySelector('.status-pill')?.textContent?.trim() || '';
    const source = overlay?.querySelector('.source-badge')?.textContent?.trim() || '';

    const res = await fetch('/save_thumbs_vote_db', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        question,
        vote,
        validation,
        source,
        timestamp: new Date().toISOString()
      })
    });

    const result = await res.json();

    if (result.success) {
      alert('Merci pour votre evaluation.');
      const buttons = document.querySelectorAll('.btn-thumb');
      buttons.forEach((btn) => {
        btn.disabled = true;
      });
    } else {
      alert(`Erreur lors de l'enregistrement : ${result.message}`);
    }
  } catch (err) {
    console.error('Erreur:', err);
    alert("Erreur lors de l'enregistrement du vote.");
  }
}

document.addEventListener('DOMContentLoaded', loadReponse);
