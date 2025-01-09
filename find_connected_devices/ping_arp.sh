#!/bin/bash

# Define the IP range
network_prefix="192.168.1"
start=0
end=225
output_file="mac_addresses.txt"

# Clear the output file
> "$output_file"

# Ping each IP in the range
echo "Pinging IP range $network_prefix.0 to $network_prefix.$end..."
for i in $(seq $start $end); do
    ping -c 1 -W 1 "$network_prefix.$i" &> /dev/null &
done

# Wait for all ping commands to finish
wait

# Use arp to get the MAC addresses, sort by IP address, and save them to the output file
echo "Fetching MAC addresses, sorting by IP, and saving to $output_file..."
arp -a | grep "$network_prefix" | awk '{print $2, $4}' | sed 's/[()]//g' | sort -V > "$output_file"

# Display the results
echo "MAC addresses saved to $output_file"
cat "$output_file"
