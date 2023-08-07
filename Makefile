prepare:
	cp example.env .env
	docker-compose build

start:
	docker-compose up -d

stop:
	docker-compose stop

remove:
	docker-compose down

restart:
	docker-compose down
	docker-compose up -d

format:
	pre-commit run -a