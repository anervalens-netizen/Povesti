.PHONY: install run test validate docker
install:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
run:
	.venv/bin/python -m app.main
test:
	.venv/bin/pytest -q
validate:
	.venv/bin/python scripts/validate_stories.py
docker:
	docker compose up -d --build
