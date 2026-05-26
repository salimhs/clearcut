.PHONY: install dev test clean demo lint

install:
	pip install .

dev:
	pip install -e ".[all]"

test:
	python -m pytest tests/ -v

lint:
	ruff check clearcut/
	ruff format --check clearcut/

format:
	ruff format clearcut/

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

demo:
	@echo "Usage: clearcut process --main input.mp4 --output final.mp4"
	@echo "       clearcut trim --input input.mp4"
	@echo "       clearcut transcribe --input input.mp4"
