.PHONY: install test run

URL ?=
OUTPUT ?= output/summary.pdf

install:
	python3 -m pip install -r requirements.txt

test:
	python3 -m pytest tests/ -v

run:
	@test -n "$(URL)" || (echo "Usage: make run URL=https://youtu.be/..."; exit 1)
	python3 src/main.py "$(URL)" --output "$(OUTPUT)"
