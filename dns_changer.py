#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DNS Changer Eye - macOS Sequoia Edition
Rotação automática de servidores DNS para privacidade e segurança
Desenvolvido para macOS Sequoia (15.0+)

Autor: Adaptação para macOS
Baseado em: DNS Changer Eye (BullsEye0)
Data: 2026
"""

import os
import sys
import random
import time
import subprocess
import logging
import signal
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional

# ============================================================================
# CONFIGURAÇÃO DE LOGGING
# ============================================================================

LOG_DIR = Path.home() / ".dns_changer"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "dns_changer.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# SERVIDORES DNS
# ============================================================================

DNS_SERVERS = [
    # Cloudflare
    ("1.1.1.1", "1.0.0.1"),
    # Quad9
    ("9.9.9.9", "149.112.112.112"),
    # OpenDNS
    ("208.67.222.222", "208.67.220.220"),
    # Verisign
    ("64.6.64.6", "64.6.65.6"),
    # UncensoredDNS
    ("91.239.100.100", "89.233.43.71"),
    # CleanBrowsing
    ("185.228.168.9", "185.228.169.9"),
    # Yandex
    ("77.88.8.8", "77.88.8.1"),
    # AdGuard
    ("176.103.130.130", "176.103.130.131"),
    # DNS Advantage
    ("156.154.70.1", "156.154.71.1"),
    # Norton
    ("199.85.126.10", "199.85.127.10"),
    # GreenTeam
    ("81.218.119.11", "209.88.198.133"),
    # SafeDNS
    ("195.46.39.39", "195.46.39.40"),
    # SmartViper
    ("208.76.50.50", "208.76.51.51"),
    # Dyn
    ("216.146.35.35", "216.146.36.36"),
    # FreeDNS
    ("37.235.1.174", "37.235.1.177"),
    # Alternate DNS
    ("198.101.242.72", "23.253.163.53"),
    # puntCAT
    ("109.69.8.51", "8.8.8.8"),
    # Quad101
    ("101.101.101.101", "101.102.103.104"),
    # FDN
    ("80.67.169.12", "80.67.169.40"),
    # OpenNIC
    ("185.121.177.177", "185.121.177.53"),
    # AS250.net
    ("195.10.46.179", "212.82.225.7"),
    # Orange
    ("194.168.4.100", "194.168.8.100"),
    # SingNet
    ("203.122.222.6", "203.122.223.6"),
    # Level3
    ("209.244.0.3", "209.244.0.4"),
    # Google
    ("8.8.8.8", "8.8.4.4"),
]

# ============================================================================
# CLASSE PRINCIPAL
# ============================================================================

class DNSChanger:
    """Gerenciador de rotação de DNS para macOS"""
    
    def __init__(self, interval: int = 300, interface: Optional[str] = None):
        """
        Inicializa o DNS Changer
        
        Args:
            interval: Intervalo em segundos para rotação de DNS (padrão: 300 = 5 min)
            interface: Interface de rede específica (Wi-Fi, Ethernet, etc.)
        """
        self.interval = interval
        self.interface = interface or self._detect_interface()
        self.running = False
        self.current_dns = None
        
        # Registrar handlers de sinal para encerramento gracioso
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        logger.info(f"DNS Changer inicializado para interface: {self.interface}")
    
    def _signal_handler(self, signum, frame):
        """Handler para sinais de encerramento"""
        logger.info("Recebido sinal de encerramento, encerrando...")
        self.running = False
        sys.exit(0)
    
    def _detect_interface(self) -> str:
        """
        Detecta automaticamente a interface de rede ativa
        
        Returns:
            Nome da interface (ex: 'Wi-Fi', 'Ethernet')
        """
        try:
            result = subprocess.run(
                ["route", "get", "default"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            for line in result.stdout.split('\n'):
                if 'interface:' in line:
                    interface = line.split(':')[1].strip()
                    logger.info(f"Interface detectada: {interface}")
                    return interface
        except Exception as e:
            logger.warning(f"Erro ao detectar interface: {e}")
        
        logger.warning("Usando interface padrão: Wi-Fi")
        return "Wi-Fi"
    
    def _validate_dns(self, dns1: str, dns2: str) -> bool:
        """
        Valida endereços IP de DNS
        
        Args:
            dns1: Primeiro servidor DNS
            dns2: Segundo servidor DNS
            
        Returns:
            True se válidos, False caso contrário
        """
        import ipaddress
        
        try:
            ipaddress.ip_address(dns1)
            ipaddress.ip_address(dns2)
            return True
        except ValueError:
            logger.error(f"DNS inválido: {dns1} ou {dns2}")
            return False
    
    def _run_command(self, command: List[str]) -> Tuple[bool, str]:
        """
        Executa comando com privilégios de root
        
        Args:
            command: Lista com comando e argumentos
            
        Returns:
            Tupla (sucesso, mensagem)
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "Comando expirou (timeout)"
        except Exception as e:
            return False, str(e)
    
    def get_current_dns(self) -> Optional[Tuple[str, str]]:
        """
        Obtém configuração de DNS atual
        
        Returns:
            Tupla (dns1, dns2) ou None se não conseguir obter
        """
        success, output = self._run_command(
            ["networksetup", "-getdnsservers", self.interface]
        )
        
        if success and output:
            dns_list = output.strip().split('\n')
            if len(dns_list) >= 2:
                return (dns_list[0], dns_list[1])
            elif len(dns_list) == 1:
                return (dns_list[0], dns_list[0])
        
        return None
    
    def set_dns(self, dns1: str, dns2: str) -> bool:
        """
        Define novos servidores DNS
        
        Args:
            dns1: Primeiro servidor DNS
            dns2: Segundo servidor DNS
            
        Returns:
            True se bem-sucedido, False caso contrário
        """
        if not self._validate_dns(dns1, dns2):
            return False
        
        success, output = self._run_command(
            ["sudo", "networksetup", "-setdnsservers", self.interface, dns1, dns2]
        )
        
        if success:
            self.current_dns = (dns1, dns2)
            logger.info(f"DNS alterado para: {dns1}, {dns2}")
            return True
        else:
            logger.error(f"Erro ao alterar DNS: {output}")
            return False
    
    def rotate_dns(self) -> bool:
        """
        Rotaciona para um novo servidor DNS aleatório
        
        Returns:
            True se bem-sucedido, False caso contrário
        """
        dns1, dns2 = random.choice(DNS_SERVERS)
        
        # Evitar repetir o mesmo DNS
        if self.current_dns == (dns1, dns2):
            return self.rotate_dns()
        
        return self.set_dns(dns1, dns2)
    
    def run(self):
        """Inicia o loop de rotação de DNS"""
        self.running = True
        logger.info(f"Iniciando rotação de DNS a cada {self.interval} segundos")
        
        try:
            # Rotação inicial
            self.rotate_dns()
            
            # Loop principal
            while self.running:
                time.sleep(self.interval)
                self.rotate_dns()
        
        except KeyboardInterrupt:
            logger.info("Interrompido pelo usuário")
        except Exception as e:
            logger.error(f"Erro no loop principal: {e}")
        finally:
            self.running = False
            logger.info("DNS Changer encerrado")
    
    def run_once(self) -> bool:
        """Rotaciona DNS uma única vez"""
        logger.info("Executando rotação única de DNS")
        return self.rotate_dns()
    
    def reset_dns(self) -> bool:
        """
        Reseta DNS para configuração automática (DHCP)
        
        Returns:
            True se bem-sucedido, False caso contrário
        """
        success, output = self._run_command(
            ["sudo", "networksetup", "-setdnsservers", self.interface, "Empty"]
        )
        
        if success:
            logger.info("DNS resetado para DHCP automático")
            return True
        else:
            logger.error(f"Erro ao resetar DNS: {output}")
            return False

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def print_banner():
    """Exibe banner do aplicativo"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║          DNS Changer Eye - macOS Sequoia Edition          ║
    ║                                                           ║
    ║        Rotação Automática de Servidores DNS               ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="DNS Changer Eye para macOS - Rotação automática de DNS"
    )
    parser.add_argument(
        "-i", "--interface",
        help="Interface de rede (ex: Wi-Fi, Ethernet)",
        default=None
    )
    parser.add_argument(
        "-t", "--interval",
        type=int,
        default=300,
        help="Intervalo de rotação em segundos (padrão: 300)"
    )
    parser.add_argument(
        "-o", "--once",
        action="store_true",
        help="Rotaciona DNS uma única vez"
    )
    parser.add_argument(
        "-r", "--reset",
        action="store_true",
        help="Reseta DNS para DHCP automático"
    )
    parser.add_argument(
        "-g", "--get",
        action="store_true",
        help="Exibe configuração de DNS atual"
    )
    parser.add_argument(
        "-s", "--set",
        nargs=2,
        metavar=("DNS1", "DNS2"),
        help="Define DNS específicos (ex: -s 1.1.1.1 1.0.0.1)"
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    changer = DNSChanger(interval=args.interval, interface=args.interface)
    
    if args.get:
        current = changer.get_current_dns()
        if current:
            print(f"DNS Atual: {current[0]}, {current[1]}")
        else:
            print("Não foi possível obter configuração de DNS")
        return 0
    
    if args.reset:
        if changer.reset_dns():
            print("DNS resetado com sucesso")
            return 0
        else:
            print("Erro ao resetar DNS")
            return 1
    
    if args.set:
        if changer.set_dns(args.set[0], args.set[1]):
            print(f"DNS definido para: {args.set[0]}, {args.set[1]}")
            return 0
        else:
            print("Erro ao definir DNS")
            return 1
    
    if args.once:
        if changer.run_once():
            print("DNS rotacionado com sucesso")
            return 0
        else:
            print("Erro ao rotacionar DNS")
            return 1
    
    # Modo contínuo (padrão)
    print(f"Iniciando rotação contínua (intervalo: {args.interval}s)")
    print("Pressione Ctrl+C para parar")
    changer.run()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
