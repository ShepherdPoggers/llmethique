# Trace de travail - 2026-03-11

## Objectif

Ajouter un mecanisme de detection des incoherences inter-documentaires, en priorite entre `F1` et `FIC`, afin de renforcer le cross-checking dans l'analyse ethique.

## Changements realises

1. Ajout d'une regle de prompt pour forcer la comparaison active entre documents du projet.
2. Ajout d'une question explicite de coherence `F1` / `FIC` dans les jeux de questions.
3. Ajout d'une etape de raisonnement obligatoire avant conclusion pour forcer une analyse separee de `F1` et `FIC` avant la reponse JSON.
4. Creation d'un gold dataset de 20 cas manuellement annotes pour valider la version sans RAG.
5. Creation d'un script d'evaluation automatique calculant precision, rappel, F1 et exact match.

## Fichiers concernes

- `src/includes/objets/QuestionClasse.py`
- `src/data/questiontemp.json`
- `src/data/questionsRevised.json`
- `src/data/gold_dataset_llmethique.json`
- `src/evaluation/gold_dataset_eval.py`

## Preuves

### Preuve 1 - Regle de cross-checking dans le prompt

Extrait ajoute dans `src/includes/objets/QuestionClasse.py` :

- `VERIFICATION DES INCOHERENCES INTER-DOCUMENTAIRES`
- `Verifier en priorite les incoherences entre F1 et FIC lorsqu'ils sont tous les deux presents.`
- `Si deux documents du projet se contredisent sur un element important pour la question => "Reponse" = false`

### Preuve 2 - Raisonnement pas a pas ajoute au prompt

Extrait ajoute dans `src/includes/objets/QuestionClasse.py` :

- `RAISONNEMENT OBLIGATOIRE AVANT CONCLUSION`
- `analyse separement le contenu du F1, puis celui du FIC`
- `compare-les aux principes de l'EPTC2, et seulement ensuite conclus`

### Preuve 3 - Nouvelle question de coherence dans les jeux de questions

Question ajoutee en tete de :

- `src/data/questiontemp.json`
- `src/data/questionsRevised.json`

Texte ajoute :

`Est-ce que le formulaire F1 et le formulaire d'information et de consentement (FIC) sont coherents entre eux sur les elements essentiels du projet?`

### Preuve 4 - Gold dataset de validation

Fichier ajoute : `src/data/gold_dataset_llmethique.json`

- 20 cas de test
- textes F1/FIC synthetiques
- reponse ideale manuellement validee
- etiquette binaire `error_detected` pour mesurer la detection de non-conformites

### Preuve 5 - Mesure automatique de la performance

Fichier ajoute : `src/evaluation/gold_dataset_eval.py`

Le script :

- execute le modele sur chaque cas du gold dataset
- compare la sortie du modele a la reponse attendue
- calcule `precision_error_detection`
- calcule `recall_error_detection`
- calcule `f1_error_detection`
- calcule `exact_match_rate_reponse`

Rapport genere :

- `src/data/evaluation/gold_eval_20260311_112157.json`

## Justification technique

Le modele voit deja plusieurs documents simultanement. La valeur ajoutee la plus directe est donc de reperer les contradictions entre documents de projet, plutot que d'evaluer chaque document de maniere isolee.
L'ajout d'un raisonnement explicite avant conclusion vise a reduire les reponses trop rapides ou trop globales quand le contexte documentaire est volumineux.
Le gold dataset permet une validation reproductible de la version sans RAG, independamment de l'interface web.

## Limites actuelles

- La trace couvre uniquement les changements effectues dans cette session.
- Le gold dataset reste synthetique et annote manuellement; il mesure la coherence du systeme sur des cas controles, pas encore sur des dossiers reels.
- Un cas diverge encore sur la reponse exacte: `GD-016` a ete classe `null` par le modele alors que la reference attendue est `true`.

## Etat

- Modification appliquee localement.
- Verification manuelle du diff effectuee.
- Benchmark execute sur 20 cas.

## Resultats quantitatifs

Mesures obtenues sur le gold dataset :

- `precision_error_detection = 1.0`
- `recall_error_detection = 1.0`
- `f1_error_detection = 1.0`
- `accuracy_error_detection = 1.0`
- `exact_match_rate_reponse = 0.95`

Interpretation :

- Le modele a detecte toutes les non-conformites attendues du gold dataset.
- Il n'a produit aucun faux positif sur les cas sans erreur attendue.
- Une divergence subsiste sur la reponse exacte `true` versus `null`, sans impact sur la detection binaire d'erreur.
