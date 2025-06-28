.PHONY: build start clean notebooks test

build:
	@echo "Setting up the environment..."
	@chmod +x setup.sh
	@./setup.sh

start:
ifdef FILE
	@echo "Starting SignalDrift from CSV file: $(FILE)..."
	@source venv/bin/activate && CSV_FILE=$(FILE) python ./src/main.py
else
	@echo "Starting SignalDrift..."
	@source venv/bin/activate && python ./src/main.py
endif

notebooks:
ifdef FILE
	@echo "Running notebook: $(FILE)..."
	@source venv/bin/activate && jupyter nbconvert --execute --to notebook --inplace notebooks/$(FILE).ipynb
else
	@echo "Starting Jupyter notebook"
	@source venv/bin/activate && cd notebooks && jupyter notebook --notebook-dir=.
endif

test:
ifdef FILE
	@echo "Running test file: $(FILE)..."
	@source venv/bin/activate && PYTHONPATH=src pytest -k "$(FILE)" src/tests/ -v $(ARGS) || \
	source venv/bin/activate && PYTHONPATH=src pytest $$(find src/tests -name "*$(FILE).py" -type f) -v $(ARGS)
else
	@echo "Running all tests with coverage..."
	@source venv/bin/activate && PYTHONPATH=src pytest src/ $(ARGS)
endif

clean:
	@echo "Cleaning up..."
	@rm -rf venv
	@rm -rf __pycache__
	@rm -rf .ipynb_checkpoints

