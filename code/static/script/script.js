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
      article.dataset.reponse = element.reponse;;
      if (element.Check) {
        article.classList.add('valide')
      }
      else if (element.Check === null) {
        article.classList.add('NA')
      } else {
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
    <div class="modal-card ${
  article.classList.contains('valide')
    ? 'valide'
    : article.classList.contains('NA')
      ? 'NA'
      : 'nonValide'
}">
      <button class="modal-close" aria-label="Fermer">×</button>
      <h2> ${article.querySelector('h2').textContent} </h2> 
      <div> ${article.dataset.reponse} </div>
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