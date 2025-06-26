#!/usr/bin/env python3
"""
PyCheatEngine - Sistema de Engenharia Reversa e Manipulação de Memória
Arquivo principal de inicialização do programa

Este é o ponto de entrada principal do PyCheatEngine, oferecendo opções para
executar tanto a interface gráfica quanto a interface de linha de comando.

Autor: PyCheatEngine Team
Versão: 1.0.0
"""

import sys
import os
import ctypes
import platform
import argparse
from typing import Optional

def check_admin_privileges() -> bool:
    """
    Verifica se o programa está sendo executado com privilégios administrativos

    Returns:
        bool: True se tem privilégios administrativos, False caso contrário
    """
    try:
        if platform.system() == 'Windows':
            import ctypes
            try:
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except (AttributeError, OSError):
                return False
        else:
            return os.geteuid() == 0
    except (ImportError, AttributeError, OSError):
        return False

def request_admin_privileges():
    """
    Solicita privilégios administrativos para o programa
    """
    if platform.system() == "Windows":
        try:
            # Tenta reexecutar o programa como administrador
            ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                sys.executable, 
                " ".join(sys.argv), 
                None, 
                1
            )
        except Exception as e:
            print(f"Erro ao solicitar privilégios administrativos: {e}")
    else:
        print("Execute o programa com 'sudo' para obter privilégios administrativos:")
        print(f"sudo python3 {sys.argv[0]}")

def show_banner():
    """Exibe o banner do programa"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                              PyCheatEngine v1.0.0                           ║
║                    Sistema de Engenharia Reversa e Manipulação              ║
║                              de Memória em Python                           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Funcionalidades:                                                           ║
║  • Scanner de memória com múltiplos tipos de dados                          ║
║  • Resolução de cadeias de ponteiros (pointer chains)                       ║
║  • Scanner de padrões de bytes (AOB) com suporte a wildcards                ║
║  • Interface gráfica intuitiva                                              ║
║  • Interface de linha de comando                                            ║
║  • Sistema de sessões para salvar/carregar estado                           ║
║                                                                              ║
║  ⚠️  IMPORTANTE: EXECUTE COMO ADMINISTRADOR                                  ║
║      Este programa EXIGE privilégios administrativos para funcionar!        ║
║      Use com responsabilidade e apenas em processos autorizados!            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def show_main_menu() -> str:
    """
    Exibe o menu principal e retorna a escolha do usuário

    Returns:
        str: Opção escolhida pelo usuário
    """
    menu = """
Escolha uma opção:

[1] Interface Gráfica (GUI) - Recomendado para usuários iniciantes
[2] Interface de Linha de Comando (CLI) - Para usuários avançados
[3] Demo Web Interativo - Funciona perfeitamente no Replit
[4] Modo Stealth 🥷 - Funcionalidades anti-detecção
[5] Mostrar informações do sistema
[6] Verificar privilégios
[7] Ajuda
[0] Sair

"""
    print(menu)

    while True:
        try:
            choice = input("Digite sua opção (0-7): ").strip()
            if choice in ['0', '1', '2', '3', '4', '5', '6', '7']:
                return choice
            else:
                print("Opção inválida. Digite um número entre 0 e 7.")
        except (EOFError, KeyboardInterrupt):
            return '0'

# Adicionando a função handle_viewmatrix_scanner
def handle_viewmatrix_scanner():
    """Gerencia busca por ViewMatrix"""
    from viewmatrix import ViewMatrixScanner

    # Garante que memory_manager está acessível
    global memory_manager

    if not memory_manager.is_attached():
        print("❌ Nenhum processo anexado")
        return

    try:
        print("\n🎯 VIEWMATRIX SCANNER")
        print("=" * 50)

        vm_scanner = ViewMatrixScanner(memory_manager)

        print("\n1. Busca automática")
        print("2. Busca em range específico")
        print("3. Ler ViewMatrix de endereço conhecido")
        print("4. Monitorar ViewMatrix")
        print("5. Testar conversão World-to-Screen")

        choice = input("\nEscolha uma opção: ").strip()

        if choice == "1":
            # Busca automática
            print("\n🔍 Iniciando busca automática por ViewMatrix...")
            candidates = vm_scanner.scan_for_viewmatrix()

            if candidates:
                print(f"\n✅ Encontrados {len(candidates)} candidatos:")
                for i, addr in enumerate(candidates[:10]):  # Mostra apenas os primeiros 10
                    matrix = vm_scanner.read_viewmatrix(addr)
                    if matrix:
                        cam_pos = matrix.get_camera_position()
                        print(f"  {i+1}. 0x{addr:X} - Câmera: ({cam_pos[0]:.2f}, {cam_pos[1]:.2f}, {cam_pos[2]:.2f})")

                best = vm_scanner.get_best_candidate()
                if best:
                    print(f"\n🎯 Melhor candidato: 0x{best:X}")

                    # Oferecer para exportar
                    if input("\nExportar informações? (y/n): ").lower() == 'y':
                        vm_scanner.export_viewmatrix_info(f"viewmatrix_scan_{memory_manager.process_id}.json")
            else:
                print("❌ Nenhuma ViewMatrix encontrada")

        elif choice == "2":
            # Busca em range específico
            try:
                start_addr = int(input("Endereço inicial (hex, ex: 0x400000): "), 16)
                end_addr = int(input("Endereço final (hex, ex: 0x800000): "), 16)

                print(f"\n🔍 Buscando ViewMatrix entre 0x{start_addr:X} e 0x{end_addr:X}...")
                candidates = vm_scanner.scan_for_viewmatrix((start_addr, end_addr))

                if candidates:
                    print(f"\n✅ Encontrados {len(candidates)} candidatos no range especificado")
                    for addr in candidates:
                        print(f"  • 0x{addr:X}")
                else:
                    print("❌ Nenhuma ViewMatrix encontrada no range")

            except ValueError:
                print("❌ Endereços inválidos")

        elif choice == "3":
            # Ler de endereço conhecido
            try:
                addr = int(input("Endereço da ViewMatrix (hex, ex: 0x12345678): "), 16)

                matrix = vm_scanner.read_viewmatrix(addr)
                if matrix and matrix.is_valid():
                    cam_pos = matrix.get_camera_position()
                    print(f"\n✅ ViewMatrix válida encontrada!")
                    print(f"📍 Posição da câmera: ({cam_pos[0]:.3f}, {cam_pos[1]:.3f}, {cam_pos[2]:.3f})")
                    print(f"🔢 Matrix:")
                    for row in matrix.matrix:
                        print(f"  [{row[0]:8.3f} {row[1]:8.3f} {row[2]:8.3f} {row[3]:8.3f}]")
                else:
                    print("❌ ViewMatrix inválida ou não encontrada")

            except ValueError:
                print("❌ Endereço inválido")

        elif choice == "4":
            # Monitorar ViewMatrix
            try:
                addr = int(input("Endereço da ViewMatrix para monitorar (hex): "), 16)

                def matrix_callback(matrix):
                    cam_pos = matrix.get_camera_position()
                    print(f"\r📹 Câmera: ({cam_pos[0]:7.2f}, {cam_pos[1]:7.2f}, {cam_pos[2]:7.2f})", end="", flush=True)

                print("\n🎥 Iniciando monitoramento... (Ctrl+C para parar)")
                vm_scanner.monitor_viewmatrix(addr, matrix_callback)

                try:
                    while True:
                        import time
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n\n⏹️ Monitoramento parado")

            except ValueError:
                print("❌ Endereço inválido")

        elif choice == "5":
            # Testar conversão World-to-Screen
            try:
                addr = int(input("Endereço da ViewMatrix (hex): "), 16)
                matrix = vm_scanner.read_viewmatrix(addr)

                if not matrix or not matrix.is_valid():
                    print("❌ ViewMatrix inválida")
                    return

                # Entrada de coordenadas do mundo
                world_x = float(input("Coordenada X do mundo: "))
                world_y = float(input("Coordenada Y do mundo: "))
                world_z = float(input("Coordenada Z do mundo: "))

                # Dimensões da tela
                screen_w = int(input("Largura da tela (ex: 1920): ") or "1920")
                screen_h = int(input("Altura da tela (ex: 1080): ") or "1080")

                # Conversão
                screen_pos = matrix.world_to_screen((world_x, world_y, world_z), screen_w, screen_h)

                if screen_pos:
                    print(f"\n✅ Coordenadas de tela: ({screen_pos[0]}, {screen_pos[1]})")
                    print(f"📍 Posição válida na tela!")
                else:
                    print("❌ Coordenadas fora da tela ou atrás da câmera")

            except (ValueError, TypeError):
                print("❌ Valores inválidos")

        else:
            print("❌ Opção inválida")

    except Exception as e:
        print(f"❌ Erro no ViewMatrix Scanner: {e}")
        import traceback
        traceback.print_exc()

def handle_aob_scan():
    """Gerencia busca por Array of Bytes"""
    from aob_scan import AOBScanner

    # Garante que memory_manager está acessível
    global memory_manager

    if not memory_manager.is_attached():
        print("❌ Nenhum processo anexado")
        return

    try:
        print("\n🔍 AOB SCANNER")
        print("=" * 50)

        aob_scanner = AOBScanner(memory_manager)

        aob_pattern = input("Digite o padrão AOB (ex: A1 B2 ?? C3): ").strip().upper()
        start_addr_str = input("Endereço inicial (hex, ex: 0x400000, deixe em branco para padrão): ").strip()
        end_addr_str = input("Endereço final (hex, ex: 0x800000, deixe em branco para padrão): ").strip()

        start_addr = None
        end_addr = None

        if start_addr_str:
            try:
                start_addr = int(start_addr_str, 16)
            except ValueError:
                print("❌ Endereço inicial inválido")
                return

        if end_addr_str:
            try:
                end_addr = int(end_addr_str, 16)
            except ValueError:
                print("❌ Endereço final inválido")
                return

        print(f"\n🔍 Buscando padrão '{aob_pattern}'...")
        if start_addr is not None and end_addr is not None:
            print(f"  Entre 0x{start_addr:X} e 0x{end_addr:X}")

        candidates = aob_scanner.scan_aob(aob_pattern, (start_addr, end_addr) if start_addr and end_addr else None)

        if candidates:
            print(f"\n✅ Encontrados {len(candidates)} correspondências:")
            for addr in candidates[:20]:  # Limita a exibição
                print(f"  • 0x{addr:X}")
        else:
            print("❌ Nenhum resultado encontrado")

    except Exception as e:
        print(f"❌ Erro no AOB Scanner: {e}")
        import traceback
        traceback.print_exc()

def handle_memory_scan():
    """Gerencia operações de scan de memória"""
    from scanner import MemoryScanner, ScanType, DataType

    global memory_manager

    if not memory_manager.is_attached():
        print("❌ Nenhum processo anexado")
        return

    try:
        scanner = MemoryScanner(memory_manager)

        print("\n🔍 SCANNER DE MEMÓRIA")
        print("=" * 50)

        # Tipo de dado
        print("Tipos de dados disponíveis:")
        print("1. int32 (números inteiros 32-bit)")
        print("2. int64 (números inteiros 64-bit)")
        print("3. float (números decimais)")
        print("4. double (números decimais precisos)")
        print("5. string (texto)")

        data_type_choice = input("\nEscolha o tipo de dado (1-5): ").strip()
        data_type_map = {
            "1": "int32", "2": "int64", "3": "float", 
            "4": "double", "5": "string"
        }

        if data_type_choice not in data_type_map:
            print("❌ Tipo inválido")
            return

        data_type_str = data_type_map[data_type_choice]
        data_type = DataType(data_type_str)

        # Valor a buscar
        value_str = input(f"Digite o valor a buscar ({data_type_str}): ").strip()

        if not value_str:
            print("❌ Valor não pode estar vazio")
            return

        # Converte valor
        try:
            if data_type in [DataType.INT32, DataType.INT64]:
                value = int(value_str)
            elif data_type in [DataType.FLOAT, DataType.DOUBLE]:
                value = float(value_str)
            else:
                value = value_str
        except ValueError:
            print("❌ Valor inválido para o tipo escolhido")
            return

        print(f"\n🔍 Iniciando scan para {data_type_str}: {value}")

        # Executa scan
        results = scanner.first_scan(value, data_type, ScanType.EXACT)

        print(f"✅ Scan concluído: {len(results)} resultados encontrados")

        if results:
            print("\nPrimeiros 10 resultados:")
            for i, result in enumerate(results[:10]):
                print(f"  {i+1}. 0x{result.address:08X} = {result.value}")

            if len(results) > 10:
                print(f"  ... e mais {len(results) - 10} resultados")

    except Exception as e:
        print(f"❌ Erro no scan: {e}")

def handle_pointer_resolve():
    """Gerencia resolução de ponteiros"""
    from pointer import PointerResolver

    global memory_manager

    if not memory_manager.is_attached():
        print("❌ Nenhum processo anexado")
        return

    try:
        print("\n🔗 RESOLUÇÃO DE PONTEIROS")
        print("=" * 50)

        resolver = PointerResolver(memory_manager)

        base_addr_str = input("Endereço base (hex, ex: 0x400000): ").strip()
        offsets_str = input("Offsets separados por vírgula (ex: 0x10,0x20,0x30): ").strip()

        if not base_addr_str or not offsets_str:
            print("❌ Endereço base e offsets são obrigatórios")
            return

        # Converte endereço base
        try:
            if base_addr_str.startswith('0x'):
                base_addr = int(base_addr_str, 16)
            else:
                base_addr = int(base_addr_str)
        except ValueError:
            print("❌ Endereço base inválido")
            return

        # Converte offsets
        try:
            offsets = []
            for offset_str in offsets_str.split(','):
                offset_str = offset_str.strip()
                if offset_str.startswith('0x'):
                    offsets.append(int(offset_str, 16))
                else:
                    offsets.append(int(offset_str))
        except ValueError:
            print("❌ Offsets inválidos")
            return

        print(f"\n🔍 Resolvendo ponteiro...")
        print(f"Base: 0x{base_addr:X}")
        print(f"Offsets: {', '.join(f'0x{off:X}' for off in offsets)}")

        final_addr = resolver.resolve_pointer_chain(base_addr, offsets)

        if final_addr:
            print(f"✅ Endereço final: 0x{final_addr:X}")

            # Tenta ler valor
            value = memory_manager.read_int32(final_addr)
            if value is not None:
                print(f"📍 Valor atual: {value}")
            else:
                print("⚠️ Não foi possível ler o valor")
        else:
            print("❌ Falha ao resolver ponteiro")

    except Exception as e:
        print(f"❌ Erro na resolução: {e}")

def handle_edit_value():
    """Gerencia edição de valores na memória"""
    global memory_manager

    if not memory_manager.is_attached():
        print("❌ Nenhum processo anexado")
        return

    try:
        print("\n✏️ EDITAR VALOR NA MEMÓRIA")
        print("=" * 50)

        addr_str = input("Endereço (hex, ex: 0x12345678): ").strip()
        value_str = input("Novo valor: ").strip()

        if not addr_str or not value_str:
            print("❌ Endereço e valor são obrigatórios")
            return

        # Converte endereço
        try:
            if addr_str.startswith('0x'):
                address = int(addr_str, 16)
            else:
                address = int(addr_str)
        except ValueError:
            print("❌ Endereço inválido")
            return

        # Tenta converter valor como int32 primeiro
        try:
            value = int(value_str)

            print(f"\n📝 Escrevendo valor {value} no endereço 0x{address:X}...")

            if memory_manager.write_int32(address, value):
                print("✅ Valor escrito com sucesso!")

                # Verifica se foi escrito corretamente
                read_value = memory_manager.read_int32(address)
                if read_value == value:
                    print(f"✓ Verificado: {read_value}")
                else:
                    print(f"⚠️ Valor lido: {read_value} (diferente do escrito)")
            else:
                print("❌ Falha ao escrever valor")

        except ValueError:
            print("❌ Valor deve ser um número inteiro")

    except Exception as e:
        print(f"❌ Erro ao editar valor: {e}")

def handle_attach_process():
    """Gerencia anexação a processos"""
    global memory_manager

    try:
        print("\n🔗 ANEXAR A PROCESSO")
        print("=" * 50)

        # Lista processos
        print("Buscando processos...")
        processes = memory_manager.list_processes()

        print(f"\nProcessos encontrados ({len(processes)}):")
        print(f"{'PID':<8} {'Nome'}")
        print("-" * 40)

        # Mostra apenas os primeiros 20 para não poluir
        for proc in processes[:20]:
            print(f"{proc['pid']:<8} {proc['name']}")

        if len(processes) > 20:
            print(f"... e mais {len(processes) - 20} processos")

        pid_str = input("\nDigite o PID do processo: ").strip()

        if not pid_str:
            print("❌ PID não pode estar vazio")
            return

        try:
            pid = int(pid_str)
        except ValueError:
            print("❌ PID deve ser um número")
            return

        print(f"\n🔗 Tentando anexar ao processo PID {pid}...")

        if memory_manager.attach_to_process(pid):
            print(f"✅ Anexado com sucesso ao processo: {memory_manager.process_name}")
        else:
            print("❌ Falha ao anexar ao processo")
            print("   Verifique se o PID está correto e se você tem permissões")

    except Exception as e:
        print(f"❌ Erro ao anexar processo: {e}")

def handle_process_details():
    """Mostra detalhes do processo anexado"""
    global memory_manager

    if not memory_manager.is_attached():
        print("❌ Nenhum processo anexado")
        return

    try:
        print("\n📋 DETALHES DO PROCESSO")
        print("=" * 50)

        print(f"PID: {memory_manager.process_id}")
        print(f"Nome: {memory_manager.process_name}")
        print(f"Handle: {memory_manager.process_handle}")

        # Tenta obter mais informações usando psutil
        try:
            import psutil
            process = psutil.Process(memory_manager.process_id)

            print(f"Status: {process.status()}")
            print(f"CPU: {process.cpu_percent():.1f}%")

            memory_info = process.memory_info()
            print(f"Memória: {memory_info.rss / 1024 / 1024:.1f} MB")

            print(f"Threads: {process.num_threads()}")
            print(f"Criado em: {process.create_time()}")

        except ImportError:
            print("⚠️ psutil não disponível para informações detalhadas")
        except Exception as e:
            print(f"⚠️ Erro ao obter detalhes: {e}")

    except Exception as e:
        print(f"❌ Erro ao mostrar detalhes: {e}")

def main_loop():
    """Laço principal do programa"""
    while True:
        choice = show_main_menu()

        if choice == '0':
            print("\nObrigado por usar o PyCheatEngine!")
            break
        elif choice == '1':
            run_gui()
        elif choice == '2':
            run_cli()
        elif choice == '3':
            run_web_demo()
        elif choice == '4':
            run_stealth_mode()
        elif choice == '5':
            show_system_info()
        elif choice == '6':
            is_admin = check_admin_privileges()
            print(f"\nPrivilégios Administrativos: {'✓ Sim' if is_admin else '✗ Não'}")
            if not is_admin:
                print("Execute o programa como administrador para melhor funcionalidade.")
        elif choice == '7':
            show_help()

        # Pausa antes de mostrar o menu novamente
        if choice != '0':
            input("\nPressione Enter para continuar...")

if __name__ == "__main__":
    # Define o título da janela do console no Windows
    if platform.system() == "Windows":
        try:
            ctypes.windll.kernel32.SetConsoleTitleW("PyCheatEngine v1.0.0")
        except:
            pass

    # Cria instância global do MemoryManager
    from memory import MemoryManager
    memory_manager = MemoryManager()

    # Inicia o laço principal
    main_loop()

    print("\n👋 Obrigado por usar o PyCheatEngine!")