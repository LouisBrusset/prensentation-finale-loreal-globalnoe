# =============================================================================
# final_presentation — commandes de dev
#
# `make` seul affiche l'aide. Sur Windows, si `make` n'est pas installe,
# utilise l'equivalent PowerShell : .\make.ps1 <cible>   (memes noms de cibles)
# =============================================================================

SHELL := cmd.exe
.SHELLFLAGS := /c

UV        := uv
PORT_API  ?= 8010
PORT_USER ?= 5173
PORT_DECK ?= 5174

.DEFAULT_GOAL := help
.PHONY: help install dev back serve-user serve-deck test lint format qr qr-lan ip seed reset clean

## ---------------------------------------------------------------------------
help: ## Affiche cette aide
	@echo.
	@echo   final_presentation - cibles disponibles
	@echo   ---------------------------------------
	@echo   make install      Cree .venv et installe les dependances (uv)
	@echo   make dev          Lance TOUT en local (API + deck + app participant)
	@echo   make back         Lance uniquement l'API FastAPI
	@echo   make serve-user   Sert frontend_user seul sur le port $(PORT_USER)
	@echo   make serve-deck   Sert frontend_main seul sur le port $(PORT_DECK)
	@echo   make test         Lance les tests backend
	@echo   make lint         Verifie le style (ruff)
	@echo   make format       Corrige le style (ruff --fix)
	@echo   make ip           Affiche l'IP LAN a donner aux telephones
	@echo   make qr           Genere static/qr/join.png depuis FP_PUBLIC_APP_URL
	@echo   make qr-lan       Genere le QR pointant vers l'IP LAN detectee
	@echo   make seed         Injecte 25 faux participants et leurs reponses
	@echo   make reset        Remet la session a zero
	@echo   make clean        Supprime .venv, caches et QR generes
	@echo.

## ---------------------------------------------------------------------------
install: ## Environnement virtuel + dependances
	$(UV) venv
	$(UV) sync --all-groups
	@echo.
	@echo Environnement pret. Lance maintenant : make dev

## ---------------------------------------------------------------------------
dev: ## Tout-en-un : l'API sert aussi les deux front-ends
	@echo.
	@echo   Deck presentateur : http://localhost:$(PORT_API)/deck
	@echo   App participant   : http://localhost:$(PORT_API)/app
	@echo   Doc API           : http://localhost:$(PORT_API)/docs
	@echo.
	$(UV) run uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port $(PORT_API)

back: ## API seule (equivalent de dev, nom explicite)
	$(UV) run uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port $(PORT_API)

serve-user: ## Sert frontend_user comme le fera Netlify (statique pur)
	$(UV) run python -m http.server $(PORT_USER) --directory frontend_user --bind 0.0.0.0

serve-deck: ## Sert frontend_main comme un site statique
	$(UV) run python -m http.server $(PORT_DECK) --directory frontend_main --bind 0.0.0.0

## ---------------------------------------------------------------------------
test: ## Tests backend
	$(UV) run pytest -q

lint: ## Verification du style
	$(UV) run ruff check backend scripts

format: ## Correction automatique du style
	$(UV) run ruff check --fix backend scripts
	$(UV) run ruff format backend scripts

## ---------------------------------------------------------------------------
ip: ## IP LAN de cette machine
	$(UV) run python -c "import socket;s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.connect(('8.8.8.8',80));print('IP LAN :',s.getsockname()[0])"

qr: ## QR vers FP_PUBLIC_APP_URL
	$(UV) run python scripts/gen_qr.py

qr-lan: ## QR vers l'app participant sur l'IP LAN (identique a `qr`)
	$(UV) run python scripts/gen_qr.py

## ---------------------------------------------------------------------------
seed: ## 25 faux participants + leurs reponses (repetitions, captures d'ecran)
	$(UV) run python -c "import urllib.request,json;r=urllib.request.Request('http://localhost:$(PORT_API)/api/admin/seed',data=json.dumps({'participants':25}).encode(),headers={'Content-Type':'application/json','X-Admin-Token':'loreal2026'});print(urllib.request.urlopen(r).read().decode())"

reset: ## Session remise a zero
	$(UV) run python -c "import urllib.request,json;r=urllib.request.Request('http://localhost:$(PORT_API)/api/admin/reset',data=b'{}',headers={'Content-Type':'application/json','X-Admin-Token':'loreal2026'});print(urllib.request.urlopen(r).read().decode())"

## ---------------------------------------------------------------------------
clean: ## Nettoyage complet
	-rmdir /s /q .venv
	-rmdir /s /q .pytest_cache
	-rmdir /s /q .ruff_cache
	-del /q static\qr\*.png
