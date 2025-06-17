.PHONY: build start clean notebooks test db-up db-down db-setup db-test-setup db-clean db-logs

build:
	@echo "Setting up the environment..."
	@chmod +x setup.sh
	@./setup.sh

start:
	@echo "Starting SignalDrift..."
	@source venv/bin/activate && python ./src/main.py

notebooks:
	@echo "Starting Jupyter notebook"
	@source venv/bin/activate && cd notebooks && jupyter notebook --notebook-dir=.

test:
	@echo "Running all tests..."
	@source venv/bin/activate && pytest src/

# Database commands
db-up:
	@echo "Starting PostgreSQL with TimescaleDB..."
	@docker-compose up -d postgres

db-down:
	@echo "Stopping PostgreSQL..."
	@docker-compose down

db-setup: db-up
	@echo "Setting up development database..."
	@sleep 5
	@echo "Database is ready at localhost:5432"
	@echo "Database: signaldrift, User: signaldrift, Password: signaldrift_dev_password"

db-test-setup:
	@echo "Starting test database..."
	@docker-compose up -d postgres_test
	@sleep 5
	@echo "Test database is ready at localhost:5433"
	@echo "Database: signaldrift_test, User: signaldrift_test, Password: signaldrift_test_password"

db-clean:
	@echo "Cleaning up databases and volumes..."
	@docker-compose down -v
	@docker volume prune -f

db-logs:
	@echo "Showing database logs..."
	@docker-compose logs -f postgres

clean:
	@echo "Cleaning up..."
	@rm -rf venv
	@rm -rf __pycache__
	@rm -rf .ipynb_checkpoints

