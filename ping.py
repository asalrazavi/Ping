import socket
import os
import sys
import struct
import time
import select
import binascii

# Define the ICMP packet structure
class ICMP:
    def __init__(self):
        self.type = 8  # ICMP Type 8 is for echo request
        self.code = 0
        self.checksum = 0
        self.id = 0
        self.seq = 0

    def calculate_checksum(self, data):
        # Helper function to calculate checksum
        checksum = 0
        for i in range(0, len(data), 2):
            checksum += (data[i] << 8) + data[i + 1]
        checksum = (checksum >> 16) + (checksum & 0xffff)
        checksum += (checksum >> 16)
        return (~checksum) & 0xffff

    def pack(self):
        # Pack the ICMP packet into a byte array
        packet = struct.pack("bbHHh", self.type, self.code, self.checksum, self.id, self.seq)
        data = struct.pack("d", time.time())
        checksum = self.calculate_checksum(packet + data)
        packet = struct.pack("bbHHh", self.type, self.code, socket.htons(checksum), self.id, self.seq)
        return packet + data


def ping(host, count):
    # Resolve the host name to IP address
    try:
        ip = socket.gethostbyname(host)
    except socket.gaierror:
        print("Invalid hostname")
        return

    # Create a socket and set the timeout
    icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    icmp_socket.settimeout(1)

    total_rtt = 0
    total_packets_sent = 0
    total_packets_received = 0

    # Create an ICMP packet
    icmp_packet = ICMP()

    for _ in range(count):
        # Send the ICMP packet to the destination
        icmp_socket.sendto(icmp_packet.pack(), (ip, 1))
        total_packets_sent += 1

        # Wait for the response
        try:
            start_time = time.time()
            ready, _, _ = select.select([icmp_socket], [], [], 1)
            if ready:
                data, addr = icmp_socket.recvfrom(1024)
                end_time = time.time()
                rtt = (end_time - start_time) * 1000
                total_rtt += rtt
                total_packets_received += 1
                print(f"Ping Successful: Time = {rtt:.2f}ms")
            else:
                print("Ping Timed Out")
        except socket.timeout:
            print("Ping Timed Out")

    icmp_socket.close()

    if total_packets_sent > 0:
        packet_loss = (total_packets_sent - total_packets_received) / total_packets_sent * 100
        average_rtt = total_rtt / total_packets_received if total_packets_received > 0 else 0

        print(f"\n--- Ping Statistics ---")
        print(f"Packets Sent: {total_packets_sent}")
        print(f"Packets Received: {total_packets_received}")
        print(f"Packet Loss: {packet_loss:.2f}%")
        print(f"Average RTT: {average_rtt:.2f}ms")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 ping.py <host> <count>")
    else:
        host = sys.argv[1]
        count = int(sys.argv[2])
        ping(host, count)
