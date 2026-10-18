#!/usr/bin/env bash
# LinguaLens on Google Cloud Run: a permanent HTTPS URL for the phone and the
# glasses, wherever you are. Scales to zero, so it costs nothing while unused.
#
#   ./deploy.sh          build + deploy (first run also creates the bucket + key)
#   ./deploy.sh url      print the phone / glasses / OBS links
#
# Progress (state.json) lives in a Cloud Storage bucket mounted at /data.
# max-instances=1 because sessions are in memory: the glasses page and the
# phone must reach the same instance. Speech keys (IFLYTEK_*, AZURE_*) can be
# added later with: gcloud run services update lingualens --update-env-vars ...
set -euo pipefail
cd "$(dirname "$0")"

PROJECT="${PROJECT:-chrome-up-irl-e8d7}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-lingualens}"
BUCKET="${BUCKET:-${PROJECT}-lingualens}"
G=(gcloud --project "$PROJECT" --quiet)

current_key() {
  "${G[@]}" run services describe "$SERVICE" --region "$REGION" --format=json 2>/dev/null \
    | python3 -c 'import json,sys
try: env = json.load(sys.stdin)["spec"]["template"]["spec"]["containers"][0].get("env", [])
except Exception: env = []
print(next((e.get("value", "") for e in env if e.get("name") == "LINGUALENS_KEY"), ""))'
}

links() {
  local url key
  url="$("${G[@]}" run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')"
  key="$(current_key || true)"
  cat <<TXT

  phone (talk here)    $url/phone?key=$key&client_id=me
  glasses web app      $url/?key=$key&client_id=me
  OBS browser source   $url/?key=$key&client_id=me     (deploy/obs-vps: LINGUALENS_URL)
  Android wrapper      lingualens_url=$url and lingualens_key=$key in android/local.properties

  Same client_id everywhere = one session shared by phone, glasses and stream.
TXT
}

if [ "${1:-}" = "url" ]; then links; exit 0; fi

"${G[@]}" services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com storage.googleapis.com >/dev/null

"${G[@]}" storage buckets describe "gs://$BUCKET" >/dev/null 2>&1 \
  || "${G[@]}" storage buckets create "gs://$BUCKET" --location "$REGION" --uniform-bucket-level-access

# the service runs as the default compute account; let it read/write progress
SA="$("${G[@]}" projects describe "$PROJECT" --format='value(projectNumber)')-compute@developer.gserviceaccount.com"
"${G[@]}" storage buckets add-iam-policy-binding "gs://$BUCKET" \
  --member "serviceAccount:$SA" --role roles/storage.objectUser >/dev/null

KEY="$(current_key || true)"
[ -n "$KEY" ] || KEY="$(openssl rand -hex 12)"

"${G[@]}" run deploy "$SERVICE" --source ../../lingualens --region "$REGION" \
  --allow-unauthenticated \
  --execution-environment gen2 --cpu 1 --memory 1Gi \
  --min-instances 0 --max-instances 1 --session-affinity --timeout 3600 \
  --add-volume "name=state,type=cloud-storage,bucket=$BUCKET" \
  --add-volume-mount "volume=state,mount-path=/data" \
  --update-env-vars "LINGUALENS_STATE=/data/state.json,LINGUALENS_KEY=$KEY"

links
