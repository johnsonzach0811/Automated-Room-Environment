"""Govee LAN discovery and status reads, following the official WLAN guide.

https://app-h5.govee.com/user-manual/wlan-guide
Discovery/status never changes lighting. Replies arrive on UDP port 4002.
"""
import ipaddress
import json
import socket
import time


def query(command, destination, port, seconds=3):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(('', 4002))
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
        if command == 'scan':
            membership = socket.inet_aton('239.255.255.250') + socket.inet_aton('0.0.0.0')
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
        sock.sendto(json.dumps({'msg': {'cmd': command, 'data':
                    {'account_topic': 'reserve'} if command == 'scan' else {}}}).encode(), (destination, port))
        deadline = time.monotonic() + seconds
        results = []
        while time.monotonic() < deadline:
            sock.settimeout(max(0.01, deadline - time.monotonic()))
            try:
                packet, address = sock.recvfrom(8192)
            except socket.timeout:
                break
            try:
                message = json.loads(packet)['msg']
                if message['cmd'] != command or not isinstance(message['data'], dict):
                    continue
                if command == 'devStatus' and address[0] != destination:
                    continue
                data = dict(message['data'], source_ip=address[0])
                if command == 'scan':
                    ipaddress.IPv4Address(data.get('ip'))
                    if data['ip'] != address[0] or not isinstance(data.get('device'), str):
                        continue
                if data not in results:
                    results.append(data)
                if command == 'devStatus':
                    break
            except (KeyError, TypeError, ValueError):
                continue
        return results


def discover():
    return query('scan', '239.255.255.250', 4001)


def status(ip, port=4003):
    results = query('devStatus', ip, port)
    if not results:
        raise TimeoutError('No device status received; delivery cannot be verified')
    return results[0]


def resolve_device(device):
    """When paired, resolve by stable identity rather than trusting a DHCP address."""
    if not device.get('identity'):
        return device
    matches = [item for item in discover() if item['device'] == device['identity']]
    if len(matches) != 1:
        raise OSError('Paired light was not uniquely discovered; no control commands sent')
    return dict(device, ip=matches[0]['ip'])
