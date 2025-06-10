import asyncio
import time
from datetime import datetime
from typing import List, Callable, Dict, Any, Optional
import json

class PeriodicTaskExecutor:
    def __init__(self, interval: float):
        self.interval = interval
        self.tasks = []
        self.results_storage = []
        self.running = False
        self.error_count = 0

    def add_task(self, task_func: Callable, name: Optional[str] = None):
        """Add a task to be executed in each batch"""
        task_info = {
            'function': task_func,
            'name': name or task_func.__name__
        }
        self.tasks.append(task_info)

    async def execute_batch(self) -> Dict[str, Any]:
        """Execute all tasks and return results with metadata"""
        start_time = time.time()

        # Create coroutines for all tasks
        task_coroutines = [task['function']() for task in self.tasks]

        # Execute all tasks concurrently
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)

        # Process results and separate successful from failed
        processed_results = {}
        errors = {}

        for _, (task_info, result) in enumerate(zip(self.tasks, results)):
            task_name = task_info['name']

            if isinstance(result, Exception):
                errors[task_name] = str(result)
                self.error_count += 1
            else:
                processed_results[task_name] = result

        return {
            'timestamp': datetime.now().isoformat(),
            'execution_time': time.time() - start_time,
            'successful_results': processed_results,
            'errors': errors,
            'total_tasks': len(self.tasks)
        }

    async def start(self, max_batches: Optional[int] = None):
        """Start periodic execution"""
        self.running = True
        batch_count = 0

        while self.running and (max_batches is None or batch_count < max_batches):
            batch_count += 1

            print(f"\n--- Executing Batch #{batch_count} ---")

            batch_result = await self.execute_batch()
            self.results_storage.append(batch_result)

            # Log batch completion
            print(f"Batch #{batch_count} completed:")
            print(f"  Execution time: {batch_result['execution_time']:.2f}s")
            print(f"  Successful tasks: {len(batch_result['successful_results'])}")
            if batch_result['errors']:
                print(f"  Errors: {len(batch_result['errors'])}")

            # Wait for next interval
            await asyncio.sleep(self.interval)

        print(f"\nExecution completed. Total batches: {batch_count}, Total errors: {self.error_count}")

    def stop(self):
        """Stop the periodic execution"""
        self.running = False

    def get_results(self) -> List[Dict]:
        """Get all stored results"""
        return self.results_storage

    def save_results_to_file(self, filename: str):
        """Save results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.results_storage, f, indent=2)

# Example tasks
async def api_call_1():
    await asyncio.sleep(0.4)
    return {"api": "service1", "status": "success", "data": [1, 2, 3]}

async def api_call_2():
    await asyncio.sleep(0.6)
    if time.time() % 10 < 1:  # Simulate occasional failure
        raise Exception("API temporarily unavailable")
    return {"api": "service2", "status": "success", "data": {"count": 42}}

async def database_query():
    await asyncio.sleep(0.3)
    return {"query": "SELECT * FROM users", "rows": 156}

# Usage example
async def main():
    executor = PeriodicTaskExecutor(interval=3.0)

    # Add tasks
    executor.add_task(api_call_1, "API_Service_1")
    executor.add_task(api_call_2, "API_Service_2")
    executor.add_task(database_query, "Database_Query")

    # Run for a specific number of batches
    await executor.start(max_batches=5)

    # Get and display results
    results = executor.get_results()
    print(f"\nCollected {len(results)} batches of results")

    # Optionally save to file
    # executor.save_results_to_file("task_results.json")

asyncio.run(main())
