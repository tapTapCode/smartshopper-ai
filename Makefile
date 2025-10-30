.PHONY: help up down logs redis-cli es-status clean restart

help:
	@echo "SmartShopper AI Development Commands"
	@echo "===================================="
	@echo "up        - Start Redis and Elasticsearch"
	@echo "down      - Stop all services"
	@echo "logs      - View all service logs"
	@echo "redis-cli - Connect to Redis CLI"
	@echo "es-status - Check Elasticsearch status"
	@echo "clean     - Stop services and remove volumes"
	@echo "restart   - Restart all services"

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

redis-cli:
	docker-compose exec redis redis-cli

es-status:
	curl -s http://localhost:9200/_cluster/health?pretty

clean:
	docker-compose down -v
	docker-compose down --rmi all --volumes --remove-orphans

restart:
	docker-compose down
	docker-compose up -d