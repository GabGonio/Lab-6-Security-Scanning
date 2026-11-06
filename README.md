# WAREZ RELEASE TRACKER

A private release tracking database for COMP-3021. Used as a scanner target for
Lab 4. Contains deliberate security vulnerabilities for scanning tools to find.

---

## Step 1: Initialise the repository

Run the included PowerShell script once after extracting the zip:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
Unblock-File .\init_repo.ps1
.\init_repo.ps1
```

This sets up the git history that truffleHog will scan. You only need to do this
once.

---

## Step 2: Start the application

```powershell
docker compose up
```

Then open your browser and go to:

```
http://localhost:5000
```

Wait about 10 seconds on first run for the database to initialise.

To stop the app:

```powershell
docker compose down
```

---

## Seeded accounts

| Username | Password  |
| -------- | --------- |
| admin    | warez1984 |
| sysop    | topcrack  |
| razor    | scene1983 |
| thg      | release4  |

---

## What the app does

| Page      | URL       | Description                         |
| --------- | --------- | ----------------------------------- |
| Dashboard | /         | Recent releases and stats           |
| Releases  | /releases | Searchable release database         |
| Crew      | /groups   | Known release groups                |
| Submit    | /submit   | Log a new release (login required)  |
| Login     | /login    | Log in with a username and password |

---

## Running the scanners

The scanning tools run inside Docker, so this deliberately vulnerable app never
touches your real system. Because of that, the tools are not installed on your
machine. A small script, `tools.ps1`, lets you run each one by its normal name.
Load it once per terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
Unblock-File .\tools.ps1
. .\tools.ps1
```

The leading dot on `. .\tools.ps1` loads the tool names into this terminal. After
that, run the tools as if they were installed. Load it again in any new terminal.

The app must be running for ZAP. The other tools read files and do not need it.

```powershell
semgrep scan --config auto .
trufflehog git file://. --no-update
pip-audit -r requirements.txt
npm audit
zap-baseline.py -t http://host.docker.internal:5000
```

---

## Notes

- Do not use real credentials on this application.
- For educational use only.
