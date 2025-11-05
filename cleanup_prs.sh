#!/bin/bash

# Configuration
repo="Roddygithub/GW2Optimizer"

# 1) Préflight & protections
echo "=== Vérification préalable ==="
gh auth status
git fetch origin --prune
git switch main && git pull --rebase

# 2) Inventaire PRs
echo -e "\n=== Inventaire des PRs ouvertes ==="
gh pr list --repo "$repo" --state open --json number,title,baseRefName,headRefName,isDraft,mergeStateStatus,author,url > .prs_open.json
jq -r '.[] | [.number, .title, .mergeStateStatus, .url] | @tsv' .prs_open.json | column -t -s $'\t' | sed 's/^/- /'

# 3) PR #9 (style/ruff-format-120)
echo -e "\n=== Traitement de la PR #9 ==="
n=9
state=$(gh pr view "$n" --repo "$repo" --json mergeStateStatus -q .mergeStateStatus 2>/dev/null || echo "")
if [ -n "$state" ]; then
  echo "Fermeture de la PR #9 (obsolète)"
  gh pr comment "$n" --repo "$repo" -b "Fermeture car obsolète : le dépôt a été reformaté et cette PR est en conflit. Merci de rouvrir si nécessaire." || true
  gh pr close "$n" --repo "$repo" || true
else
  echo "La PR #9 n'existe plus ou a déjà été fermée"
fi

# 4) Auto-merge des PRs 'CLEAN' avec checks requis verts
echo -e "\n=== Fusion automatique des PRs prêtes ==="
for n in $(jq -r '.[] | select(.baseRefName=="main" and (.isDraft|not)) | .number' .prs_open.json); do
  echo -e "\n→ Vérification PR #$n"
  merge_state=$(gh pr view "$n" --repo "$repo" --json mergeStateStatus -q .mergeStateStatus 2>/dev/null || echo "NOT_FOUND")
  checks_fail=$(gh pr checks "$n" --repo "$repo" 2>/dev/null | grep -E "(fail|cancel|timeout|error)" | wc -l | tr -d ' ')
  
  echo "  État: $merge_state, Échecs de vérification: $checks_fail"
  
  if [ "$merge_state" = "CLEAN" ] && [ "$checks_fail" = "0" ]; then
    echo "  → Fusion en cours..."
    gh pr merge "$n" --repo "$repo" --squash --delete-branch || echo "  ! Échec de la fusion pour #$n"
  else
    echo "  → PR non éligible à la fusion automatique"
    gh pr comment "$n" --repo "$repo" -b "Nettoyage automatisé : PR non fusionnée (état=$merge_state, échecs=$checks_fail). Merci de faire un rebase sur main et de relancer la CI." || true
    gh pr edit "$n" --repo "$repo" --add-label "cleanup:pending" 2>/dev/null || true
  fi
done

# 5) Gestion des dépendances Dependabot
echo -e "\n=== Gestion des dépendances Dependabot ==="
gh pr list --repo "$repo" --search "author:app/dependabot is:open" --json number,title,url,headRefName > .prs_deps.json

# Fusion des dépendances patch/minor sans conflits
for n in $(jq -r '.[] | select(.title | test("bump.*from [0-9]+\.|to [0-9]+\.")) | .number' .prs_deps.json); do
  merge_state=$(gh pr view "$n" --repo "$repo" --json mergeStateStatus -q .mergeStateStatus 2>/dev/null || echo "NOT_FOUND")
  checks_fail=$(gh pr checks "$n" --repo "$repo" 2>/dev/null | grep -E "(fail|cancel|timeout|error)" | wc -l | tr -d ' ')
  
  if [ "$merge_state" = "CLEAN" ] && [ "$checks_fail" = "0" ]; then
    echo "→ Fusion de la dépendance #$n"
    gh pr merge "$n" --repo "$repo" --squash --delete-branch || echo "  ! Échec de la fusion pour #$n"
  else
    echo "→ Marquage de la dépendance #$n pour consolidation"
    gh pr edit "$n" --repo "$repo" --add-label "deps:rollup" 2>/dev/null || true
    gh pr comment "$n" --repo "$repo" -b "Sera inclus dans une PR de consolidation des dépendances (conflits ou vérifications en échec)." || true
  fi
done

# Création d'une branche de consolidation si nécessaire
if [ -s .prs_deps.json ] && [ "$(jq 'length' .prs_deps.json)" -gt 0 ]; then
  rollup_branch="deps/rollup-$(date +%Y%m%d)"
  echo -e "\n→ Création de la branche de consolidation: $rollup_branch"
  
  git switch -c "$rollup_branch" main
  
  # Mise à jour des dépendances (à adapter selon votre gestionnaire de paquets)
  if [ -f "requirements.txt" ]; then
    echo "Mise à jour des dépendances Python..."
    pip install -U pip
    pip install -r requirements.txt
    pip freeze > requirements.txt
  fi
  
  if [ -f "package.json" ]; then
    echo "Mise à jour des dépendances Node.js..."
    npm update
  fi
  
  # Commit et push des mises à jour
  git add .
  if ! git diff --cached --quiet; then
    git commit -m "chore(deps): consolidation des mises à jour"
    git push -u origin "$rollup_branch"
    
    # Création de la PR de consolidation
    gh pr create --repo "$repo" \
      -t "chore(deps): consolidation des dépendances $(date +%Y-%m-%d)" \
      -b "Regroupement des mises à jour de dépendances qui ne pouvaient pas être fusionnées automatiquement." \
      --base main \
      --head "$rollup_branch"
  else
    echo "Aucune mise à jour de dépendances nécessaire."
    git switch main
    git branch -D "$rollup_branch"
  fi
fi

# 6) Création du rapport
echo -e "\n=== Création du rapport ==="
body=$(cat <<'EOF'
# Rapport de nettoyage des PRs et dépendances

## Actions effectuées
- Fermeture des PRs obsolètes (ex: #9)
- Fusion automatique des PRs prêtes (CLEAN + vérifications OK)
- Marquage des PRs nécessitant une attention particulière (label: cleanup:pending)
- Consolidation des mises à jour de dépendances Dependabot

## Prochaines étapes
1. Activer l'option "Supprimer automatiquement les branches de fonctionnalités" dans les paramètres du dépôt
2. Vérifier les règles de protection des branches
3. Examiner les PRs marquées "cleanup:pending" pour résolution manuelle

## Détails
Consultez le journal d'exécution pour plus de détails sur les actions effectuées.
EOF
)

echo "Création de l'issue de rapport..."
gh issue create --repo "$repo" \
  -t "Rapport de nettoyage - $(date +%Y-%m-%d)" \
  -b "$body" \
  -l "cleanup,report"

echo -e "\n=== Nettoyage terminé ==="
echo "Consultez les rapports ci-dessus pour les détails des actions effectuées."
