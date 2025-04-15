import time
import statistics
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import os
import json

from execution_engine.docker_engine import DockerExecutionEngine
from execution_engine.gvisor_engine import GVisorExecutionEngine

class PerformanceComparison:
    """
    A class to compare the performance of different virtualization technologies
    """
    def __init__(self):
        """
        Initialize the engines for comparison
        """
        self.docker_engine = DockerExecutionEngine()
        self.gvisor_engine = GVisorExecutionEngine()
        self.results_dir = Path(__file__).parent.parent / "docs" / "performance"
        
        # Create results directory if it doesn't exist
        os.makedirs(self.results_dir, exist_ok=True)
    
    def run_benchmark(self, function, event_data, iterations=10):
        """
        Run benchmark tests comparing Docker and gVisor
        """
        print(f"Running benchmark for function {function.name} ({function.id})")
        print(f"Iterations: {iterations}")
        
        # Build Docker image if needed
        if not function.container_image:
            print("Building Docker image...")
            function.container_image = self.docker_engine.build_function_image(function)
        
        # Build gVisor image
        print("Building gVisor image...")
        gvisor_image = self.gvisor_engine.build_function_image(function)
        
        # Results storage
        docker_times = []
        gvisor_times = []
        
        # Warm-up run (not counted)
        print("Performing warm-up run...")
        self.docker_engine.execute_function(function, event_data)
        
        # Run Docker benchmarks
        print("Running Docker benchmarks...")
        for i in range(iterations):
            start_time = time.time()
            self.docker_engine.execute_function(function, event_data)
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
            docker_times.append(execution_time)
            print(f"Docker iteration {i+1}: {execution_time:.2f}ms")
        
        # Update function container image for gVisor
        original_image = function.container_image
        function.container_image = gvisor_image
        
        # Run gVisor benchmarks
        print("Running gVisor benchmarks...")
        for i in range(iterations):
            start_time = time.time()
            self.gvisor_engine.execute_function(function, event_data)
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
            gvisor_times.append(execution_time)
            print(f"gVisor iteration {i+1}: {execution_time:.2f}ms")
        
        # Restore original image
        function.container_image = original_image
        
        # Calculate statistics
        docker_avg = statistics.mean(docker_times)
        gvisor_avg = statistics.mean(gvisor_times)
        docker_std = statistics.stdev(docker_times) if len(docker_times) > 1 else 0
        gvisor_std = statistics.stdev(gvisor_times) if len(gvisor_times) > 1 else 0
        
        # Create results dictionary
        results = {
            "function_id": function.id,
            "function_name": function.name,
            "iterations": iterations,
            "docker": {
                "times": docker_times,
                "average": docker_avg,
                "stddev": docker_std
            },
            "gvisor": {
                "times": gvisor_times,
                "average": gvisor_avg,
                "stddev": gvisor_std
            },
            "comparison": {
                "gvisor_overhead": (gvisor_avg / docker_avg - 1) * 100 if docker_avg > 0 else 0
            }
        }
        
        # Save results to file
        results_file = self.results_dir / f"benchmark_{function.id}_{int(time.time())}.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        # Generate and save charts
        self._generate_charts(results, function.id)
        
        return results
    
    def _generate_charts(self, results, function_id):
        """
        Generate charts comparing the performance
        """
        # Bar chart
        labels = ['Docker', 'gVisor']
        averages = [results["docker"]["average"], results["gvisor"]["average"]]
        std_devs = [results["docker"]["stddev"], results["gvisor"]["stddev"]]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        x = np.arange(len(labels))
        width = 0.35
        
        rects = ax.bar(x, averages, width, yerr=std_devs, alpha=0.7, capsize=10, 
                     color=['#3498db', '#e74c3c'], label='Execution Time')
        
        ax.set_ylabel('Execution Time (ms)')
        ax.set_title(f'Performance Comparison - Function {function_id}')
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()
        
        # Add labels on top of bars
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.2f}ms',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom')
        
        # Add overhead percentage
        overhead = results["comparison"]["gvisor_overhead"]
        ax.annotate(f'{overhead:.1f}% overhead',
                    xy=(1, averages[1]),
                    xytext=(0, -30),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    color='#e74c3c')
        
        # Save chart
        chart_file = self.results_dir / f"benchmark_chart_{function_id}_{int(time.time())}.png"
        plt.tight_layout()
        plt.savefig(chart_file)
        plt.close()

if __name__ == "__main__":
    # This script can be run independently to test performance
    from sqlalchemy.orm import Session
    from backend.db.database import get_db
    from backend.models.function import Function
    
    # Get database session
    db = next(get_db())
    
    # Get the first active function
    function = db.query(Function).filter(Function.is_active == True).first()
    
    if function:
        # Run benchmark
        comparison = PerformanceComparison()
        results = comparison.run_benchmark(function, {"test": "data"})
        
        # Print results
        print("\nBenchmark Results:")
        print(f"Docker average: {results['docker']['average']:.2f}ms")
        print(f"gVisor average: {results['gvisor']['average']:.2f}ms")
        print(f"gVisor overhead: {results['comparison']['gvisor_overhead']:.1f}%")
    else:
        print("No active functions found. Please create and deploy a function first.")
