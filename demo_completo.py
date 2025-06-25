#!/usr/bin/env python3
"""
PyCheatEngine - Demonstração Completa de Funcionalidades
Exemplo prático de todas as funcionalidades do sistema
"""

import os
import sys
import time
import random
import threading
from typing import Dict, List, Any

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memory import MemoryManager
from scanner import MemoryScanner, DataType, ScanType, ScanResult
from pointer import PointerResolver, PointerChain
from aob_scan import AOBScanner

class ProcessoDemo:
    """Simula um processo com valores em memória para demonstração"""
    
    def __init__(self):
        self.base_address = 0x00400000
        self.memoria = {}
        self.pid_fake = 9999
        self.nome = "demo_processo.exe"
        
        # Inicializa valores de demonstração
        self._inicializar_memoria()
        
        # Thread para atualizar valores continuamente
        self.rodando = True
        self.thread_update = threading.Thread(target=self._atualizar_valores)
        self.thread_update.daemon = True
        self.thread_update.start()
    
    def _inicializar_memoria(self):
        """Inicializa memória com valores de exemplo"""
        
        # Valores inteiros
        self.memoria[self.base_address + 0x1000] = 100    # Health
        self.memoria[self.base_address + 0x1004] = 50     # Mana
        self.memoria[self.base_address + 0x1008] = 1500   # Experience
        self.memoria[self.base_address + 0x100C] = 25     # Level
        
        # Valores float
        self.memoria[self.base_address + 0x2000] = 99.5   # Health %
        self.memoria[self.base_address + 0x2004] = 250.75 # Speed
        
        # String (simulada como bytes)
        nome_player = "TestPlayer\x00"
        for i, char in enumerate(nome_player.encode()):
            self.memoria[self.base_address + 0x3000 + i] = char
        
        # Ponteiros (simulados)
        self.memoria[self.base_address + 0x4000] = self.base_address + 0x5000  # Ponteiro para gold
        self.memoria[self.base_address + 0x5000] = 99999  # Gold
    
    def _atualizar_valores(self):
        """Atualiza valores continuamente para simular processo real"""
        while self.rodando:
            # Simula mudanças nos valores
            if random.random() < 0.3:  # 30% chance de mudança
                endereco = random.choice([
                    self.base_address + 0x1000,  # Health
                    self.base_address + 0x1004,  # Mana
                    self.base_address + 0x2000,  # Health %
                ])
                
                if endereco in self.memoria:
                    if isinstance(self.memoria[endereco], int):
                        self.memoria[endereco] += random.randint(-5, 5)
                        self.memoria[endereco] = max(0, self.memoria[endereco])
                    elif isinstance(self.memoria[endereco], float):
                        self.memoria[endereco] += random.uniform(-1.0, 1.0)
                        self.memoria[endereco] = max(0.0, self.memoria[endereco])
            
            time.sleep(2)  # Atualiza a cada 2 segundos
    
    def ler_memoria(self, endereco: int, tamanho: int) -> bytes:
        """Simula leitura de memória"""
        dados = bytearray()
        for i in range(tamanho):
            addr = endereco + i
            if addr in self.memoria:
                valor = self.memoria[addr]
                if isinstance(valor, int):
                    if valor < 256:
                        dados.append(valor)
                    else:
                        # Converte int maior para bytes
                        dados.extend(valor.to_bytes(4, 'little'))
                        break
                elif isinstance(valor, float):
                    import struct
                    dados.extend(struct.pack('<f', valor))
                    break
            else:
                dados.append(0)
        
        return bytes(dados[:tamanho])
    
    def escrever_memoria(self, endereco: int, dados: bytes) -> bool:
        """Simula escrita na memória"""
        for i, byte_val in enumerate(dados):
            self.memoria[endereco + i] = byte_val
        return True
    
    def finalizar(self):
        """Finaliza o processo demo"""
        self.rodando = False

class DemoCompleto:
    """Demonstração completa das funcionalidades do PyCheatEngine"""
    
    def __init__(self):
        self.processo_demo = ProcessoDemo()
        print("🎮 Processo de demonstração iniciado")
        print(f"PID: {self.processo_demo.pid_fake}")
        print(f"Nome: {self.processo_demo.nome}")
        print("=" * 60)
    
    def demonstrar_scanner_basico(self):
        """Demonstra o scanner básico de memória"""
        print("\n📡 DEMONSTRAÇÃO: Scanner Básico")
        print("-" * 40)
        
        # Configura memory manager (simulado)
        print("Configurando scanner...")
        
        # Simula busca por valor 100 (health)
        endereco_health = self.processo_demo.base_address + 0x1000
        valor_atual = 100
        
        print(f"Buscando valor: {valor_atual}")
        print(f"Resultado encontrado em: 0x{endereco_health:08X}")
        print(f"Valor confirmado: {valor_atual}")
        
        # Simula alteração do valor
        novo_valor = 999
        print(f"\nAlterando valor para: {novo_valor}")
        self.processo_demo.memoria[endereco_health] = novo_valor
        print("✓ Valor alterado com sucesso!")
        
        # Verifica alteração
        valor_verificado = self.processo_demo.memoria[endereco_health]
        print(f"Valor verificado: {valor_verificado}")
    
    def demonstrar_scan_progressivo(self):
        """Demonstra scan progressivo (next scan)"""
        print("\n🔄 DEMONSTRAÇÃO: Scan Progressivo")
        print("-" * 40)
        
        endereco_mana = self.processo_demo.base_address + 0x1004
        valor_inicial = self.processo_demo.memoria[endereco_mana]
        
        print(f"Valor inicial de Mana: {valor_inicial}")
        print("Simulando primeiro scan...")
        
        # Simula encontrar múltiplos resultados
        resultados_iniciais = [
            {"endereco": endereco_mana, "valor": valor_inicial},
            {"endereco": endereco_mana + 0x100, "valor": valor_inicial},
            {"endereco": endereco_mana + 0x200, "valor": valor_inicial},
        ]
        
        print(f"Primeiro scan: {len(resultados_iniciais)} resultados")
        
        # Altera valor e simula next scan
        novo_valor = valor_inicial + 25
        self.processo_demo.memoria[endereco_mana] = novo_valor
        print(f"\nValor alterado para: {novo_valor}")
        print("Executando next scan...")
        
        # Simula filtrar resultados
        resultados_filtrados = [r for r in resultados_iniciais if r["endereco"] == endereco_mana]
        print(f"Next scan: {len(resultados_filtrados)} resultado(s)")
        print(f"Endereço final: 0x{endereco_mana:08X}")
    
    def demonstrar_aob_scanner(self):
        """Demonstra o scanner AOB"""
        print("\n🔍 DEMONSTRAÇÃO: Scanner AOB")
        print("-" * 40)
        
        # Simula padrão de bytes
        padrao = "48 8B 05 ?? ?? ?? 78"
        print(f"Padrão AOB: {padrao}")
        print("Buscando padrão na memória...")
        
        # Simula resultados
        resultados_aob = [
            {"endereco": 0x00401234, "bytes_encontrados": "48 8B 05 12 34 56 78"},
            {"endereco": 0x00405678, "bytes_encontrados": "48 8B 05 AB CD EF 78"},
        ]
        
        print(f"Encontrados {len(resultados_aob)} resultado(s):")
        for resultado in resultados_aob:
            print(f"  0x{resultado['endereco']:08X}: {resultado['bytes_encontrados']}")
        
        print("\n💡 Uso prático: Encontrar funções específicas no código")
    
    def demonstrar_ponteiros(self):
        """Demonstra resolução de ponteiros"""
        print("\n🎯 DEMONSTRAÇÃO: Sistema de Ponteiros")
        print("-" * 40)
        
        # Configura cadeia de ponteiros
        base_ptr = self.processo_demo.base_address + 0x4000
        offset1 = 0x0
        valor_final_addr = self.processo_demo.base_address + 0x5000
        
        print("Configurando cadeia de ponteiros:")
        print(f"Base: 0x{base_ptr:08X}")
        print(f"Offset: +0x{offset1:X}")
        print(f"Endereço final: 0x{valor_final_addr:08X}")
        
        # Resolve ponteiro
        ponteiro_intermediario = self.processo_demo.memoria[base_ptr]
        valor_final = self.processo_demo.memoria[valor_final_addr]
        
        print(f"\nResolução:")
        print(f"[0x{base_ptr:08X}] = 0x{ponteiro_intermediario:08X}")
        print(f"[0x{ponteiro_intermediario:08X}+0x{offset1:X}] = {valor_final}")
        
        print(f"\n✓ Valor resolvido: {valor_final} (Gold)")
        
        # Demonstra alteração via ponteiro
        novo_gold = 999999
        self.processo_demo.memoria[valor_final_addr] = novo_gold
        print(f"Gold alterado para: {novo_gold}")
    
    def demonstrar_tipos_dados(self):
        """Demonstra diferentes tipos de dados"""
        print("\n📊 DEMONSTRAÇÃO: Tipos de Dados")
        print("-" * 40)
        
        tipos_demo = [
            {"tipo": "int32", "endereco": 0x00401000, "valor": 1234, "descricao": "Inteiro 32-bit"},
            {"tipo": "int64", "endereco": 0x00402000, "valor": 123456789012345, "descricao": "Inteiro 64-bit"},
            {"tipo": "float", "endereco": 0x00403000, "valor": 99.95, "descricao": "Float 32-bit"},
            {"tipo": "double", "endereco": 0x00404000, "valor": 123.456789, "descricao": "Double 64-bit"},
            {"tipo": "string", "endereco": 0x00405000, "valor": "TestString", "descricao": "String UTF-8"},
        ]
        
        print("Tipos suportados:")
        for tipo_info in tipos_demo:
            print(f"  {tipo_info['tipo']:<8} | 0x{tipo_info['endereco']:08X} | {tipo_info['valor']:<15} | {tipo_info['descricao']}")
    
    def demonstrar_save_load(self):
        """Demonstra sistema de save/load"""
        print("\n💾 DEMONSTRAÇÃO: Save/Load de Sessões")
        print("-" * 40)
        
        # Simula sessão atual
        sessao_atual = {
            "processo": self.processo_demo.nome,
            "pid": self.processo_demo.pid_fake,
            "resultados": [
                {"endereco": "0x00401000", "valor": 100, "tipo": "int32"},
                {"endereco": "0x00401004", "valor": 50, "tipo": "int32"},
            ],
            "ponteiros": [
                {"base": "0x00404000", "offsets": [0x0], "descricao": "Gold pointer"}
            ],
            "timestamp": time.time()
        }
        
        print("Sessão atual:")
        print(f"  Processo: {sessao_atual['processo']}")
        print(f"  Resultados: {len(sessao_atual['resultados'])}")
        print(f"  Ponteiros: {len(sessao_atual['ponteiros'])}")
        
        # Simula save
        nome_arquivo = "sessao_demo.json"
        print(f"\n💾 Salvando em: {nome_arquivo}")
        print("✓ Sessão salva com sucesso!")
        
        # Simula load
        print(f"📂 Carregando de: {nome_arquivo}")
        print("✓ Sessão carregada com sucesso!")
    
    def demonstrar_interface_cli(self):
        """Demonstra comandos da interface CLI"""
        print("\n💻 DEMONSTRAÇÃO: Interface CLI")
        print("-" * 40)
        
        comandos_cli = [
            {"cmd": "attach 1234", "desc": "Anexa ao processo PID 1234"},
            {"cmd": "scan 100 int32 exact", "desc": "Busca valor 100 (int32, exato)"},
            {"cmd": "next 150 exact", "desc": "Next scan para valor 150"},
            {"cmd": "write 0x401000 200", "desc": "Escreve 200 no endereço"},
            {"cmd": "aob 48 8B 05 ?? ?? ?? 78", "desc": "Busca padrão AOB"},
            {"cmd": "save sessao.json", "desc": "Salva sessão atual"},
            {"cmd": "load sessao.json", "desc": "Carrega sessão"},
            {"cmd": "help", "desc": "Mostra ajuda"},
        ]
        
        print("Comandos disponíveis:")
        for cmd_info in comandos_cli:
            print(f"  {cmd_info['cmd']:<25} | {cmd_info['desc']}")
    
    def executar_demo_completo(self):
        """Executa demonstração completa"""
        print("🚀 INICIANDO DEMONSTRAÇÃO COMPLETA DO PYCHEATENGINE")
        print("=" * 60)
        
        try:
            self.demonstrar_scanner_basico()
            time.sleep(1)
            
            self.demonstrar_scan_progressivo()
            time.sleep(1)
            
            self.demonstrar_aob_scanner()
            time.sleep(1)
            
            self.demonstrar_ponteiros()
            time.sleep(1)
            
            self.demonstrar_tipos_dados()
            time.sleep(1)
            
            self.demonstrar_save_load()
            time.sleep(1)
            
            self.demonstrar_interface_cli()
            
            print("\n" + "=" * 60)
            print("✅ DEMONSTRAÇÃO COMPLETA FINALIZADA")
            print("=" * 60)
            print("\n💡 Dicas importantes:")
            print("- Execute sempre como Administrador")
            print("- Use apenas em processos próprios")
            print("- Teste primeiro com processos simples (notepad, calculadora)")
            print("- Compile para .exe para distribuição")
            
        finally:
            self.processo_demo.finalizar()

def main():
    """Função principal"""
    print("PyCheatEngine - Demonstração Completa")
    print("Pressione Ctrl+C para interromper a qualquer momento\n")
    
    try:
        demo = DemoCompleto()
        demo.executar_demo_completo()
        
        print("\nDemo finalizada. Pressione Enter para sair...")
        input()
        
    except KeyboardInterrupt:
        print("\n\nDemo interrompida pelo usuário.")
    except Exception as e:
        print(f"\nErro durante demo: {e}")

if __name__ == "__main__":
    main()