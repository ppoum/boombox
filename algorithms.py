from multiprocessing import Process, shared_memory
from multiprocessing.shared_memory import SharedMemory

import numpy

SENSIBILITY_CONST = 1.7


def start_algorithm(data: numpy.ndarray, samplerate: int, shared_buf: SharedMemory, algorithm_id: int, thread_count: int):
    # data is expected to have a shape of (n, 2), where n is the number of sample pairs
    # and a samplerate of 48000. Results might still work for other sample rates, but could be less
    # accurate.
    # TODO rewrite so that shared_memory buffer is passed as argument, and computation can be done
    #  in a streaming manner (assuming processing speed is faster than playing speed, which should be the case with
    #  modern CPUs).

    algorithms = [algo_uno]

    if algorithm_id > len(algorithms):
        print(f"Algorithm {algorithm_id} does not exist!")
        exit(2)

    print("Spawning threads...")
    for i in range(thread_count):
        result = shared_memory.SharedMemory(shared_buf.name)
        Process(target=algorithms[algorithm_id-1], args=(data, samplerate, result, i, thread_count)).start()
        print(f"Spawned thread {i}")
    print("Threads spawned")


def algo_uno(data: numpy.ndarray, samplerate: int, result: SharedMemory, thread_id, thread_count):
    # data is expected to have a shape of (n, 2), where n is the number of sample pairs
    # and a samplerate of 48000. Results might still work for other sample rates, but could be less
    # accurate.
    # TODO dynamically generate sample # for average energy (1s) and instant (20ms)

    # Calculate initial average energy (prefill buffer with first 48128 samples
    avg_e = 0
    variance = 0
    for a, b in data[:48128]:
        avg_e += a * a + b * b
    avg_e *= 1024 / 48128
    # for a, b in data[:48128]:
        # variance +=

    for i in range(thread_id*1024, data.shape[0], 1024*thread_count):
        if (i//1024) % (thread_count*10) == 0:
            print(f"[{thread_id}] {i} ({100*float(i)/data.shape[0]:.2f}%)")
        # 48128 samples ~= 1s
        if i > 48128:
            # New instant energy slice after initial buffer depleted, "shift" buffer and add last 1024
            avg_e = 0
            for a, b in data[i-48128:i]:
                avg_e += a * a + b * b
            avg_e *= 1024 / 48128

        # Compute instant energy (e)
        e = 0
        for a, b in data[i:i+1024]:
            e += a * a + b * b

        result.buf[i//1024] = 1 if e >= SENSIBILITY_CONST * avg_e else 0

    return result
