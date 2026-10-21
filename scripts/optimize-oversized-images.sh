#!/usr/bin/env bash
# Optimize oversized featured PNGs / avatars.
# - Backs up each original PNG (WebP not backed up) under backups/image-optimize-<ts>/
# - Resizes to max width, compresses with pngquant toward a size budget
# - Regenerates sibling .webp (best-effort; not required for rollback)
#
# Usage:
#   ./scripts/optimize-oversized-images.sh          # run
#   ./scripts/optimize-oversized-images.sh --dry-run
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
fi

for cmd in magick pngquant cwebp; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "ERROR: missing required tool: $cmd" >&2
    exit 1
  fi
done

TS="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$ROOT/backups/image-optimize-${TS}"

# path|max_width|target_kb|note
# max_width 0 = do not resize (only compress)
TARGETS=(
  # Featured PNGs > 1 MB
  "content/OpenShift-Platform/Security/Secrets-Management/OpenBao/images/logos/part10_openbao_logo.png|1200|300|OpenBao Part 10"
  "content/GitOpsCollection/images/agent/Logo-ArgoCDAgent.png|1200|300|Argo CD Agent"
  "content/OpenShift-Platform/Security/Secrets-Management/OpenBao/images/logos/part7_openbao_logo.png|1200|300|OpenBao Part 7"
  "content/GitOpsCollection/images/logos/ep-16-gitops.png|1200|300|Ep.16"
  "content/OpenShift-Platform/Security/Secrets-Management/OpenBao/images/logos/part5_openbao_logo.png|1200|300|OpenBao Part 5"
  "content/OpenShift-Platform/Security/Secrets-Management/OpenBao/images/logos/part6_openbao_logo.png|1200|300|OpenBao Part 6"
  "content/OpenShift-Platform/Security/Secrets-Management/OpenBao/images/logos/part3_openbao_logo.png|1200|300|OpenBao Part 3"
  "content/Other/images/homelab/cat_laboratory.png|1200|300|cat_laboratory (featured)"
  "content/OpenShift-Platform/Security/Secrets-Management/OpenBao/images/logos/part4_openbao_logo.png|1200|300|OpenBao Part 4"
  "content/OpenShift-Platform/Security/Secrets-Management/OpenBao/images/logos/part1_openbao_logo.png|1200|300|OpenBao Part 1"
  # Featured 300 KB–1 MB
  "content/Other/images/homelab/homelab_logo.png|1200|300|HomeLab logo"
  "content/OpenShift-Platform/Virtualization/images/network-overview/Logo_VirtualizationNetworking.png|1200|300|Virt networking logo"
  "content/OpenShift-Platform/Security/Compliance/logos/compliance-operator-customrules-cel-logo.png|1200|300|CEL custom rules"
  "content/OpenShift-Platform/Security/Secrets-Management/OpenBao/images/logos/part8_openbao_logo.png|1200|300|OpenBao Part 8"
  "content/OpenShift-Platform/Security/Secrets-Management/OpenBao/images/logos/part9_openbao_logo.png|1200|300|OpenBao Part 9"
  "content/suse/images/logos/opensuse_cloud_init.png|1200|300|openSUSE cloud-init"
  "content/OpenShift-Platform/Observability/images/observability/Logo_observability_1.png|416|80|Observability logo 1"
  "content/OpenShift-Platform/Observability/images/observability/Logo_observability_2.png|416|80|Observability logo 2"
  "content/OpenShift-Platform/Observability/images/observability/Logo_observability_7.png|416|80|Observability logo 7"
  "content/OpenShift-Platform/Observability/images/observability/Logo_OTEL.png|416|80|OTEL logo"
  # Extra large non-featured logos often on cards / related
  "content/ansible/images/cats_onboarding.png|1200|300|AAP onboarding cat"
  "content/OpenShift-Platform/Networking/images/logos/Migrating_br-ex_Logo.png|1200|300|br-ex logo"
  # Avatars — Toni has a single file used for list + profile, so keep 200px (not 96).
  "static/img/authors/toni-schmidbauer.png|200|25|Toni avatar (list+profile; was 512px/230KB)"
  "static/img/authors/thomas-jungbauer.png|96|15|Thomas avatar (list)"
  "static/img/authors/thomas-jungbauer-big.png|200|40|Thomas avatar (profile)"
)

kb_of() {
  local f="$1"
  echo $(( $(wc -c <"$f") / 1024 ))
}

dims_of() {
  magick identify -format '%wx%h' "$1" 2>/dev/null || echo '?x?'
}

backup_png() {
  local src="$1"
  local dest="$BACKUP_DIR/$src"
  mkdir -p "$(dirname "$dest")"
  cp -p "$src" "$dest"
}

# Compress in place toward target_kb; keeps last successful write.
compress_png() {
  local src="$1"
  local target_kb="$2"
  local tmp
  tmp="$(mktemp "${src}.XXXXXX.png")"
  cp "$src" "$tmp"

  local qualities=("80-95" "65-85" "50-75" "40-65" "30-55" "15-40")
  local q out_kb
  for q in "${qualities[@]}"; do
    if pngquant --quality="$q" --force --output "$tmp.q.png" -- "$tmp" 2>/dev/null; then
      mv "$tmp.q.png" "$tmp"
      out_kb="$(kb_of "$tmp")"
      if (( out_kb <= target_kb )); then
        break
      fi
    fi
  done

  # Palette / deflate if still over budget
  if (( $(kb_of "$tmp") > target_kb )); then
    magick "$tmp" -strip -colors 256 PNG8:"$tmp.opt.png" 2>/dev/null || true
    if [[ -f "$tmp.opt.png" ]] && (( $(kb_of "$tmp.opt.png") < $(kb_of "$tmp") )); then
      mv "$tmp.opt.png" "$tmp"
    else
      rm -f "$tmp.opt.png"
      magick "$tmp" -strip -define png:compression-level=9 "$tmp.opt.png"
      mv "$tmp.opt.png" "$tmp"
    fi
  fi

  # Last resort: step down width until under budget (min 800px)
  local w
  w="$(magick identify -format '%w' "$tmp")"
  while (( $(kb_of "$tmp") > target_kb )) && (( w > 800 )); do
    w=$(( w * 90 / 100 ))
    magick "$tmp" -resize "${w}x>" -colors 256 PNG8:"$tmp.opt.png"
    mv "$tmp.opt.png" "$tmp"
  done

  mv "$tmp" "$src"
}

regenerate_webp() {
  local src="$1"
  local webp="${src%.*}.webp"
  # Skip if no prior webp and not under authors (optional); always regenerate when sibling exists or for authors
  if [[ -f "$webp" ]] || [[ "$src" == static/img/authors/* ]]; then
    cwebp -quiet -q 85 "$src" -o "$webp" 2>/dev/null || true
  fi
}

optimize_one() {
  local src="$1"
  local max_w="$2"
  local target_kb="$3"
  local note="$4"

  if [[ ! -f "$src" ]]; then
    echo "SKIP missing: $src ($note)"
    return 0
  fi

  local before_kb before_dim
  before_kb="$(kb_of "$src")"
  before_dim="$(dims_of "$src")"

  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "DRY  $src  ${before_dim}  ${before_kb}KB  → max_w=${max_w} target≤${target_kb}KB  ($note)"
    return 0
  fi

  backup_png "$src"

  local work
  work="$(mktemp "${src}.work.XXXXXX.png")"
  cp "$src" "$work"

  if [[ "$max_w" -gt 0 ]]; then
    magick "$work" -strip -resize "${max_w}x>" "$work.resized.png"
    mv "$work.resized.png" "$work"
  else
    magick "$work" -strip "$work.stripped.png"
    mv "$work.stripped.png" "$work"
  fi

  mv "$work" "$src"
  compress_png "$src" "$target_kb"
  regenerate_webp "$src"

  local after_kb after_dim
  after_kb="$(kb_of "$src")"
  after_dim="$(dims_of "$src")"
  printf 'OK   %s  %s %sKB → %s %sKB  (backup: %s)  %s\n' \
    "$src" "$before_dim" "$before_kb" "$after_dim" "$after_kb" "$BACKUP_DIR/$src" "$note"
}

echo "Root:    $ROOT"
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Mode:    dry-run (no writes, no backup)"
else
  echo "Backup:  $BACKUP_DIR"
  mkdir -p "$BACKUP_DIR"
  echo "$TS" >"$BACKUP_DIR/README.txt"
  {
    echo "Original PNGs backed up before optimize-oversized-images.sh"
    echo "Restore one file:  cp \"$BACKUP_DIR/<relative-path>\" \"<relative-path>\""
    echo "Restore all:       rsync -a \"$BACKUP_DIR/content/\" content/ ; rsync -a \"$BACKUP_DIR/static/\" static/"
  } >>"$BACKUP_DIR/README.txt"
fi
echo

ok=0
for entry in "${TARGETS[@]}"; do
  IFS='|' read -r src max_w target_kb note <<<"$entry"
  optimize_one "$src" "$max_w" "$target_kb" "$note"
  ok=$((ok + 1))
done

# Day-2 duplicates of observability logos (if still present as copies)
DUPES=(
  "content/OpenShift-Platform/Day-2/images/observability/Logo_observability_1.png|416|80|Day-2 copy logo 1"
  "content/OpenShift-Platform/Day-2/images/observability/Logo_observability_2.png|416|80|Day-2 copy logo 2"
  "content/OpenShift-Platform/Day-2/images/observability/Logo_observability_7.png|416|80|Day-2 copy logo 7"
  "content/OpenShift-Platform/Day-2/images/observability/Logo_OTEL.png|416|80|Day-2 copy OTEL"
)
for entry in "${DUPES[@]}"; do
  IFS='|' read -r src max_w target_kb note <<<"$entry"
  if [[ -f "$src" ]]; then
    optimize_one "$src" "$max_w" "$target_kb" "$note"
  fi
done

echo
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry-run complete. Re-run without --dry-run to backup + optimize."
else
  echo "Done. Original PNGs: $BACKUP_DIR"
  echo "Total source bytes in backup: $(du -sh "$BACKUP_DIR" | awk '{print $1}')"
fi
