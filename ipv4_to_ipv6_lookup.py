#!/usr/bin/env python3
"""
IPv4 to IPv6 Lookup Script
Reads IPv4 addresses from 'list.ipv4' and finds corresponding IPv6 addresses
Outputs only IPv6 addresses to 'list.ipv6'
"""

import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


def resolve_ipv4_to_ipv6(ipv4_address):
    """
    Resolve IPv4 address to IPv6 address using DNS reverse lookup

    Args:
        ipv4_address (str): IPv4 address to resolve

    Returns:
        str or None: IPv6 address if found, None otherwise
    """
    try:
        # Step 1: Reverse DNS lookup to get hostname
        hostname, _, _ = socket.gethostbyaddr(ipv4_address)

        # Step 2: Get IPv6 addresses for the hostname
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET6)

        # Extract IPv6 addresses
        ipv6_addresses = []
        for info in addr_info:
            ipv6_addr = info[4][0]
            if ipv6_addr not in ipv6_addresses:
                ipv6_addresses.append(ipv6_addr)

        # Return the first IPv6 address found
        if ipv6_addresses:
            return ipv6_addresses[0]

    except (socket.herror, socket.gaierror, OSError):
        # DNS resolution failed
        pass

    return None


def process_ipv4_list(input_file, output_file, max_workers):
    """
    Process a list of IPv4 addresses and find corresponding IPv6 addresses

    Args:
        input_file (str): Input file containing IPv4 addresses
        output_file (str): Output file for IPv6 addresses
        max_workers (int): Maximum number of concurrent threads
    """

    # Read IPv4 addresses from input file
    try:
        with open(input_file, 'r') as f:
            ipv4_addr = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    ipv4_addr.append(line)
    except FileNotFoundError:
        print("Error: Input file '" + input_file + "' not found")
        return
    except Exception as e:
        print("Error reading input file: " + e)
        return

    if not ipv4_addr:
        print("No IPv4 addresses found in input file")
        return

    print("Processing " + str(len(ipv4_addr)) + "IPv4 addresses...")

    # Thread-safe counter and results storage
    lock = threading.Lock()
    proc_cnt = 0
    found_cnt = 0
    ipv6_results = []

    def process_single_ip(ipv4):
        nonlocal proc_cnt, found_cnt

        ipv6 = resolve_ipv4_to_ipv6(ipv4)

        with lock:
            proc_cnt += 1
            if ipv6:
                found_cnt += 1
                ipv6_results.append(ipv6)

            # Progress indicator
            if proc_cnt % 10 == 0:
                out = "Processed: " + str(proc_cnt / len(ipv4_addr)) + " - "
                out += "Found: " + str(found_cnt) + " IPv6 addresses"
                print(out)

    # Process addresses concurrently
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(process_single_ip, ipv4) for ipv4 in ipv4_addr
        ]

        # Wait for all tasks to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print("Error processing address: " + e)

    end_time = time.time()

    # Write IPv6 results to output file
    try:
        with open(output_file, 'w') as f:
            for ipv6 in ipv6_results:
                f.write(ipv6 + "\n")
    except Exception as e:
        print("Error writing output file: " + e)
        return

    # Print statistics
    print(f"\nProcessing completed in {end_time - start_time:.2f} seconds")
    print(f"Total IPv4 addresses processed: {proc_cnt}")
    print(f"IPv6 addresses found: {found_cnt}")
    print(f"Success rate: {(found_cnt / proc_cnt * 100):.1f}%")
    print(f"Results saved to: {output_file}")


def main():
    """Main function"""
    print("IPv4 to IPv6 Lookup Tool")
    print("=" * 30)

    # Process with default files
    process_ipv4_list("list.ipv4", "list.ipv6", 20)

if __name__ == "__main__":
    main()
