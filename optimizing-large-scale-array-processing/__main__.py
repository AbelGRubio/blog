import numpy as np
import os
import time
import threading
import psutil
import matplotlib.pyplot as plt
from multiprocessing import Pool


# Constants
channels = 6000
sampling_rate = 2000  # Hz
duration = 60  # seconds
samples = sampling_rate * duration  # 120_000
shape = (channels, samples)
dtype = 'float64'
file_path = 'data_array.npy'
chunk_size = 2000  # 1 second worth of samples

# Global to store memory usage
memory_log = []
all_memory_logs = {}  # Stores {label: [(t0, mem0), (t1, mem1), ...]}

def generate_data_file():
    if not os.path.exists(file_path):
        print("Generating dummy data file...")
        data = np.random.rand(*shape).astype(dtype)
        np.save(file_path, data)
        print("File created.")
    else:
        print("Data file already exists.")

def estimate_memory_usage():
    memory_bytes = channels * samples * np.dtype(dtype).itemsize
    memory_mb = memory_bytes / (1024 ** 2)
    print(f"Estimated memory usage: {memory_mb:.2f} MB")

# ----------- Chunk reading -----------

def read_chunk(path, chunk_idx, chunk_size):
    data = np.load(path, mmap_mode='r')
    start = chunk_idx * chunk_size
    end = start + chunk_size
    return data[:, start:end]

# ----------- Processing Functions -----------

def compute_squared_sum_full_load():
    data = np.load(file_path)  # Carga todo el array en RAM
    return np.sum(data ** 2, dtype='float64')

def compute_squared_sum_chunked():
    total_chunks = samples // chunk_size
    squared_sum = 0.0
    for i in range(total_chunks):
        chunk = read_chunk(file_path, i, chunk_size)
        squared_sum += np.sum(chunk ** 2)
    return squared_sum

def compute_squared_sum_memmap():
    data_memmap = np.load(file_path, mmap_mode='r')
    return np.sum(data_memmap ** 2, dtype='float64')


def incremental_squared_sum():
    total = 0.0
    total_chunks = samples // chunk_size
    for i in range(total_chunks):
        chunk = read_chunk(file_path, i, chunk_size)
        total += np.sum(chunk ** 2)
    return total

def process_chunk(chunk_idx):
    chunk = read_chunk(file_path, chunk_idx, chunk_size)
    return np.sum(chunk ** 2)

def parallel_squared_sum():
    total_chunks = samples // chunk_size
    with Pool() as pool:
        results = pool.map(process_chunk, range(total_chunks))
    return sum(results)

# ----------- Memory Monitoring -----------

def monitor_memory(interval=0.1):
    proc = psutil.Process(os.getpid())
    while monitoring_flag:
        mem = proc.memory_info().rss / (1024 ** 2)  # in MB
        memory_log.append((time.time(), mem))
        time.sleep(interval)

def benchmark_with_memory(func, label):
    global monitoring_flag, memory_log
    print(f"\nRunning: {label}")
    memory_log = []
    monitoring_flag = True

    monitor_thread = threading.Thread(target=monitor_memory)
    monitor_thread.start()

    start_time = time.time()
    result = func()
    end_time = time.time()

    monitoring_flag = False
    monitor_thread.join()

    print(f"{label} Result: {result:.2f}, Time: {end_time - start_time:.2f}s")
    all_memory_logs[label] = memory_log
    return result

def plot_memory_usage(label):
    if not memory_log:
        print("No memory data collected.")
        return
    times, mem_usage = zip(*memory_log)
    times = [t - times[0] for t in times]  # Normalize time
    plt.figure()
    plt.plot(times, mem_usage, label=label)
    plt.xlabel("Time (s)")
    plt.ylabel("Memory Usage (MB)")
    plt.title(f"Memory Usage Over Time - {label}")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{label.lower().replace(' ', '_')}_memory_plot.png")
    plt.show()

def plot_all_memory_usages():
    if not all_memory_logs:
        print("No memory logs collected.")
        return

    # Header de tabla Markdown
    table_md = "| Method                | Peak Memory Usage (GB) | Estimated Time (s) |\n"
    table_md += "|-----------------------|------------------------|---------------------|\n"

    plt.figure()

    for label, log in all_memory_logs.items():
        times, mem_usage = zip(*log)
        t0 = times[0]
        times = [t - t0 for t in times]
        max_mem_gb = max(mem_usage) / 1024  # MB to GB
        duration_s = times[-1]  # Approx duration in seconds

        # Añadir al gráfico
        plt.plot(times, mem_usage,
                 label=f"{label} (Max: {max_mem_gb:.2f} GB, "
                       f"Time: {duration_s:.2f}s)")

        # Añadir a la tabla Markdown
        table_md += (f"| {label:<21} | {max_mem_gb:>22.2f} "
                     f"| {duration_s:>19.2f} |\n")

    plt.xlabel("Time (s)")
    plt.ylabel("Memory Usage (MB)")
    plt.title("Memory Usage Over Time - All Methods")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("all_methods_memory_plot.png")
    plt.show()

    # Imprimir tabla Markdown
    print("\n### 📊 Benchmark Summary (Markdown Table)\n")
    print(table_md)




# ----------- Main -----------

if __name__ == "__main__":
    generate_data_file()
    estimate_memory_usage()

    results = {}
    results["Full Load in Memory"] = benchmark_with_memory(
        compute_squared_sum_full_load, "Full Load in Memory")
    results["Chunked Processing"] = benchmark_with_memory(
        compute_squared_sum_chunked, "Chunked Processing")
    results["Memory Mapping"] = benchmark_with_memory(
        compute_squared_sum_memmap, "Memory Mapping")
    results["Incremental Streaming"] = benchmark_with_memory(
        incremental_squared_sum, "Incremental Streaming")
    results["Parallel Processing"] = benchmark_with_memory(
        parallel_squared_sum, "Parallel Processing")

    # --- Validate that all results are (almost) equal ---
    reference = next(iter(results.values()))
    tolerance = 1e-5
    print("\n🔍 Verifying consistency across methods:")
    for label, value in results.items():
        diff = abs(value - reference)
        if diff < tolerance:
            print(f"✅ {label} matches (diff = {diff:.2e})")
        else:
            print(f"❌ {label} DOES NOT MATCH (diff = {diff:.2e})")

    plot_all_memory_usages()
