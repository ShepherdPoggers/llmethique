async function loadReponse() {

  try {
    const res = await fetch('/give_json')
    const data = await res.json()

    const sectionQuestion = document.getElementById('questionContainer')
    data.forEach(element => {
      let article = document.createElement('article')
      article.innerHTML = `
        <h2>${element.question}</h2>
        `
      article.dataset.justification = element.reponse.Justification;
      article.dataset.recommandation = element.reponse.Recommandation;

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
  // Contenu “propre” pour la modale (copie du HTML de l’article)
  const content = `
    <div class="modal-card ${article.classList.contains('valide')
      ? 'valide'
      : article.classList.contains('NA')
        ? 'NA'
        : 'nonValide'
    }">
      <button class="modal-close" aria-label="Fermer">×</button>
      <h2> ${article.querySelector('h2').textContent} </h2> 
      <div> 
      ${article.dataset.validation}
      <h3>Justification</h3>
       ${article.dataset.justification}
      ${article.dataset.recommandation}
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
document.addEventListener('DOMContentLoaded', loadReponse);