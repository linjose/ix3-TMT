.PHONY: install migrate admin run worker check test collectstatic docker-up docker-down

install:
	python3 -m venv .venv
	.venv/bin/pip install -U pip wheel
	.venv/bin/pip install -r requirements.txt

migrate:
	.venv/bin/python manage.py migrate

admin:
	.venv/bin/python manage.py createsuperuser

run:
	.venv/bin/python manage.py runserver 0.0.0.0:8000

worker:
	.venv/bin/python manage.py process_jobs --loop

check:
	.venv/bin/python manage.py check

collectstatic:
	.venv/bin/python manage.py collectstatic --noinput

test:
	.venv/bin/python manage.py test

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down
