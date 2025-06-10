.PHONY: build start clean notebooks test

build:
	@echo "Setting up the environment..."
	@chmod +x setup.sh
	@./setup.sh

start:
	@echo "Starting Jupyter notebook..."
	@source venv/bin/activate && jupyter notebook

notebooks:
	@echo "Starting Jupyter notebook"
	@source venv/bin/activate && cd notebooks && jupyter notebook --notebook-dir=.

test:
	@echo "Running all tests..."
	@source venv/bin/activate && pytest src/

clean:
	@echo "Cleaning up..."
	@rm -rf venv
	@rm -rf __pycache__
	@rm -rf .ipynb_checkpoints

