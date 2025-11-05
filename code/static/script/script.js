async function loadReponse() {

    try {
        const res = await fetch('/give_json')
        const data = await res.json()

        const sectionQuestion = document.getElementById('questionContainer')
        data.forEach(element => {
            let article = document.createElement('article')
            article.innerHTML = `
        <h2>${element.question}</h2>
        <div>${element.reponse}</div>
        `;
        if(element.Check)
        {
            article.classList.add('valide')
        }
        else{
            article.classList.add('nonValide')
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
    <div class="modal-card ${article.classList.contains('valide') ? 'valide' : 'nonValide'}">
      <button class="modal-close" aria-label="Fermer">×</button>
      ${article.innerHTML}
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