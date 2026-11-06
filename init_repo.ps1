# Run this once after extracting the zip to set up the git repository.
# This creates the git history that scanning tools will analyse.

git init
git config user.email "sysop@warez.local"
git config user.name "Sysop"

# Initial commit with a sync API token.
# The URL is assembled from parts so the credential lives only in the file this
# script writes (sync.py), not in the script itself. Secret scanners should
# find it in the deleted file in history, not here.
$user = "warez_sync"
$pass = "xf0rc3-4p1-t0k3n-1984"
$dbhost = "sync.warez.local:5432"
"SYNC_DB_URL = 'postgresql://${user}:${pass}@${dbhost}/warezdb'" | Out-File -FilePath sync.py -Encoding utf8
git add sync.py
git commit -m "add release sync config"

# Remove the token file
git rm sync.py
git commit -m "move config out of source"

# Commit the application files
git add .
git commit -m "warez tracker v1.0"

Write-Host "Repository initialised. Run 'docker compose up' to start the app."
