.PHONY: setup start clean

setup:
	@echo "Setting up the environment..."
	@chmod +x setup.sh
	@./setup.sh

start:
	@echo "Starting Jupyter notebook..."
	@source venv/bin/activate && jupyter notebook

clean:
	@echo "Cleaning up..."
	@rm -rf venv
	@rm -rf __pycache__
	@rm -rf .ipynb_checkpoints

