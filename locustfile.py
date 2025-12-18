"""
Locust load testing script for KubeServe inference endpoints.

This script tests the prediction endpoints under load to verify:
- HPA (Horizontal Pod Autoscaler) triggers correctly
- System handles concurrent requests
- Latency remains acceptable under load
"""

from locust import HttpUser, task, between, events
import json
import random


class KubeServeUser(HttpUser):
    """
    Simulates a user making prediction requests to a deployed model.
    """
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when a simulated user starts."""
        # Example prediction data (adjust based on your model)
        self.prediction_data = {
            "data": [[random.uniform(0, 10), random.uniform(0, 10)]]
        }
    
    @task(3)
    def predict_single(self):
        """
        Make a single prediction request.
        Weight: 3 (most common operation)
        """
        response = self.client.post(
            "/predict",
            json=self.prediction_data,
            name="predict_single",
            catch_response=True
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                if "predictions" in data:
                    response.success()
                else:
                    response.failure("Missing 'predictions' in response")
            except json.JSONDecodeError:
                response.failure("Invalid JSON response")
        else:
            response.failure(f"HTTP {response.status_code}")
    
    @task(1)
    def predict_batch(self):
        """
        Make a batch prediction request.
        Weight: 1 (less common)
        """
        batch_data = {
            "data": [
                [random.uniform(0, 10), random.uniform(0, 10)]
                for _ in range(random.randint(2, 10))
            ]
        }
        
        response = self.client.post(
            "/predict",
            json=batch_data,
            name="predict_batch",
            catch_response=True
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                if "predictions" in data:
                    response.success()
                else:
                    response.failure("Missing 'predictions' in response")
            except json.JSONDecodeError:
                response.failure("Invalid JSON response")
        else:
            response.failure(f"HTTP {response.status_code}")
    
    @task(1)
    def health_check(self):
        """
        Check deployment health.
        Weight: 1
        """
        response = self.client.get(
            "/health",
            name="health_check",
            catch_response=True
        )
        
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"HTTP {response.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the test starts."""
    print("\n" + "="*60)
    print("🚀 Starting KubeServe Load Test")
    print("="*60)
    print(f"Target: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print("="*60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the test stops."""
    print("\n" + "="*60)
    print("✅ Load Test Completed")
    print("="*60)
    stats = environment.stats
    print(f"\nTotal Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Average Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"Min Response Time: {stats.total.min_response_time:.2f}ms")
    print(f"Max Response Time: {stats.total.max_response_time:.2f}ms")
    print("="*60 + "\n")

