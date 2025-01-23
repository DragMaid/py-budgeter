install:
	pip install -r requirements.txt
vinstall:
	python -m venv venv
	source ./venv/bin/activate
	pip install -r requirements.txt
run:
	python ./src/main.py
dev:
	./scripts/run.sh
.PHONY: install run
