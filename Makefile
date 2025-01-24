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
reset:
	./scripts/reset.sh
test:
	./scripts/test.sh
.PHONY: reset install run
