.PHONY: all build run stop wait-db migrate create-user

all: build run migrate create-user

build:
	docker compose build

run:
	docker compose up -d

stop:
	docker compose down

wait-db:
	@until docker compose exec mysql-db \
		sh -c 'mysql -u root -p"$$MYSQL_ROOT_PASSWORD" -e "SELECT 1"' 2>/dev/null; \
	do echo "Waiting for MySQL... Timeout 5 seconds"; sleep 5; done

migrate:
	make wait-db
	docker compose exec flask-app flask db init || true
	docker compose exec flask-app flask db migrate
	docker compose exec flask-app flask db upgrade

create-user:
	@read -p "Enter username: " username; \
	read -sp "Enter password: " password; \
	docker compose exec flask-app python scripts/create_user.py $$username $$password