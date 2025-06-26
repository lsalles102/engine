#!/usr/bin/env python3
"""
Interface Gráfica Principal do PyCheatEngine
GUI completa estilo Cheat Engine com funcionalidades stealth
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import time
import json
from typing import List, Optional, Dict, Any

# Imports do PyCheatEngine
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory import MemoryManager
from scanner import MemoryScanner, ScanType, DataType, ScanResult
from stealth import create_stealth_memory_manager, AntiDebugger, demo_stealth_capabilities
from stealth_config import get_stealth_config, apply_preset, STEALTH_PRESETS

class PyCheatEngineGUI:
    """Interface gráfica principal do PyCheatEngine"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PyCheatEngine v1.0.0 - Memory Scanner & Stealth")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2b2b2b')

        # Componentes principais
        self.memory_manager = None
        self.scanner = None
        self.stealth_enabled = False
        self.stealth_level = 0
        self.anti_debugger = None

        # Variáveis de interface
        self.scan_results = []
        self.is_scanning = False
        self.scan_progress = tk.DoubleVar()

        # Verifica privilégios administrativos
        self.check_admin_privileges()

        # Configuração de estilo
        self.setup_styles()

        # Interface
        self.create_menu()
        self.create_main_interface()
        self.create_status_bar()

        # Inicia com MemoryManager padrão
        self.memory_manager = MemoryManager()
        self.scanner = MemoryScanner(self.memory_manager)

        self.update_interface_state()

    def check_admin_privileges(self):
        """Verifica e alerta sobre privilégios administrativos"""
        import platform
        import ctypes

        try:
            if platform.system() == 'Windows':
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                is_admin = os.geteuid() == 0
        except:
            is_admin = False

        if not is_admin:
            # Mostra aviso na interface
            self.show_admin_warning()

    def show_admin_warning(self):
        """Mostra aviso sobre privilégios administrativos"""
        def show_warning():
            result = messagebox.askyesno(
                "⚠️ Privilégios Administrativos",
                "PyCheatEngine não está sendo executado como administrador!\n\n" +
                "Para anexar processos corretamente, privilégios administrativos são necessários.\n\n" +
                "Deseja executar como administrador?\n\n" +
                "• Clique 'Sim' para reiniciar como administrador\n" +
                "• Clique 'Não' para continuar (funcionalidade limitada)",
                icon='warning'
            )

            if result:
                self.request_admin_and_restart()

        # Agenda para depois da inicialização
        self.root.after(1000, show_warning)

    def request_admin_and_restart(self):
        """Solicita privilégios administrativos e reinicia"""
        try:
            import platform
            import ctypes
            import sys

            if platform.system() == "Windows":
                # Reconstrói argumentos
                args = ' '.join(sys.argv)

                # Executa como administrador
                ctypes.windll.shell32.ShellExecuteW(
                    None, 
                    "runas", 
                    sys.executable, 
                    args, 
                    None, 
                    1
                )

                # Fecha a instância atual
                self.root.quit()
                sys.exit(0)
            else:
                messagebox.showinfo(
                    "Privilégios Administrativos",
                    "Execute o programa com 'sudo' no Linux:\n\n" +
                    f"sudo python3 {sys.argv[0]}"
                )
        except Exception as e:
            messagebox.showerror(
                "Erro",
                f"Erro ao solicitar privilégios administrativos:\n{e}\n\n" +
                "Execute manualmente como administrador."
            )

    def setup_styles(self):
        """Configura estilos da interface"""
        style = ttk.Style()
        style.theme_use('clam')

        # Cores escuras estilo Cheat Engine
        style.configure('Dark.TFrame', background='#2b2b2b')
        style.configure('Dark.TLabel', background='#2b2b2b', foreground='white')
        style.configure('Dark.TButton', background='#404040', foreground='white')
        style.configure('Dark.TEntry', fieldbackground='#404040', foreground='white')
        style.configure('Stealth.TLabel', background='#2b2b2b', foreground='#00ff00')
        style.configure('Error.TLabel', background='#2b2b2b', foreground='#ff4444')
        style.configure('Success.TLabel', background='#2b2b2b', foreground='#44ff44')

    def create_menu(self):
        """Cria menu principal"""
        menubar = tk.Menu(self.root, bg='#404040', fg='white')
        self.root.config(menu=menubar)

        # Menu File
        file_menu = tk.Menu(menubar, tearoff=0, bg='#404040', fg='white')
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Anexar Processo", command=self.attach_process_dialog)
        file_menu.add_command(label="Desanexar", command=self.detach_process)
        file_menu.add_separator()
        file_menu.add_command(label="Executar como Administrador", command=self.request_admin_and_restart)
        file_menu.add_separator()
        file_menu.add_command(label="Exportar Resultados", command=self.export_results)
        file_menu.add_command(label="Importar Resultados", command=self.import_results)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.root.quit)

        # Menu Stealth
        stealth_menu = tk.Menu(menubar, tearoff=0, bg='#404040', fg='white')
        menubar.add_cascade(label="🥷 Stealth", menu=stealth_menu)
        stealth_menu.add_command(label="Ativar Stealth", command=self.toggle_stealth)
        stealth_menu.add_command(label="Configurar Nível", command=self.configure_stealth_level)
        stealth_menu.add_command(label="Aplicar Preset", command=self.apply_stealth_preset)
        stealth_menu.add_command(label="Modo Driver", command=self.toggle_driver_mode)
        stealth_menu.add_separator()
        stealth_menu.add_command(label="Monitor Anti-Debug", command=self.toggle_anti_debug)
        stealth_menu.add_command(label="Demo Capacidades", command=self.demo_stealth)

        # Menu Tools
        tools_menu = tk.Menu(menubar, tearoff=0, bg='#404040', fg='white')
        menubar.add_cascade(label="Ferramentas", menu=tools_menu)
        tools_menu.add_command(label="AOB Scanner", command=self.open_aob_scanner)
        tools_menu.add_command(label="ViewMatrix Scanner", command=self.open_viewmatrix_scanner)
        tools_menu.add_command(label="Pointer Resolver", command=self.open_pointer_resolver)

        # Menu Help
        help_menu = tk.Menu(menubar, tearoff=0, bg='#404040', fg='white')
        menubar.add_cascade(label="Ajuda", menu=help_menu)
        help_menu.add_command(label="Sobre", command=self.show_about)

    def create_main_interface(self):
        """Cria interface principal"""
        # Frame principal
        main_frame = ttk.Frame(self.root, style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Frame superior - Processo e Stealth
        top_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        top_frame.pack(fill=tk.X, pady=(0, 5))

        self.create_process_frame(top_frame)
        self.create_stealth_frame(top_frame)

        # Frame principal com painéis
        content_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Painel esquerdo - Scanner
        left_frame = ttk.LabelFrame(content_frame, text="Scanner de Memória", style='Dark.TFrame')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 2))

        self.create_scanner_frame(left_frame)

        # Painel direito - Resultados e Edição
        right_frame = ttk.LabelFrame(content_frame, text="Resultados e Edição", style='Dark.TFrame')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(2, 0))

        self.create_results_frame(right_frame)

    def create_process_frame(self, self, parent):
        """Cria frame de processo"""
        process_frame = ttk.LabelFrame(parent, text="Processo", style='Dark.TFrame')
        process_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # Informações do processo
        info_frame = ttk.Frame(process_frame, style='Dark.TFrame')
        info_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(info_frame, text="Processo:", style='Dark.TLabel').pack(side=tk.LEFT)
        self.process_info_label = ttk.Label(info_frame, text="Nenhum processo anexado", style='Error.TLabel')
        self.process_info_label.pack(side=tk.LEFT, padx=(5, 0))

        # Botões
        button_frame = ttk.Frame(process_frame, style='Dark.TFrame')
        button_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        ttk.Button(button_frame, text="Anexar Processo", command=self.attach_process_dialog, style='Dark.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Atualizar", command=self.update_process_info, style='Dark.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Teste", command=self.test_attachment, style='Dark.TButton').pack(side=tk.LEFT)

    def create_stealth_frame(self, parent):
        """Cria frame de stealth"""
        stealth_frame = ttk.LabelFrame(parent, text="🥷 Stealth Mode", style='Dark.TFrame')
        stealth_frame.pack(side=tk.RIGHT, fill=tk.X, padx=(5, 0))

        # Status stealth
        status_frame = ttk.Frame(stealth_frame, style='Dark.TFrame')
        status_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(status_frame, text="Status:", style='Dark.TLabel').pack(side=tk.LEFT)
        self.stealth_status_label = ttk.Label(status_frame, text="DESATIVADO", style='Error.TLabel')
        self.stealth_status_label.pack(side=tk.LEFT, padx=(5, 0))

        ttk.Label(status_frame, text="Nível:", style='Dark.TLabel').pack(side=tk.LEFT, padx=(10, 0))
        self.stealth_level_label = ttk.Label(status_frame, text="0", style='Dark.TLabel')
        self.stealth_level_label.pack(side=tk.LEFT, padx=(5, 0))

        # Botões stealth
        button_frame = ttk.Frame(stealth_frame, style='Dark.TFrame')
        button_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        ttk.Button(button_frame, text="Ativar", command=self.toggle_stealth, style='Dark.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Config", command=self.configure_stealth_level, style='Dark.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Driver", command=self.toggle_driver_mode, style='Dark.TButton').pack(side=tk.LEFT)

    def create_scanner_frame(self, parent):
        """Cria frame do scanner"""
        # Configurações de scan
        config_frame = ttk.LabelFrame(parent, text="Configurações de Scan", style='Dark.TFrame')
        config_frame.pack(fill=tk.X, padx=5, pady=5)

        # Tipo de dado
        type_frame = ttk.Frame(config_frame, style='Dark.TFrame')
        type_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(type_frame, text="Tipo:", style='Dark.TLabel').pack(side=tk.LEFT)
        self.data_type_var = tk.StringVar(value="int32")
        data_type_combo = ttk.Combobox(type_frame, textvariable=self.data_type_var, 
                                      values=["int32", "int64", "float", "double", "string"], 
                                      state="readonly", width=10)
        data_type_combo.pack(side=tk.LEFT, padx=(5, 0))

        # Tipo de scan
        scan_frame = ttk.Frame(config_frame, style='Dark.TFrame')
        scan_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(scan_frame, text="Scan:", style='Dark.TLabel').pack(side=tk.LEFT)
        self.scan_type_var = tk.StringVar(value="exact")
        scan_type_combo = ttk.Combobox(scan_frame, textvariable=self.scan_type_var,
                                      values=["exact", "greater_than", "less_than", "increased", 
                                             "decreased", "changed", "unchanged"], 
                                      state="readonly", width=12)
        scan_type_combo.pack(side=tk.LEFT, padx=(5, 0))

        # Valor de busca
        value_frame = ttk.Frame(config_frame, style='Dark.TFrame')
        value_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(value_frame, text="Valor:", style='Dark.TLabel').pack(side=tk.LEFT)
        self.search_value_var = tk.StringVar()
        value_entry = ttk.Entry(value_frame, textvariable=self.search_value_var, style='Dark.TEntry', width=20)
        value_entry.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)

        # Botões de scan
        button_frame = ttk.Frame(config_frame, style='Dark.TFrame')
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        self.first_scan_btn = ttk.Button(button_frame, text="First Scan", command=self.first_scan, style='Dark.TButton')
        self.first_scan_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.next_scan_btn = ttk.Button(button_frame, text="Next Scan", command=self.next_scan, style='Dark.TButton', state='disabled')
        self.next_scan_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.cancel_btn = ttk.Button(button_frame, text="Cancelar", command=self.cancel_scan, style='Dark.TButton', state='disabled')
        self.cancel_btn.pack(side=tk.LEFT)

        # Progresso
        progress_frame = ttk.Frame(config_frame, style='Dark.TFrame')
        progress_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.scan_progress, maximum=100)
        self.progress_bar.pack(fill=tk.X)

        self.progress_label = ttk.Label(progress_frame, text="Pronto", style='Dark.TLabel')
        self.progress_label.pack()

        # Log de atividades
        log_frame = ttk.LabelFrame(parent, text="Log de Atividades", style='Dark.TFrame')
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, bg='#1e1e1e', fg='#00ff00', 
                                                 insertbackground='white', wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def create_results_frame(self, parent):
        """Cria frame de resultados"""
        # Lista de resultados
        list_frame = ttk.LabelFrame(parent, text="Resultados do Scan", style='Dark.TFrame')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Treeview para resultados
        columns = ("Endereço", "Valor", "Anterior", "Tipo")
        self.results_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)

        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=120)

        # Scrollbar para treeview
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)

        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        # Bind eventos
        self.results_tree.bind('<Double-1>', self.edit_selected_value)

        # Frame de edição
        edit_frame = ttk.LabelFrame(parent, text="Editar Valor", style='Dark.TFrame')
        edit_frame.pack(fill=tk.X, padx=5, pady=5)

        # Endereço
        addr_frame = ttk.Frame(edit_frame, style='Dark.TFrame')
        addr_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(addr_frame, text="Endereço:", style='Dark.TLabel').pack(side=tk.LEFT)
        self.edit_address_var = tk.StringVar()
        ttk.Entry(addr_frame, textvariable=self.edit_address_var, style='Dark.TEntry', width=15).pack(side=tk.LEFT, padx=(5, 0))

        # Novo valor
        value_frame = ttk.Frame(edit_frame, style='Dark.TFrame')
        value_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(value_frame, text="Novo Valor:", style='Dark.TLabel').pack(side=tk.LEFT)
        self.edit_value_var = tk.StringVar()
        ttk.Entry(value_frame, textvariable=self.edit_value_var, style='Dark.TEntry', width=15).pack(side=tk.LEFT, padx=(5, 0))

        # Botões de edição
        edit_button_frame = ttk.Frame(edit_frame, style='Dark.TFrame')
        edit_button_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(edit_button_frame, text="Escrever", command=self.write_value, style='Dark.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(edit_button_frame, text="Atualizar Resultados", command=self.update_results, style='Dark.TButton').pack(side=tk.LEFT)

        # Informações de resultados
        info_frame = ttk.Frame(edit_frame, style='Dark.TFrame')
        info_frame.pack(fill=tk.X, padx=5, pady=2)

        self.results_info_label = ttk.Label(info_frame, text="0 resultados", style='Dark.TLabel')
        self.results_info_label.pack(side=tk.LEFT)

    def create_status_bar(self):
        """Cria barra de status"""
        status_frame = ttk.Frame(self.root, style='Dark.TFrame')
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = ttk.Label(status_frame, text="ProcessDark pronto", style='Dark.TLabel')
        self.status_label.pack(side=tk.LEFT, padx=5, pady=2)

        # Status stealth na barra
        self.stealth_status_bar = ttk.Label(status_frame, text="Stealth: OFF", style='Error.TLabel')
        self.stealth_status_bar.pack(side=tk.RIGHT, padx=5, pady=2)

    def log_message(self, message: str, level: str = "info"):
        """Adiciona mensagem ao log"""
        timestamp = time.strftime("%H:%M:%S")

        if level == "error":
            color_prefix = "🔴"
        elif level == "success":
            color_prefix = "✅"
        elif level == "warning":
            color_prefix = "⚠️"
        elif level == "stealth":
            color_prefix = "🥷"
        else:
            color_prefix = "ℹ️"

        log_message = f"[{timestamp}] {color_prefix} {message}\n"

        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def attach_process_dialog(self):
        """Abre diálogo para anexar processo"""
        dialog = ProcessSelectionDialog(self.root, self.memory_manager)
        if dialog.result:
            self.attach_to_process(dialog.result)

    def attach_to_process(self, process_id: int):
        """Anexa a um processo"""
        try:
            self.log_message(f"🔗 Iniciando anexação ao processo PID {process_id}...")

            # Verifica se o processo existe
            process_name = f"PID_{process_id}"
            try:
                import psutil
                process = psutil.Process(process_id)
                process_name = process.name()
                status = process.status()
                self.log_message(f"✓ Processo encontrado: {process_name} (Status: {status})")

                # Verifica se processo não é zombie
                if status == psutil.STATUS_ZOMBIE:
                    self.log_message(f"❌ Processo {process_id} é um zombie", "error")
                    messagebox.showerror("Erro", f"O processo {process_name} (PID: {process_id}) é um processo zombie.\n\nEscolha outro processo.")
                    return

            except psutil.NoSuchProcess:
                self.log_message(f"❌ Processo {process_id} não existe", "error")
                messagebox.showerror("Erro", f"Processo PID {process_id} não foi encontrado.\n\nO processo pode ter sido encerrado.\nTente atualizar a lista de processos.")
                return
            except psutil.AccessDenied:
                self.log_message(f"⚠️ Acesso negado ao processo {process_id}, tentando anexar mesmo assim...", "warning")
                process_name = f"Process_{process_id}"
            except Exception as e:
                self.log_message(f"⚠️ Erro ao verificar processo {process_id}: {e}", "warning")

            # Mostra progresso
            self.log_message("🔄 Tentando anexar com diferentes níveis de acesso...")
            self.root.update_idletasks()

            # Tenta anexar
            anexacao_sucesso = self.memory_manager.attach_to_process(process_id)

            if anexacao_sucesso:
                # Verifica se realmente anexou
                anexacao_confirmada = self.memory_manager.is_attached()
                self.log_message(f"🔍 Verificação de anexação: {anexacao_confirmada}")

                if anexacao_confirmada and self.memory_manager.process_id == process_id:
                    # SUCESSO CONFIRMADO
                    self.scanner = MemoryScanner(self.memory_manager)
                    self.scanner.set_progress_callback(self.update_scan_progress)

                    # Se stealth estiver ativo, recria com stealth
                    if self.stealth_enabled:
                        self.log_message("🥷 Reativando modo stealth...", "stealth")
                        try:
                            self.enable_stealth_mode()
                        except:
                            pass

                    self.log_message(f"✅ ANEXAÇÃO CONFIRMADA! PID {process_id} ({process_name})", "success")

                    # FORÇAR ATUALIZAÇÃO DA INTERFACE IMEDIATAMENTE
                    self.process_info_label.configure(text=f"✅ PID: {process_id} ({process_name})", style='Success.TLabel')
                    self.status_label.configure(text=f"✅ Anexado ao processo {process_id}")

                    # Força repaint imediato
                    self.process_info_label.update()
                    self.status_label.update()
                    self.root.update()

                    # Atualiza estado da interface múltiplas vezes
                    for i in range(5):
                        self.update_interface_state()
                        self.root.update_idletasks()
                        self.root.update()
                        import time
                        time.sleep(0.05)

                    self.log_message("✅ Interface atualizada com sucesso!", "success")

                    # Mensagem de sucesso
                    success_msg = f"✅ Anexação bem-sucedida!\n\n"
                    success_msg += f"📋 PID: {process_id}\n"
                    success_msg += f"📝 Nome: {process_name}\n"
                    success_msg += f"🔧 Status: Pronto para scan"
                    if self.stealth_enabled:
                        success_msg += f"\n🥷 Modo Stealth: Ativo"

                    # Agenda mensagem para depois da atualização da interface
                    self.root.after(200, lambda: messagebox.showinfo("Anexação Bem-Sucedida", success_msg))
                    return

            # Se chegou aqui, anexação falhou
            self.log_message(f"❌ FALHA na anexação ao processo {process_id}", "error")

            # Força limpeza do estado
            try:
                self.memory_manager.process_id = None
                if hasattr(self.memory_manager, 'process_handle'):
                    self.memory_manager.process_handle = None
            except:
                pass

            # Força atualização da interface para mostrar desanexado
            self.process_info_label.configure(text="❌ Nenhum processo anexado", style='Error.TLabel')
            self.status_label.configure(text="ProcessDark pronto")
            self.update_interface_state()

            error_msg = f"❌ Falha ao anexar ao processo:\n\n"
            error_msg += f"📋 PID: {process_id}\n"
            error_msg += f"📝 Nome: {process_name}\n\n"
            error_msg += f"🔧 Possíveis soluções:\n\n"
            error_msg += f"1. ⚡ Execute como administrador\n"
            error_msg += f"2. 🛡️ Processo pode estar protegido\n"
            error_msg += f"3. 💻 Processo pode ter encerrado\n"
            error_msg += f"4. 🔒 Antivírus pode estar bloqueando\n\n"
            error_msg += f"💡 Tente outro processo ou reinicie como admin."

            messagebox.showerror("Erro de Anexação", error_msg)

        except Exception as e:
            self.log_message(f"❌ Erro inesperado ao anexar processo: {e}", "error")
            import traceback
            traceback.print_exc()

            # Limpa estado em caso de erro
            try:
                self.memory_manager.process_id = None
                if hasattr(self.memory_manager, 'process_handle'):
                    self.memory_manager.process_handle = None
            except:
                pass

            # Força interface para estado desanexado
            self.process_info_label.configure(text="❌ Nenhum processo anexado", style='Error.TLabel')
            self.status_label.configure(text="ProcessDark pronto")
            self.update_interface_state()

            error_msg = f"❌ Erro inesperado durante anexação:\n\n{e}\n\n"
            error_msg += f"🔧 Tente:\n"
            error_msg += f"1. Reiniciar o PyCheatEngine\n"
            error_msg += f"2. Executar como administrador\n"
            error_msg += f"3. Escolher outro processo"

            messagebox.showerror("Erro Inesperado", error_msg)

    def detach_process(self):
        """Desanexa do processo atual"""
        if self.memory_manager and self.memory_manager.is_attached():
            self.memory_manager.close()
            self.scan_results.clear()
            self.update_results_display()
            self.log_message("Processo desanexado", "info")
            self.update_interface_state()

    def toggle_stealth(self):
        """Ativa/desativa modo stealth"""
        if not self.stealth_enabled:
            self.enable_stealth_mode()
        else:
            self.disable_stealth_mode()

    def enable_stealth_mode(self):
        """Ativa modo stealth"""
        try:
            # Substitui memory_manager por versão stealth
            old_process_id = None
            if self.memory_manager and self.memory_manager.is_attached():
                old_process_id = self.memory_manager.process_id
                self.memory_manager.close()

            # Cria novo memory manager com stealth
            self.memory_manager = create_stealth_memory_manager()
            self.scanner = MemoryScanner(self.memory_manager)
            self.scanner.set_progress_callback(self.update_scan_progress)

            # Reanexa se havia processo
            if old_process_id:
                self.memory_manager.attach_to_process(old_process_id)

            # Ativa stealth
            self.memory_manager.enable_stealth(True)
            if self.stealth_level > 0:
                config = get_stealth_config()
                config.set_stealth_level(self.stealth_level)

            self.stealth_enabled = True
            self.log_message("Modo Stealth ATIVADO", "stealth")
            self.update_stealth_display()

        except Exception as e:
            self.log_message(f"Erro ao ativar stealth: {e}", "error")

    def disable_stealth_mode(self):
        """Desativa modo stealth"""
        try:
            old_process_id = None
            if self.memory_manager and self.memory_manager.is_attached():
                old_process_id = self.memory_manager.process_id
                self.memory_manager.close()

            # Volta para memory manager normal
            self.memory_manager = MemoryManager()
            self.scanner = MemoryScanner(self.memory_manager)
            self.scanner.set_progress_callback(self.update_scan_progress)

            if old_process_id:
                self.memory_manager.attach_to_process(old_process_id)

            self.stealth_enabled = False
            self.log_message("Modo Stealth DESATIVADO", "info")
            self.update_stealth_display()

        except Exception as e:
            self.log_message(f"Erro ao desativar stealth: {e}", "error")

    def configure_stealth_level(self):
        """Configura nível de stealth"""
        dialog = StealthLevelDialog(self.root, self.stealth_level)
        if dialog.result is not None:
            self.stealth_level = dialog.result

            if self.stealth_enabled and hasattr(self.memory_manager, 'enable_stealth'):
                config = get_stealth_config()
                config.set_stealth_level(self.stealth_level)

            self.log_message(f"Nível stealth definido para {self.stealth_level}", "stealth")
            self.update_stealth_display()

    def apply_stealth_preset(self):
        """Aplica preset de stealth"""
        dialog = StealthPresetDialog(self.root)
        if dialog.result:
            if apply_preset(dialog.result):
                self.log_message(f"Preset '{dialog.result}' aplicado", "stealth")
                if self.stealth_enabled:
                    self.enable_stealth_mode()
            else:
                self.log_message(f"Falha ao aplicar preset '{dialog.result}'", "error")

    def toggle_driver_mode(self):
        """Ativa/desativa modo driver"""
        if self.stealth_enabled and hasattr(self.memory_manager, 'enable_driver_mode'):
            current_status = getattr(self.memory_manager, 'use_driver', False)
            self.memory_manager.enable_driver_mode(not current_status)

            status = "ATIVADO" if not current_status else "DESATIVADO"
            self.log_message(f"Modo Driver {status}", "stealth")
        else:
            self.log_message("Ative o modo stealth primeiro", "warning")

    def toggle_anti_debug(self):
        """Ativa/desativa monitor anti-debug"""
        if not self.anti_debugger:
            from stealth import AntiDebugger
            self.anti_debugger = AntiDebugger()

            def debug_callback():
                self.log_message("⚠️ DEBUGGER DETECTADO!", "error")

            self.anti_debugger.add_debug_callback(debug_callback)
            self.anti_debugger.start_monitoring()
            self.log_message("Monitor Anti-Debug ATIVADO", "stealth")
        else:
            self.anti_debugger.stop_monitoring()
            self.anti_debugger = None
            self.log_message("Monitor Anti-Debug DESATIVADO", "info")

    def demo_stealth(self):
        """Demonstra capacidades stealth"""
        try:
            self.log_message("Executando demonstração stealth...", "stealth")

            # Executa em thread separada para não travar interface
            def run_demo():
                demo_stealth_capabilities()

            demo_thread = threading.Thread(target=run_demo, daemon=True)
            demo_thread.start()

        except Exception as e:
            self.log_message(f"Erro na demonstração: {e}", "error")

    def first_scan(self):
        """Executa primeiro scan"""
        if not self.memory_manager or not self.memory_manager.is_attached():
            messagebox.showerror("Erro", "Anexe a um processo primeiro!")
            return

        value_str = self.search_value_var.get().strip()
        if not value_str:
            messagebox.showerror("Erro", "Digite um valor para buscar!")
            return

        try:
            # Converte valor baseado no tipo
            data_type = DataType(self.data_type_var.get())
            scan_type = ScanType(self.scan_type_var.get())

            if data_type in [DataType.INT32, DataType.INT64]:
                value = int(value_str)
            elif data_type in [DataType.FLOAT, DataType.DOUBLE]:
                value = float(value_str)
            else:
                value = value_str

            self.is_scanning = True
            self.first_scan_btn.configure(state='disabled')
            self.cancel_btn.configure(state='normal')

            self.log_message(f"Iniciando first scan: {value} ({data_type.value})", "info")

            # Executa scan em thread separada
            def run_scan():
                try:
                    results = self.scanner.first_scan(value, data_type, scan_type)
                    self.scan_results = results

                    self.root.after(0, lambda: self.scan_completed(len(results)))

                except Exception as e:
                    self.root.after(0, lambda: self.scan_error(str(e)))

            scan_thread = threading.Thread(target=run_scan, daemon=True)
            scan_thread.start()

        except ValueError as e:
            messagebox.showerror("Erro", f"Valor inválido: {e}")
            self.is_scanning = False

    def next_scan(self):
        """Executa próximo scan"""
        if not self.scan_results:
            messagebox.showerror("Erro", "Execute um first scan primeiro!")
            return

        value_str = self.search_value_var.get().strip()
        scan_type = ScanType(self.scan_type_var.get())

        # Para alguns tipos de scan, valor é opcional
        value = None
        if scan_type in [ScanType.EXACT, ScanType.GREATER_THAN, ScanType.LESS_THAN]:
            if not value_str:
                messagebox.showerror("Erro", "Digite um valor para este tipo de scan!")
                return

            try:
                data_type = DataType(self.data_type_var.get())
                if data_type in [DataType.INT32, DataType.INT64]:
                    value = int(value_str)
                elif data_type in [DataType.FLOAT, DataType.DOUBLE]:
                    value = float(value_str)
                else:
                    value = value_str
            except ValueError as e:
                messagebox.showerror("Erro", f"Valor inválido: {e}")
                return

        self.is_scanning = True
        self.next_scan_btn.configure(state='disabled')
        self.cancel_btn.configure(state='normal')

        self.log_message(f"Iniciando next scan: {scan_type.value}", "info")

        def run_next_scan():
            try:
                results = self.scanner.next_scan(value, scan_type)
                self.scan_results = results

                self.root.after(0, lambda: self.scan_completed(len(results)))

            except Exception as e:
                self.root.after(0, lambda: self.scan_error(str(e)))

        scan_thread = threading.Thread(target=run_next_scan, daemon=True)
        scan_thread.start()

    def cancel_scan(self):
        """Cancela scan atual"""
        if self.scanner:
            self.scanner.cancel_scan()
        self.is_scanning = False
        self.log_message("Scan cancelado", "warning")
        self.reset_scan_buttons()

    def scan_completed(self, result_count: int):
        """Callback quando scan completa"""
        self.is_scanning = False
        self.log_message(f"Scan completo: {result_count} resultados", "success")
        self.update_results_display()
        self.reset_scan_buttons()
        self.scan_progress.set(100)
        self.progress_label.configure(text=f"Concluído: {result_count} resultados")

    def scan_error(self, error_msg: str):
        """Callback quando scan tem erro"""
        self.is_scanning = False
        self.log_message(f"Erro no scan: {error_msg}", "error")
        self.reset_scan_buttons()
        messagebox.showerror("Erro no Scan", error_msg)

    def reset_scan_buttons(self):
        """Reseta estado dos botões de scan"""
        self.first_scan_btn.configure(state='normal')
        self.next_scan_btn.configure(state='normal' if self.scan_results else 'disabled')
        self.cancel_btn.configure(state='disabled')

    def update_scan_progress(self, progress: float):
        """Atualiza progresso do scan"""
        self.scan_progress.set(progress)
        self.progress_label.configure(text=f"Escaneando... {progress:.1f}%")
        self.root.update_idletasks()

    def update_results_display(self):
        """Atualiza exibição dos resultados"""
        # Limpa treeview
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Adiciona resultados (máximo 100 for performance)
        display_count = min(len(self.scan_results), 1000)

        for i, result in enumerate(self.scan_results[:display_count]):
            address = f"0x{result.address:08X}"
            value = str(result.value)
            previous = str(result.previous_value) if result.previous_value is not None else ""
            data_type = result.data_type.value

            self.results_tree.insert('', tk.END, values=(address, value, previous, data_type))

        # Atualiza informações
        total_results = len(self.scan_results)
        if total_results > 1000:
            info_text = f"{total_results} resultados (mostrando primeiros 1000)"
        else:
            info_text = f"{total_results} resultados"

        self.results_info_label.configure(text=info_text)

    def edit_selected_value(self, event):
        """Edita valor selecionado"""
        selection = self.results_tree.selection()
        if not selection:
            return

        item = self.results_tree.item(selection[0])
        values = item['values']

        if values:
            self.edit_address_var.set(values[0])  # Endereço
            self.edit_value_var.set(values[1])    # Valor atual

    def write_value(self):
        """Escreve novo valor na memória"""
        if not self.memory_manager or not self.memory_manager.is_attached():
            messagebox.showerror("Erro", "Nenhum processo anexado!")
            return

        address_str = self.edit_address_var.get().strip()
        value_str = self.edit_value_var.get().strip()

        if not address_str or not value_str:
            messagebox.showerror("Erro", "Preencha endereço e valor!")
            return

        try:
            # Converte endereço
            if address_str.startswith('0x'):
                address = int(address_str, 16)
            else:
                address = int(address_str)

            # Converte valor baseado no tipo atual
            data_type = DataType(self.data_type_var.get())

            if data_type == DataType.INT32:
                value = int(value_str)
                success = self.memory_manager.write_int32(address, value)
            elif data_type == DataType.INT64:
                value = int(value_str)
                success = self.memory_manager.write_int64(address, value)
            elif data_type == DataType.FLOAT:
                value = float(value_str)
                success = self.memory_manager.write_float(address, value)
            elif data_type == DataType.DOUBLE:
                value = float(value_str)
                success = self.memory_manager.write_double(address, value)
            elif data_type == DataType.STRING:
                success = self.memory_manager.write_string(address, value_str)
            else:
                messagebox.showerror("Erro", "Tipo de dado não suportado para escrita!")
                return

            if success:
                self.log_message(f"Valor escrito: 0x{address:X} = {value_str}", "success")

                # Verifica se foi escrito corretamente
                if data_type == DataType.INT32:
                    read_value = self.memory_manager.read_int32(address)
                elif data_type == DataType.FLOAT:
                    read_value = self.memory_manager.read_float(address)
                else:
                    read_value = None

                if read_value is not None:
                    self.log_message(f"Verificação: valor lido = {read_value}", "info")
            else:
                self.log_message(f"Falha ao escrever valor em 0x{address:X}", "error")

        except ValueError as e:
            messagebox.showerror("Erro", f"Valor inválido: {e}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao escrever: {e}")

    def update_results(self):
        """Atualiza valores dos resultados"""
        if not self.scanner:
            return

        self.log_message("Atualizando valores dos resultados...", "info")

        def update_worker():
            try:
                self.scanner.update_results()
                self.root.after(0, lambda: self.update_results_completed())
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"Erro ao atualizar: {e}", "error"))

        update_thread = threading.Thread(target=update_worker, daemon=True)
        update_thread.start()

    def update_results_completed(self):
        """Callback quando atualização completa"""
        self.update_results_display()
        self.log_message("Resultados atualizados", "success")

    def update_interface_state(self):
        """Atualiza estado da interface"""
        print(f"🔄 Atualizando interface state...")

        # Verificação mais rigorosa do estado de anexação
        attached = False
        if self.memory_manager is not None:
            attached = (self.memory_manager.process_id is not None and 
                       self.memory_manager.is_attached())

        print(f"   - Memory manager existe: {self.memory_manager is not None}")
        if self.memory_manager:
            print(f"   - Process ID: {self.memory_manager.process_id}")
            print(f"   - Is attached: {attached}")

        # Atualiza informações do processo
        if attached:
            try:
                # Tenta obter nome do processo
                process_name = "Unknown"
                try:
                    import psutil
                    process = psutil.Process(self.memory_manager.process_id)
                    process_name = process.name()
                except:
                    process_name = f"Process_{self.memory_manager.process_id}"

                process_info = f"✅ PID: {self.memory_manager.process_id} ({process_name})"
                status_info = f"✅ Anexado ao processo {self.memory_manager.process_id}"

                print(f"   - Process info: {process_info}")
                print(f"   - Status info: {status_info}")

                # FORÇA a atualização dos labels MÚLTIPLAS VEZES
                for i in range(3):
                    self.process_info_label.configure(text=process_info, style='Success.TLabel')
                    self.status_label.configure(text=status_info)

                    # Força repaint imediato a cada iteração
                    try:
                        self.process_info_label.update()
                        self.status_label.update()
                        self.root.update_idletasks()
                    except:
                        pass

                print("✅ Interface atualizada - processo anexado")

            except Exception as e:
                print(f"⚠️ Erro ao atualizar info do processo: {e}")
                # Fallback com informação mínima
                process_info = f"✅ PID: {self.memory_manager.process_id}"
                status_info = f"✅ Anexado ao processo {self.memory_manager.process_id}"

                self.process_info_label.configure(text=process_info, style='Success.TLabel')
                self.status_label.configure(text=status_info)

                try:
                    self.process_info_label.update()
                    self.status_label.update()
                except:
                    pass
        else:
            print("   - Nenhum processo anexado")

            # FORÇA estado desanexado MÚLTIPLAS VEZES
            for i in range(3):
                self.process_info_label.configure(text="❌ Nenhum processo anexado", style='Error.TLabel')
                self.status_label.configure(text="ProcessDark pronto")

                # Força repaint imediato
                try:
                    self.process_info_label.update()
                    self.status_label.update()
                    self.root.update_idletasks()
                except:
                    pass

        # Atualiza botões baseado no estado
        scan_enabled = attached and not self.is_scanning

        try:
            self.first_scan_btn.configure(state='normal' if scan_enabled else 'disabled')
            self.next_scan_btn.configure(state='normal' if (scan_enabled and self.scan_results) else 'disabled')
        except:
            pass

        # Múltiplas atualizações visuais forçadas
        for i in range(3):
            try:
                self.root.update_idletasks()
                self.root.update()
            except:
                pass

        print(f"🔄 Atualização da interface concluída - Status: {'ANEXADO' if attached else 'DESANEXADO'}")

        # Retorna o estado para verificação externa
        return attached

    def update_stealth_display(self):
        """Atualiza exibição do status stealth"""
        if self.stealth_enabled:
            self.stealth_status_label.configure(text="ATIVO", style='Success.TLabel')
            self.stealth_status_bar.configure(text=f"Stealth: ON (Lv.{self.stealth_level})", style='Stealth.TLabel')
        else:
            self.stealth_status_label.configure(text="DESATIVADO", style='Error.TLabel')
            self.stealth_status_bar.configure(text="Stealth: OFF", style='Error.TLabel')

        self.stealth_level_label.configure(text=str(self.stealth_level))

    def update_process_info(self):
        """Atualiza informações do processo"""
        self.update_interface_state()
        self.log_message("Informações do processo atualizadas", "info")

    def test_attachment(self):
        """Testa o estado atual da anexação"""
        self.log_message("🧪 Testando estado da anexação...", "info")

        if self.memory_manager:
            self.log_message(f"Memory Manager: {'OK' if self.memory_manager else 'NONE'}", "info")
            self.log_message(f"Process ID: {self.memory_manager.process_id}", "info")
            self.log_message(f"Is Attached: {self.memory_manager.is_attached()}", "info")

            if hasattr(self.memory_manager, 'process_handle'):
                self.log_message(f"Process Handle: {'OK' if self.memory_manager.process_handle else 'NONE'}", "info")

            # Força atualização da interface
            self.update_interface_state()

            # Tenta anexar ao próprio processo como teste
            import os
            current_pid = os.getpid()
            self.log_message(f"Testando anexação ao processo atual (PID {current_pid})...", "info")

            if self.memory_manager.attach_to_process(current_pid):
                self.log_message("✅ Teste de anexação: SUCESSO", "success")
                self.update_interface_state()
            else:
                self.log_message("❌ Teste de anexação: FALHOU", "error")
        else:
            self.log_message("❌ Memory Manager não existe!", "error")

    def export_results(self):
        """Exporta resultados para arquivo"""
        if not self.scan_results:
            messagebox.showwarning("Aviso", "Nenhum resultado para exportar!")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename and self.scanner:
            if self.scanner.export_results(filename):
                self.log_message(f"Resultados exportados para {filename}", "success")
            else:
                self.log_message("Falha ao exportar resultados", "error")

    def import_results(self):
        """Importa resultados de arquivo"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename and self.scanner:
            if self.scanner.import_results(filename):
                self.scan_results = self.scanner.scan_results
                self.update_results_display()
                self.log_message(f"Resultados importados de {filename}", "success")
            else:
                self.log_message("Falha ao importar resultados", "error")

    def open_aob_scanner(self):
        """Abre AOB Scanner"""
        AOBScannerDialog(self.root, self.memory_manager)

    def open_viewmatrix_scanner(self):
        """Abre ViewMatrix Scanner"""
        ViewMatrixScannerDialog(self.root, self.memory_manager)

    def open_pointer_resolver(self):
        """Abre Pointer Resolver"""
        PointerResolverDialog(self.root, self.memory_manager)

    def show_about(self):
        """Mostra informações sobre o programa"""
        about_text = """
PyCheatEngine v1.0.0

Sistema de Engenharia Reversa e Manipulação de Memória

Funcionalidades:
• Scanner de memória avançado
• Funcionalidades stealth anti-detecção
• AOB Scanner com wildcards
• ViewMatrix Scanner para jogos 3D
• Resolução de ponteiros
• Interface gráfica completa

⚠️ Use com responsabilidade!
Apenas em processos autorizados.

Desenvolvido para fins educacionais.
        """
        messagebox.showinfo("Sobre PyCheatEngine", about_text)

    def run(self):
        """Executa a interface gráfica"""
        self.log_message("PyCheatEngine iniciado - Interface GUI carregada", "success")
        self.log_message("💡 Dica: Anexe a um processo e ative o modo stealth para máxima evasão", "info")
        self.root.mainloop()

# Diálogos auxiliares
class ProcessSelectionDialog:
    """Diálogo para seleção de processo"""

    def __init__(self, parent, memory_manager):
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Selecionar Processo")
        self.dialog.geometry("600x400")
        self.dialog.configure(bg='#2b2b2b')
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Lista de processos
        frame = ttk.Frame(self.dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Selecione um processo:", style='Dark.TLabel').pack(anchor=tk.W)

        # Treeview
        columns = ("PID", "Nome")
        self.tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=200)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Botões
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Botões da esquerda
        left_buttons = ttk.Frame(button_frame)
        left_buttons.pack(side=tk.LEFT)

        ttk.Button(left_buttons, text="🔄 Atualizar Lista", command=self.refresh_processes, style='Dark.TButton').pack(side=tk.LEFT, padx=(0, 5))

        # Botões da direita
        right_buttons = ttk.Frame(button_frame)
        right_buttons.pack(side=tk.RIGHT)

        ttk.Button(right_buttons, text="❌ Cancelar", command=self.dialog.destroy, style='Dark.TButton').pack(side=tk.RIGHT, padx=(5, 0))
        self.attach_button = ttk.Button(right_buttons, text="🔗 Anexar Processo", command=self.select_process, style='Dark.TButton', state='disabled')
        self.attach_button.pack(side=tk.RIGHT, padx=(5, 0))

        # Instruções para o usuário
        instruction_frame = ttk.Frame(self.dialog)
        instruction_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        instructions = [
            "💡 Como anexar a um processo:",
            "   1. Clique em um processo da lista para selecioná-lo",
            "   2. Clique no botão 'Anexar Processo' OU dê duplo clique",
            "   3. Confirme a anexação na janela que aparecer",
            "",
            "⚠️ Importante: Execute como administrador para melhor compatibilidade"
        ]

        for instruction in instructions:
            label = ttk.Label(instruction_frame, text=instruction, style='Dark.TLabel', font=('Arial', 8))
            label.pack(anchor=tk.W)

        # Carrega processos
        self.memory_manager = memory_manager
        self.refresh_processes()

        # Bind eventos - corrige duplo clique e seleção
        self.tree.bind('<Double-1>', self.on_double_click)
        self.tree.bind('<Return>', lambda e: self.select_process())
        self.tree.bind('<Button-1>', self.on_single_click)

    def refresh_processes(self):
        """Atualiza lista de processos"""
        # Limpa lista
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Mostra status de carregamento
        loading_item = self.tree.insert('', tk.END, values=("...", "Carregando processos..."))
        self.dialog.update()

        try:
            print("🔄 Atualizando lista de processos...")
            processes = self.memory_manager.list_processes()

            # Remove item de carregamento
            self.tree.delete(loading_item)

            if not processes:
                self.tree.insert('', tk.END, values=("", "❌ Nenhum processo encontrado"))
                messagebox.showwarning("Aviso", 
                    "Nenhum processo encontrado!\n\n" +
                    "Possíveis soluções:\n" +
                    "• Execute como administrador\n" +
                    "• Verifique se há processos rodando\n" +
                    "• Tente reiniciar o PyCheatEngine")
                return

            print(f"✓ Carregando {len(processes)} processos na lista...")

            # Adiciona processos à lista
            for proc in processes:
                try:
                    # Cria nome de exibição
                    name_display = proc['name']

                    # Adiciona informações extras se disponíveis
                    extras = []

                    if 'exe' in proc and proc['exe'] not in ['Unknown', 'Access Denied', '']:
                        exe_path = proc['exe']
                        if '\\' in exe_path:
                            exe_name = exe_path.split('\\')[-1]
                        else:
                            exe_name = exe_path

                        if exe_name != proc['name']:
                            extras.append(exe_name)

                    if 'status' in proc and proc['status'] != 'unknown':
                        extras.append(proc['status'])

                    if extras:
                        name_display += f" ({', '.join(extras)})"

                    # Adiciona à árvore com valores corretos
                    self.tree.insert('', tk.END, values=(proc['pid'], name_display))

                except Exception as e:
                    print(f"⚠️ Erro ao processar processo {proc.get('pid', '?')}: {e}")
                    continue

            print(f"✅ Lista atualizada com {len(processes)} processos")

        except Exception as e:
            # Remove item de carregamento se ainda estiver lá
            try:
                self.tree.delete(loading_item)
            except:
                pass

            self.tree.insert('', tk.END, values=("", f"❌ Erro: {str(e)[:50]}..."))

            error_msg = f"Erro ao listar processos: {e}\n\n"
            error_msg += "Soluções:\n"
            error_msg += "• Execute como administrador\n"
            error_msg += "• Feche outros programas que possam interferir\n"
            error_msg += "• Reinicie o sistema se necessário"

            print(f"❌ Erro na listagem: {e}")
            messagebox.showerror("Erro na Listagem", error_msg)

    def select_process(self):
        """Seleciona processo para anexar"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um processo da lista!")
            return

        try:
            item = self.tree.item(selection[0])
            values = item['values']

            # Verifica se é um item válido
            if not values or len(values) < 2:
                messagebox.showwarning("Aviso", "Item selecionado inválido!")
                return

            # Verifica se o primeiro valor é um PID válido
            pid_str = str(values[0]).strip()
            if pid_str == "..." or pid_str == "" or not pid_str.isdigit():
                messagebox.showwarning("Aviso", "Selecione um processo válido!\n\nDica: Clique em um processo da lista primeiro.")
                return

            pid = int(pid_str)
            process_name = str(values[1]).strip()

            print(f"✓ Processo selecionado: PID {pid} - {process_name}")

            # Confirma seleção com mais informações
            confirm_msg = f"Confirmar anexação ao processo:\n\n"
            confirm_msg += f"📋 PID: {pid}\n"
            confirm_msg += f"📝 Nome: {process_name}\n\n"
            confirm_msg += f"⚠️ Certifique-se de que você tem permissão para anexar a este processo.\n\n"
            confirm_msg += f"Prosseguir com a anexação?"

            confirm = messagebox.askyesno("Confirmar Anexação", confirm_msg)

            if confirm:
                print(f"✓ Usuário confirmou anexação ao PID {pid}")
                self.result = pid
                self.dialog.destroy()
            else:
                print("❌ Usuário cancelou anexação")

        except (ValueError, IndexError, TypeError) as e:
            print(f"❌ Erro ao selecionar processo: {e}")
            messagebox.showerror("Erro", f"Erro ao processar seleção:\n{e}\n\nTente:\n1. Selecionar outro processo\n2. Atualizar a lista\n3. Executar como administrador")
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            messagebox.showerror("Erro", f"Erro inesperado:\n{e}")

    def on_single_click(self, event):
        """Manipula clique simples para seleção"""
        try:
            item = self.tree.identify('item', event.x, event.y)
            if item:
                self.tree.selection_set(item)
                # Habilita botão de anexar se há seleção válida
                self.update_attach_button_state()
        except Exception as e:
            print(f"❌ Erro na seleção: {e}")

    def update_attach_button_state(self):
        """Atualiza estado do botão anexar baseado na seleção"""
        try:
            selection = self.tree.selection()
            if selection:
                item = self.tree.item(selection[0])
                values = item['values']
                if values and len(values) >= 2 and str(values[0]).isdigit():
                    self.attach_button.configure(state='normal')
                else:
                    self.attach_button.configure(state='disabled')
            else:
                self.attach_button.configure(state='disabled')
        except:
            self.attach_button.configure(state='disabled')

    def on_double_click(self, event):
        """Manipula duplo clique na lista de processos"""
        try:
            # Obtém item sob o cursor
            item = self.tree.identify('item', event.x, event.y)
            if item:
                # Seleciona o item
                self.tree.selection_set(item)
                # Executa anexação automaticamente
                self.select_process()
        except Exception as e:
            print(f"❌ Erro no duplo clique: {e}")
            messagebox.showerror("Erro", f"Erro no duplo clique:\n{e}")

class StealthLevelDialog:
    """Diálogo para configurar nível stealth"""

    def __init__(self, parent, current_level):
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Configurar Nível Stealth")
        self.dialog.geometry("400x300")
        self.dialog.configure(bg='#2b2b2b')
        self.dialog.transient(parent)
        self.dialog.grab_set()

        frame = ttk.Frame(self.dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ttk.Label(frame, text="Selecione o nível de stealth:", style='Dark.TLabel').pack(anchor=tk.W)

        # Níveis
        self.level_var = tk.IntVar(value=current_level)

        levels = [
            (0, "Desabilitado", "Sem proteções stealth"),
            (1, "Básico", "Delays aleatórios"),
            (2, "Moderado", "Anti-debug + delays"),
            (3, "Avançado", "Camuflagem + evasão"),
            (4, "Alto", "Evasão de API"),
            (5, "Máximo", "Todas as técnicas")
        ]

        for level, name, desc in levels:
            rb = ttk.Radiobutton(frame, text=f"Nível {level}: {name}", 
                               variable=self.level_var, value=level, style='Dark.TRadiobutton')
            rb.pack(anchor=tk.W, pady=2)

            desc_label = ttk.Label(frame, text=f"    {desc}", style='Dark.TLabel')
            desc_label.pack(anchor=tk.W, padx=(20, 0))

        # Botões
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancelar", command=self.dialog.destroy).pack(side=tk.RIGHT)

    def ok_clicked(self):
        self.result = self.level_var.get()
        self.dialog.destroy()

class StealthPresetDialog:
    """Diálogo para aplicar presets stealth"""

    def __init__(self, parent):
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Aplicar Preset Stealth")
        self.dialog.geometry("400x250")
        self.dialog.configure(bg='#2b2b2b')
        self.dialog.transient(parent)
        self.dialog.grab_set()

        frame = ttk.Frame(self.dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ttk.Label(frame, text="Selecione um preset:", style='Dark.TLabel').pack(anchor=tk.W)

        self.preset_var = tk.StringVar()

        for preset_name in STEALTH_PRESETS.keys():
            rb = ttk.Radiobutton(frame, text=preset_name, variable=self.preset_var, 
                               value=preset_name, style='Dark.TRadiobutton')
            rb.pack(anchor=tk.W, pady=5)

        # Botões
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(button_frame, text="Aplicar", command=self.apply_clicked).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancelar", command=self.dialog.destroy).pack(side=tk.RIGHT)

    def apply_clicked(self):
        if self.preset_var.get():
            self.result = self.preset_var.get()
            self.dialog.destroy()

class AOBScannerDialog:
    """Diálogo para AOB Scanner"""

    def __init__(self, parent, memory_manager):
        self.memory_manager = memory_manager

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("AOB Scanner")
        self.dialog.geometry("500x400")
        self.dialog.configure(bg='#2b2b2b')

        # Interface AOB Scanner aqui
        # (Implementação simplificada)

        frame = ttk.Frame(self.dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(frame, text="AOB Scanner - Em desenvolvimento", style='Dark.TLabel').pack()
        ttk.Button(frame, text="Fechar", command=self.dialog.destroy).pack(pady=10)

class ViewMatrixScannerDialog:
    """Diálogo para ViewMatrix Scanner"""

    def __init__(self, parent, memory_manager):
        self.memory_manager = memory_manager
        self.viewmatrix_scanner = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("ViewMatrix Scanner")
        self.dialog.geometry("600x500")
        self.dialog.configure(bg='#2b2b2b')
        self.dialog.transient(parent)

        if memory_manager and memory_manager.is_attached():
            try:
                from viewmatrix import ViewMatrixScanner
                self.viewmatrix_scanner = ViewMatrixScanner(memory_manager)
            except ImportError:
                pass

        self.create_interface()

    def create_interface(self):
        """Cria interface do ViewMatrix Scanner"""
        main_frame = ttk.Frame(self.dialog, style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Título
        title_label = ttk.Label(main_frame, text="ViewMatrix Scanner", 
                               style='Dark.TLabel', font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 10))

        if not self.memory_manager or not self.memory_manager.is_attached():
            ttk.Label(main_frame, text="❌ Nenhum processo anexado", 
                     style='Error.TLabel').pack(pady=20)
            ttk.Button(main_frame, text="Fechar", 
                      command=self.dialog.destroy, style='Dark.TButton').pack()
            return

        # Opções de scan
        options_frame = ttk.LabelFrame(main_frame, text="Opções de Scan", style='Dark.TFrame')
        options_frame.pack(fill=tk.X, pady=(0, 10))

        # Botão de scan automático
        ttk.Button(options_frame, text="Busca Automática", 
                  command=self.auto_scan, style='Dark.TButton').pack(side=tk.LEFT, padx=5, pady=5)

        # Botão de scan em range
        ttk.Button(options_frame, text="Busca em Range", 
                  command=self.range_scan, style='Dark.TButton').pack(side=tk.LEFT, padx=5, pady=5)

        # Entrada para endereço específico
        address_frame = ttk.LabelFrame(main_frame, text="Endereço Específico", style='Dark.TFrame')
        address_frame.pack(fill=tk.X, pady=(0, 10))

        addr_input_frame = ttk.Frame(address_frame, style='Dark.TFrame')
        addr_input_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(addr_input_frame, text="Endereço:", style='Dark.TLabel').pack(side=tk.LEFT)
        self.address_var = tk.StringVar()
        ttk.Entry(addr_input_frame, textvariable=self.address_var, 
                 style='Dark.TEntry', width=20).pack(side=tk.LEFT, padx=(5, 0))

        ttk.Button(addr_input_frame, text="Ler ViewMatrix", 
                  command=self.read_specific, style='Dark.TButton').pack(side=tk.LEFT, padx=(5, 0))

        # Resultados
        results_frame = ttk.LabelFrame(main_frame, text="Resultados", style='Dark.TFrame')
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Lista de candidatos
        self.results_listbox = tk.Listbox(results_frame, bg='#1e1e1e', fg='white', 
                                         selectbackground='#404040', height=8)
        self.results_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.results_listbox.bind('<Double-1>', self.on_result_select)

        # Log de atividades
        log_frame = ttk.LabelFrame(main_frame, text="Log", style='Dark.TFrame')
        log_frame.pack(fill=tk.X)

        self.log_text = tk.Text(log_frame, height=6, bg='#1e1e1e', fg='#00ff00', 
                               wrap=tk.WORD, font=('Consolas', 9))
        self.log_text.pack(fill=tk.X, padx=5, pady=5)

        # Botões inferiores
        button_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="Exportar", 
                  command=self.export_results, style='Dark.TButton').pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Fechar", 
                  command=self.dialog.destroy, style='Dark.TButton').pack(side=tk.RIGHT)

        self.log("ViewMatrix Scanner inicializado")

    def log(self, message):
        """Adiciona mensagem ao log"""
        import time
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.dialog.update()

    def auto_scan(self):
        """Executa busca automática por ViewMatrix"""
        if not self.viewmatrix_scanner:
            self.log("❌ Scanner não disponível")
            return

        self.log("🔍 Iniciando busca automática...")
        self.results_listbox.delete(0, tk.END)

        try:
            candidates = self.viewmatrix_scanner.scan_for_viewmatrix()

            if candidates:
                self.log(f"✅ Encontrados {len(candidates)} candidatos")
                for addr in candidates[:20]:  # Limita exibição
                    try:
                        matrix = self.viewmatrix_scanner.read_viewmatrix(addr)
                        if matrix and matrix.is_valid():
                            cam_pos = matrix.get_camera_position()
                            result_text = f"0x{addr:X} - Câmera: ({cam_pos[0]:.2f}, {cam_pos[1]:.2f}, {cam_pos[2]:.2f})"
                            self.results_listbox.insert(tk.END, result_text)
                        else:
                            result_text = f"0x{addr:X} - ViewMatrix inválida"
                            self.results_listbox.insert(tk.END, result_text)
                    except:
                        result_text = f"0x{addr:X} - Erro ao ler"
                        self.results_listbox.insert(tk.END, result_text)
            else:
                self.log("❌ Nenhuma ViewMatrix encontrada")

        except Exception as e:
            self.log(f"❌ Erro na busca: {e}")

    def range_scan(self):
        """Executa busca em range específico"""
        if not self.viewmatrix_scanner:
            self.log("❌ Scanner não disponível")
            return

        # Diálogo para entrada de range
        range_dialog = tk.Toplevel(self.dialog)
        range_dialog.title("Range de Busca")
        range_dialog.geometry("300x150")
        range_dialog.configure(bg='#2b2b2b')
        range_dialog.transient(self.dialog)

        ttk.Label(range_dialog, text="Endereço inicial (hex):", style='Dark.TLabel').pack(pady=5)
        start_var = tk.StringVar(value="0x400000")
        ttk.Entry(range_dialog, textvariable=start_var, style='Dark.TEntry').pack(pady=5)

        ttk.Label(range_dialog, text="Endereço final (hex):", style='Dark.TLabel').pack(pady=5)
        end_var = tk.StringVar(value="0x800000")
        ttk.Entry(range_dialog, textvariable=end_var, style='Dark.TEntry').pack(pady=5)

        def execute_range_scan():
            try:
                start_addr = int(start_var.get(), 16)
                end_addr = int(end_var.get(), 16)
                range_dialog.destroy()

                self.log(f"🔍 Buscando entre 0x{start_addr:X} e 0x{end_addr:X}...")
                candidates = self.viewmatrix_scanner.scan_for_viewmatrix((start_addr, end_addr))

                if candidates:
                    self.log(f"✅ Encontrados {len(candidates)} candidatos no range")
                    self.results_listbox.delete(0, tk.END)
                    for addr in candidates:
                        self.results_listbox.insert(tk.END, f"0x{addr:X}")
                else:
                    self.log("❌ Nenhuma ViewMatrix encontrada no range")

            except ValueError:
                self.log("❌ Endereços inválidos")
                range_dialog.destroy()

        ttk.Button(range_dialog, text="Buscar", command=execute_range_scan, 
                  style='Dark.TButton').pack(pady=10)

    def read_specific(self):
        """Lê ViewMatrix de endereço específico"""
        if not self.viewmatrix_scanner:
            self.log("❌ Scanner não disponível")
            return

        addr_str = self.address_var.get().strip()
        if not addr_str:
            self.log("❌ Digite um endereço")
            return

        try:
            addr = int(addr_str, 16) if addr_str.startswith('0x') else int(addr_str, 16)

            matrix = self.viewmatrix_scanner.read_viewmatrix(addr)
            if matrix and matrix.is_valid():
                cam_pos = matrix.get_camera_position()
                self.log(f"✅ ViewMatrix válida em 0x{addr:X}")
                self.log(f"📍 Posição da câmera: ({cam_pos[0]:.3f}, {cam_pos[1]:.3f}, {cam_pos[2]:.3f})")

                # Adiciona aos resultados
                result_text = f"0x{addr:X} - Manual - Câmera: ({cam_pos[0]:.2f}, {cam_pos[1]:.2f}, {cam_pos[2]:.2f})"
                self.results_listbox.insert(tk.END, result_text)
            else:
                self.log(f"❌ ViewMatrix inválida em 0x{addr:X}")

        except ValueError:
            self.log("❌ Endereço inválido")

    def on_result_select(self, event):
        """Callback quando resultado é selecionado"""
        selection = self.results_listbox.curselection()
        if not selection:
            return

        item = self.results_listbox.get(selection[0])
        # Extrai endereço do texto
        addr_str = item.split()[0]
        self.address_var.set(addr_str)
        self.log(f"Selecionado: {addr_str}")

    def export_results(self):
        """Exporta resultados para arquivo"""
        if not self.viewmatrix_scanner:
            self.log("❌ Scanner não disponível")
            return

        try:
            filename = f"viewmatrix_scan_{self.memory_manager.process_id}.json"
            if self.viewmatrix_scanner.export_viewmatrix_info(filename):
                self.log(f"✅ Resultados exportados: {filename}")
            else:
                self.log("❌ Falha ao exportar")
        except Exception as e:
            self.log(f"❌ Erro na exportação: {e}")

class PointerResolverDialog:
    """Diálogo para Pointer Resolver"""

    def __init__(self, parent, memory_manager):
        self.memory_manager = memory_manager

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Pointer Resolver")
        self.dialog.geometry("500x400")
        self.dialog.configure(bg='#2b2b2b')

        frame = ttk.Frame(self.dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Pointer Resolver - Em desenvolvimento", style='Dark.TLabel').pack()
        ttk.Button(frame, text="Fechar", command=self.dialog.destroy).pack(pady=10)

if __name__ == "__main__":
    app = PyCheatEngineGUI()
    app.run()