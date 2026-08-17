.DEFAULT_GOAL := help
COMPOSE := docker compose

.PHONY: help up down restart reload logs logs-backend logs-frontend ps build backup

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

up: ## Levanta los servicios en segundo plano
	$(COMPOSE) up -d

down: ## Para y elimina los contenedores
	$(COMPOSE) down

restart: ## Reinicia los contenedores (sin recrearlos)
	$(COMPOSE) restart

reload: ## Recrea los contenedores para recoger cambios en .env
	$(COMPOSE) up -d --force-recreate

build: ## Reconstruye las imágenes (tras cambios en Dockerfile/dependencias)
	$(COMPOSE) up -d --build

ps: ## Estado de los servicios
	$(COMPOSE) ps

logs: ## Logs de todos los servicios en tiempo real
	$(COMPOSE) logs -f

logs-backend: ## Logs solo del backend
	$(COMPOSE) logs -f ragvault-backend

logs-frontend: ## Logs solo del frontend
	$(COMPOSE) logs -f ragvault-frontend

backup: ## Copia de seguridad de backend/data (BD SQLite + Chroma + ficheros subidos) en backups/
	@mkdir -p backups
	tar czf backups/ragvault-backup-$$(date +%Y%m%d-%H%M%S).tar.gz backend/data
	@echo "Backup creado en backups/"
