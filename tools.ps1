# COMP-3021 scanning tools.
#
# Each scanner runs by its own name, as if installed on your machine. You type
# the real command; Docker is handled for you. Underneath these are the genuine
# tools, so their own --help works (ZAP uses -h).
#
# The scanner target is a deliberately vulnerable app, kept in a container on
# purpose so it never touches your real system. A real app would not be wrapped
# this way. The container is a safety box for the lab, nothing more.
#
# Load once per terminal, from the project root:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   Unblock-File .\tools.ps1
#   . .\tools.ps1
#
# Docker Desktop must be running.


function semgrep {
    docker run --rm -v "${PWD}:/src" -w /src semgrep/semgrep:latest semgrep @args
}

function trufflehog {
    docker run --rm -v "${PWD}:/pwd" -w /pwd trufflesecurity/trufflehog:latest @args
}

function pip-audit {
    $inner = "pip install pip-audit -q && pip-audit " + ($args -join " ")
    docker run --rm -v "${PWD}:/src" -w /src python:3.10-slim sh -c $inner
}

function npm {
    docker run --rm -v "${PWD}:/src" -w /src node:20-slim npm @args
}

function zap-baseline.py {
    docker run --rm -t ghcr.io/zaproxy/zaproxy:stable zap-baseline.py @args
}

function zap-full-scan.py {
    docker run --rm -t ghcr.io/zaproxy/zaproxy:stable zap-full-scan.py @args
}