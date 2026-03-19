// Mapping couleur par source
const sourceColors = {
  'F1': '#FF6B6B',
  'FIC': '#4ECDC4',
  'outilsRecrutement': '#FFE66D',
  'financement': '#95E1D3',
  'rechercheMilieu': '#C7B3E5',
  'questionnaires': '#F38181',
  'guideEntrevue': '#AA96DA',
  'guideDiscussions': '#FCBAD3',
  'guideObservation': '#A8DADC',
  'instrumentsMesure': '#F4A261',
  'autorisationDonneesSecondaires': '#2A9D8F',
  'descriptionCollecte': '#E76F51',
  'preuveCGRB': '#264653',
  'N/A': '#B0B0B0',
  '': '#B0B0B0'
};

function getSourceColor(source) {
  return sourceColors[source] || '#999999';
}

async function loadReponse() {

  try {
    const res = await fetch('/give_json')
    const data = await res.json()

    const sectionQuestion = document.getElementById('questionContainer')
    data.forEach(element => {
      let article = document.createElement('article')
      const source = element.reponse.Source || '';
      const sourceColor = getSourceColor(source);
      
      article.innerHTML = ` 
        <h2>${element.question}</h2> 
        <span class="source-badge" style="background-color: ${sourceColor}">${source || 'N/A'}</span>
      ` // Affiche la source avec couleur
      article.dataset.justification = element.reponse.Justification;
      article.dataset.recommandation = element.reponse.Recommandation;
      article.dataset.source = source;

      if (element.reponse.Reponse) {
        article.classList.add('valide')
        article.dataset.validation = "Oui"
        article.dataset.recommandation = ''
      }
      else if (element.reponse.Reponse === null) {
        article.classList.add('NA')
        article.dataset.validation = "Ne s'applique pas"
        article.dataset.recommandation = ''

      } else {
        article.classList.add('nonValide')
        article.dataset.validation = "Non"
        article.dataset.recommandation = `<h3>Recommandation</h3>
      ${element.reponse.Recommandation} `
      }
      article.addEventListener('click', () => openOverlay(article))
      sectionQuestion.appendChild(article)
    });


  }
  catch (err) {
    console.log(err)
  }
}

function openOverlay(article) {
  const sourceColor = getSourceColor(article.dataset.source);
  
  // Contenu "propre" pour la modale (copie du HTML de l'article)
  const content = `
    <div class="modal-card ${article.classList.contains('valide')
      ? 'valide'
      : article.classList.contains('NA')
        ? 'NA'
        : 'nonValide'
    }">
      <button class="modal-close" aria-label="Fermer">×</button>
      <h2> ${article.querySelector('h2').textContent} </h2> 
      <div class="source-info">
        <span class="source-badge" style="background-color: ${sourceColor}">Source: ${article.dataset.source || 'N/A'}</span>
      </div>
      <div> 
      <p id='validation'>${article.dataset.validation}</p>
      <h3>Justification (avec citation)</h3>
       <div class="justification-box">
         ${article.dataset.justification}
       </div>
      ${article.dataset.recommandation}
      </div>

      <div class="thumbs-section">
        <h3>Pensez-vous que cette réponse est correcte ?</h3>
        <div class="thumbs-buttons">
          <button class="btn-thumb btn-thumb-up" onclick="submitThumbsVote(event, '${article.querySelector('h2').textContent.replace(/'/g, "\\'")}', 'up')">👍 Correct</button>
          <button class="btn-thumb btn-thumb-down" onclick="submitThumbsVote(event, '${article.querySelector('h2').textContent.replace(/'/g, "\\'")}', 'down')">👎 Incorrect</button>
        </div>
      </div>
    </div>
  `;

  const overlay = document.createElement('div');
  overlay.className = 'overlay';
  overlay.innerHTML = content;

  // Fermeture : bouton X ou clic en dehors
  overlay.addEventListener('click', (e) => {
    const isBackdrop = e.target.classList.contains('overlay');
    const isCloseBtn = e.target.classList.contains('modal-close');
    if (isBackdrop || isCloseBtn) overlay.remove();
  });

  document.body.appendChild(overlay);
}


async function submitThumbsVote(event, question, vote) {
  event.preventDefault();
  
  try {
    const res = await fetch('/save_thumbs_vote', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        question: question,
        vote: vote,
        timestamp: new Date().toISOString()
      })
    });
    
    const result = await res.json();
    
    if (result.success) {
      alert('Merci pour votre évaluation !');
      // Désactiver les boutons après vote
      const buttons = document.querySelectorAll('.btn-thumb');
      buttons.forEach(btn => btn.disabled = true);
    } else {
      alert('Erreur lors de l\'enregistrement: ' + result.message);
    }
  } catch (err) {
    console.error('Erreur:', err);
    alert('Erreur lors de l\'enregistrement du vote');
  }
}

document.addEventListener('DOMContentLoaded', loadReponse);
