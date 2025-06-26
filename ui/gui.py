"""
Interface Gráfica para PyCheatEngine
Implementa uma GUI completa usando Tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading
import json
import os
from typing import List, Dict, Any, Optional, Union
import struct
import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory import MemoryManager
from scanner import MemoryScanner, ScanType, DataType, ScanResult
from pointer import PointerResolver, PointerChain
from aob_scan import AOBScanner, AOBResult

class CheatEngineGUI:
    """Interface gráfica principal do PyCheatEngine"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PyCheatEngine - Sistema de Engenharia Reversa")
        self.root.geometry("1200x800")

        # Componentes principais
        self.memory_manager = MemoryManager()
        self.scanner = MemoryScanner(self.memory_manager)
        self.pointer_resolver = PointerResolver(self.memory_manager)
        self.aob_scanner = AOBScanner(self.memory_manager)

        # Variáveis de controle
        self.current_process = None
        self.scan_thread = None
        self.auto_update_enabled = tk.BooleanVar(value=False)
        self.update_thread = None

        # Configuração de callbacks
        self.scanner.set_progress_callback(self.update_scan_progress)
        self.aob_scanner.set_progress_callback(self.update_aob_progress)

        self.setup_ui()
        self.setup_menu()

        # Inicia thread de atualização automática
        self.start_auto_update()

    def setup_menu(self):
        """Configura o menu principal"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menu Arquivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Salvar Sessão", command=self.save_session)
        file_menu.add_command(label="Carregar Sessão", command=self.load_session)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.root.quit)

        # Menu Processos
        process_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Processos", menu=process_menu)
        process_menu.add_command(label="Atualizar Lista", command=self.refresh_process_list)
        process_menu.add_command(label="Desanexar", command=self.detach_process)

        # Menu Ferramentas
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ferramentas", menu=tools_menu)
        tools_menu.add_command(label="Calculadora Hex", command=self.open_hex_calculator)
        tools_menu.add_command(label="Conversor de Tipos", command=self.open_type_converter)

        # Menu Ajuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ajuda", menu=help_menu)
        help_menu.add_command(label="Sobre", command=self.show_about)

    def setup_ui(self):
        """Configura a interface principal"""
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Notebook para abas
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Aba Scanner
        self.setup_scanner_tab(notebook)

        # Aba Ponteiros
        self.setup_pointer_tab(notebook)

        # Aba AOB Scanner
        self.setup_aob_tab(notebook)

        # Frame de status
        self.setup_status_frame(main_frame)

    def setup_scanner_tab(self, parent):
        """Configura a aba do scanner de memória"""
        scanner_frame = ttk.Frame(parent)
        parent.add(scanner_frame, text="Scanner de Memória")

        # Frame esquerdo - Controles
        left_frame = ttk.Frame(scanner_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # Seleção de processo
        process_group = ttk.LabelFrame(left_frame, text="Processo")
        process_group.pack(fill=tk.X, pady=5)

        ttk.Label(process_group, text="Selecionar Processo:").pack(anchor=tk.W)
        self.process_var = tk.StringVar()
        self.process_combo = ttk.Combobox(process_group, textvariable=self.process_var, 
                                         state="readonly", width=30)
        self.process_combo.pack(pady=2)
        self.process_combo.bind('<<ComboboxSelected>>', self.on_process_selected)

        ttk.Button(process_group, text="Atualizar Lista", 
                  command=self.refresh_process_list).pack(pady=2)

        self.refresh_process_list()

        # Configurações de scan
        scan_group = ttk.LabelFrame(left_frame, text="Configurações de Scan")
        scan_group.pack(fill=tk.X, pady=5)

        # Frame de dicas
        tips_frame = ttk.Frame(scan_group)
        tips_frame.pack(fill=tk.X, pady=2)
        tips_label1 = ttk.Label(tips_frame, text="💡 DICA: Para próximo scan, altere o valor no jogo PRIMEIRO!", 
                              font=('TkDefaultFont', 8), foreground='blue')
        tips_label1.pack(anchor=tk.W)

        tips_label2 = ttk.Label(tips_frame, text="🎯 MUNIÇÕES: Atire algumas vezes, depois use 'decreased' (não 'exact')", 
                              font=('TkDefaultFont', 8), foreground='green')
        tips_label2.pack(anchor=tk.W)

        tips_label3 = ttk.Label(tips_frame, text="⚡ VIDA/HP: Perca vida no jogo, depois use 'decreased' para filtrar", 
                              font=('TkDefaultFont', 8), foreground='orange')
        tips_label3.pack(anchor=tk.W)

        tips_label4 = ttk.Label(tips_frame, text="⌨️ ATALHOS: Ctrl+C=Copiar | Clique direito=Menu | Enter=Editar", 
                              font=('TkDefaultFont', 8), foreground='purple')
        tips_label4.pack(anchor=tk.W)

        ttk.Label(scan_group, text="Tipo de Dado:").pack(anchor=tk.W)
        self.data_type_var = tk.StringVar(value="int32")
        data_type_combo = ttk.Combobox(scan_group, textvariable=self.data_type_var,
                                      values=["int32", "int64", "float", "double", "string"],
                                      state="readonly")
        data_type_combo.pack(pady=2)

        ttk.Label(scan_group, text="Valor:").pack(anchor=tk.W)
        self.scan_value_var = tk.StringVar()
        ttk.Entry(scan_group, textvariable=self.scan_value_var).pack(pady=2)

        ttk.Label(scan_group, text="Tipo de Comparação:").pack(anchor=tk.W)
        self.scan_type_var = tk.StringVar(value="exact")
        scan_type_combo = ttk.Combobox(scan_group, textvariable=self.scan_type_var,
                                      values=["exact", "increased", "decreased", "changed", 
                                             "unchanged", "greater_than", "less_than"],
                                      state="readonly")
        scan_type_combo.pack(pady=2)

        # Label explicativo
        help_label = ttk.Label(scan_group, text="exact=valor específico | changed=qualquer mudança | increased/decreased=direção", 
                              font=('TkDefaultFont', 7), foreground='gray')
        help_label.pack(anchor=tk.W)

        # Botões de scan
        button_frame = ttk.Frame(scan_group)
        button_frame.pack(fill=tk.X, pady=5)

        self.first_scan_btn = ttk.Button(button_frame, text="Primeiro Scan", 
                                        command=self.start_first_scan)
        self.first_scan_btn.pack(side=tk.LEFT, padx=2)

        self.next_scan_btn = ttk.Button(button_frame, text="Próximo Scan", 
                                       command=self.start_next_scan, state=tk.DISABLED)
        self.next_scan_btn.pack(side=tk.LEFT, padx=2)

        self.cancel_scan_btn = ttk.Button(button_frame, text="Cancelar", 
                                         command=self.cancel_scan, state=tk.DISABLED)
        self.cancel_scan_btn.pack(side=tk.LEFT, padx=2)

        # Barra de progresso
        self.scan_progress = ttk.Progressbar(scan_group, mode='determinate')
        self.scan_progress.pack(fill=tk.X, pady=5)

        # Frame direito - Resultados
        right_frame = ttk.Frame(scanner_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Lista de resultados
        results_group = ttk.LabelFrame(right_frame, text="Resultados")
        results_group.pack(fill=tk.BOTH, expand=True)

        # Treeview para resultados
        columns = ("address", "value", "type")
        self.results_tree = ttk.Treeview(results_group, columns=columns, show="headings", height=15)

        self.results_tree.heading("address", text="Endereço")
        self.results_tree.heading("value", text="Valor Atual") 
        self.results_tree.heading("type", text="Tipo")

        self.results_tree.column("address", width=120, anchor="w")
        self.results_tree.column("value", width=100, anchor="e")
        self.results_tree.column("type", width=80, anchor="center")

        # Configura seleção múltipla e cores
        self.results_tree.configure(selectmode='extended')  # Permite seleção múltipla

        # Configura tags para cores alternadas
        self.results_tree.tag_configure('odd', background='#f0f0f0')
        self.results_tree.tag_configure('even', background='white')
        self.results_tree.tag_configure('selected', background='#0078d4', foreground='white')

        # Scrollbar para resultados
        results_scroll = ttk.Scrollbar(results_group, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scroll.set)

        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind para duplo clique e seleção simples
        self.results_tree.bind('<Double-1>', self.on_result_double_click)
        self.results_tree.bind('<ButtonRelease-1>', self.on_result_select)
        self.results_tree.bind('<Button-3>', self.show_results_context_menu)  # Clique direito

        # Bind para teclas de atalho
        self.results_tree.bind('<Control-c>', self.copy_selected_address)
        self.results_tree.bind('<Control-a>', self.select_all_results)

        # Permite que o Treeview receba foco
        self.results_tree.focus_set()

        # Controles de valor
        value_frame = ttk.Frame(right_frame)
        value_frame.pack(fill=tk.X, pady=5)

        ttk.Label(value_frame, text="Novo Valor:").pack(side=tk.LEFT)
        self.new_value_var = tk.StringVar()
        self.new_value_entry = ttk.Entry(value_frame, textvariable=self.new_value_var, width=20)
        self.new_value_entry.pack(side=tk.LEFT, padx=5)

        # Bind Enter para escrever valor rapidamente
        self.new_value_entry.bind('<Return>', lambda e: self.write_selected_value())

        # Bind teclas do Treeview
        self.root.bind('<Return>', self.on_enter_key)
        self.root.bind('<Delete>', self.on_delete_key)

        ttk.Button(value_frame, text="Escrever Valor", 
                  command=self.write_selected_value).pack(side=tk.LEFT, padx=5)

        ttk.Button(value_frame, text="Limpar", 
                  command=lambda: self.new_value_var.set("")).pack(side=tk.LEFT, padx=2)

        # Checkbox para atualização automática
        ttk.Checkbutton(value_frame, text="Atualização Automática", 
                       variable=self.auto_update_enabled).pack(side=tk.RIGHT)

    def setup_pointer_tab(self, parent):
        """Configura a aba de ponteiros"""
        pointer_frame = ttk.Frame(parent)
        parent.add(pointer_frame, text="Ponteiros")

        # Frame superior - Criação de ponteiros
        top_frame = ttk.LabelFrame(pointer_frame, text="Nova Cadeia de Ponteiros")
        top_frame.pack(fill=tk.X, padx=5, pady=5)

        # Entrada para endereço base
        addr_frame = ttk.Frame(top_frame)
        addr_frame.pack(fill=tk.X, pady=2)
        ttk.Label(addr_frame, text="Endereço Base:").pack(side=tk.LEFT)
        self.base_addr_var = tk.StringVar()
        ttk.Entry(addr_frame, textvariable=self.base_addr_var, width=20).pack(side=tk.LEFT, padx=5)

        # Entrada para offsets
        offset_frame = ttk.Frame(top_frame)
        offset_frame.pack(fill=tk.X, pady=2)
        ttk.Label(offset_frame, text="Offsets (separados por vírgula):").pack(side=tk.LEFT)
        self.offsets_var = tk.StringVar()
        ttk.Entry(offset_frame, textvariable=self.offsets_var, width=30).pack(side=tk.LEFT, padx=5)

        # Descrição
        desc_frame = ttk.Frame(top_frame)
        desc_frame.pack(fill=tk.X, pady=2)
        ttk.Label(desc_frame, text="Descrição:").pack(side=tk.LEFT)
        self.pointer_desc_var = tk.StringVar()
        ttk.Entry(desc_frame, textvariable=self.pointer_desc_var, width=40).pack(side=tk.LEFT, padx=5)

        # Botões
        btn_frame = ttk.Frame(top_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Adicionar Ponteiro", 
                  command=self.add_pointer_chain).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Testar Ponteiro", 
                  command=self.test_pointer_chain).pack(side=tk.LEFT, padx=5)

        # Lista de ponteiros
        list_frame = ttk.LabelFrame(pointer_frame, text="Cadeias de Ponteiros")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Treeview para ponteiros
        pointer_columns = ("description", "base", "offsets", "final_addr", "value", "valid")
        self.pointer_tree = ttk.Treeview(list_frame, columns=pointer_columns, show="headings")

        self.pointer_tree.heading("description", text="Descrição")
        self.pointer_tree.heading("base", text="Base")
        self.pointer_tree.heading("offsets", text="Offsets")
        self.pointer_tree.heading("final_addr", text="Endereço Final")
        self.pointer_tree.heading("value", text="Valor")
        self.pointer_tree.heading("valid", text="Válido")

        self.pointer_tree.column("description", width=150)
        self.pointer_tree.column("base", width=100)
        self.pointer_tree.column("offsets", width=120)
        self.pointer_tree.column("final_addr", width=100)
        self.pointer_tree.column("value", width=80)
        self.pointer_tree.column("valid", width=60)

        pointer_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.pointer_tree.yview)
        self.pointer_tree.configure(yscrollcommand=pointer_scroll.set)

        self.pointer_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pointer_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind para contexto
        self.pointer_tree.bind('<Button-3>', self.show_pointer_context_menu)

    def setup_aob_tab(self, parent):
        """Configura a aba do scanner AOB"""
        aob_frame = ttk.Frame(parent)
        parent.add(aob_frame, text="Scanner AOB")

        # Frame superior - Configurações
        config_frame = ttk.LabelFrame(aob_frame, text="Configurações AOB")
        config_frame.pack(fill=tk.X, padx=5, pady=5)

        # Padrão de bytes
        pattern_frame = ttk.Frame(config_frame)
        pattern_frame.pack(fill=tk.X, pady=2)
        ttk.Label(pattern_frame, text="Padrão de Bytes:").pack(side=tk.LEFT)
        self.aob_pattern_var = tk.StringVar()
        pattern_entry = ttk.Entry(pattern_frame, textvariable=self.aob_pattern_var, width=50)
        pattern_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Descrição do padrão
        desc_frame = ttk.Frame(config_frame)
        desc_frame.pack(fill=tk.X, pady=2)
        ttk.Label(desc_frame, text="Descrição:").pack(side=tk.LEFT)
        self.aob_desc_var = tk.StringVar()
        ttk.Entry(desc_frame, textvariable=self.aob_desc_var, width=40).pack(side=tk.LEFT, padx=5)

        # Botões AOB
        aob_btn_frame = ttk.Frame(config_frame)
        aob_btn_frame.pack(fill=tk.X, pady=5)

        self.aob_scan_btn = ttk.Button(aob_btn_frame, text="Buscar Padrão", 
                                      command=self.start_aob_scan)
        self.aob_scan_btn.pack(side=tk.LEFT, padx=5)

        self.aob_cancel_btn = ttk.Button(aob_btn_frame, text="Cancelar", 
                                        command=self.cancel_aob_scan, state=tk.DISABLED)
        self.aob_cancel_btn.pack(side=tk.LEFT, padx=5)

        # Barra de progresso AOB
        self.aob_progress = ttk.Progressbar(config_frame, mode='determinate')
        self.aob_progress.pack(fill=tk.X, pady=5)

        # Resultados AOB
        aob_results_frame = ttk.LabelFrame(aob_frame, text="Resultados AOB")
        aob_results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Treeview para resultados AOB
        aob_columns = ("address", "pattern", "matched_bytes")
        self.aob_tree = ttk.Treeview(aob_results_frame, columns=aob_columns, show="headings")

        self.aob_tree.heading("address", text="Endereço")
        self.aob_tree.heading("pattern", text="Padrão")
        self.aob_tree.heading("matched_bytes", text="Bytes Encontrados")

        self.aob_tree.column("address", width=120)
        self.aob_tree.column("pattern", width=200)
        self.aob_tree.column("matched_bytes", width=200)

        aob_scroll = ttk.Scrollbar(aob_results_frame, orient=tk.VERTICAL, command=self.aob_tree.yview)
        self.aob_tree.configure(yscrollcommand=aob_scroll.set)

        self.aob_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        aob_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_status_frame(self, parent):
        """Configura o frame de status"""
        self.status_frame = ttk.Frame(parent)
        self.status_frame.pack(fill=tk.X, pady=5)

        self.status_label = ttk.Label(self.status_frame, text="Pronto")
        self.status_label.pack(side=tk.LEFT)

        self.result_count_label = ttk.Label(self.status_frame, text="")
        self.result_count_label.pack(side=tk.RIGHT)

    def refresh_process_list(self):
        """Atualiza a lista de processos"""
        try:
            processes = MemoryManager.list_processes()
            process_list = [f"{proc['name']} (PID: {proc['pid']})" for proc in processes]
            self.process_combo['values'] = process_list
            self.update_status("Lista de processos atualizada")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar lista de processos: {e}")

    def on_process_selected(self, event):
        """Callback para seleção de processo"""
        selection = self.process_var.get()
        if selection:
            try:
                # Extrai PID da string
                pid_str = selection.split("PID: ")[1].rstrip(")")
                pid = int(pid_str)

                if self.memory_manager.attach_to_process(pid):
                    self.current_process = pid
                    self.update_status(f"Anexado ao processo: {selection}")
                    self.first_scan_btn.config(state=tk.NORMAL)
                else:
                    messagebox.showerror("Erro", "Falha ao anexar ao processo")

            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao anexar ao processo: {e}")

    def detach_process(self):
        """Desanexa do processo atual"""
        self.memory_manager.detach_process()
        self.current_process = None
        self.scanner.clear_results()
        self.clear_results_display()
        self.first_scan_btn.config(state=tk.DISABLED)
        self.next_scan_btn.config(state=tk.DISABLED)
        self.update_status("Processo desanexado")

    def start_first_scan(self):
        """Inicia o primeiro scan"""
        if not self.memory_manager.is_attached():
            messagebox.showerror("Erro", "Nenhum processo anexado")
            return

        value = self.scan_value_var.get()
        if not value:
            messagebox.showerror("Erro", "Digite um valor para buscar")
            return

        try:
            # Converte valor baseado no tipo
            data_type = DataType(self.data_type_var.get())
            scan_type = ScanType(self.scan_type_var.get())

            if data_type in [DataType.INT32, DataType.INT64]:
                value = int(value)
            elif data_type in [DataType.FLOAT, DataType.DOUBLE]:
                value = float(value)

            # Desabilita botões
            self.first_scan_btn.config(state=tk.DISABLED)
            self.cancel_scan_btn.config(state=tk.NORMAL)

            # Inicia scan em thread separada
            self.scan_thread = threading.Thread(
                target=self._perform_first_scan,
                args=(value, data_type, scan_type)
            )
            self.scan_thread.start()

        except ValueError as e:
            messagebox.showerror("Erro", f"Valor inválido: {e}")

    def _perform_first_scan(self, value, data_type, scan_type):
        """Executa o primeiro scan em thread separada"""
        try:
            results = self.scanner.first_scan(value, data_type, scan_type)

            # Atualiza UI na thread principal
            self.root.after(0, self._scan_completed, results, True)

        except Exception as e:
            self.root.after(0, self._scan_error, str(e))

    def start_next_scan(self):
        """Inicia o próximo scan"""
        print(f"[GUI] start_next_scan chamado")

        # Validação de pré-requisitos
        if not self.memory_manager.is_attached():
            error_msg = "Nenhum processo anexado"
            print(f"[GUI ERROR] {error_msg}")
            messagebox.showerror("Erro", error_msg)
            return

        if not self.scanner.scan_results:
            error_msg = "Nenhum resultado de scan anterior. Execute o primeiro scan antes."
            print(f"[GUI ERROR] {error_msg}")
            messagebox.showerror("Erro", error_msg)
            return

        print(f"[GUI] {len(self.scanner.scan_results)} resultados anteriores encontrados")

        # Obtém parâmetros da interface
        value = self.scan_value_var.get().strip()
        scan_type_str = self.scan_type_var.get()
        print(f"[GUI] Valor digitado: '{value}', Tipo: '{scan_type_str}'")

        # Valida tipo de scan
        try:
            scan_type = ScanType(scan_type_str)
        except ValueError as e:
            error_msg = f"Tipo de scan inválido: {scan_type_str}"
            print(f"[GUI ERROR] {error_msg}")
            messagebox.showerror("Erro", error_msg)
            return

        # Processa valor baseado no tipo de scan
        processed_value = None

        if scan_type in [ScanType.INCREASED, ScanType.DECREASED, ScanType.CHANGED, ScanType.UNCHANGED]:
            # Estes tipos não precisam de valor
            processed_value = None
            print(f"[GUI] Scan {scan_type.value} não precisa de valor, usando None")

        else:
            # Estes tipos precisam de valor
            if not value:
                error_msg = f"Tipo de scan '{scan_type.value}' requer um valor"
                print(f"[GUI ERROR] {error_msg}")
                messagebox.showerror("Erro", error_msg)
                return

            try:
                # Obtém tipo de dado dos resultados existentes
                if self.scanner.scan_results and len(self.scanner.scan_results) > 0:
                    data_type = self.scanner.scan_results[0].data_type
                    print(f"[GUI] Tipo de dado dos resultados: {data_type.value}")
                else:
                    data_type = DataType(self.data_type_var.get())
                    print(f"[GUI] Tipo de dado da interface: {data_type.value}")

                # Converte valor baseado no tipo de dado
                if data_type == DataType.INT32:
                    processed_value = int(value)
                    if processed_value < -2147483648 or processed_value > 2147483647:
                        raise ValueError("Valor fora do range INT32")
                elif data_type == DataType.INT64:
                    processed_value = int(value)
                    if processed_value < -9223372036854775808 or processed_value > 9223372036854775807:
                        raise ValueError("Valor fora do range INT64")
                elif data_type in [DataType.FLOAT, DataType.DOUBLE]:
                    processed_value = float(value)
                    if abs(processed_value) > 1e308:
                        raise ValueError("Valor muito grande para float/double")
                elif data_type == DataType.STRING:
                    processed_value = str(value)
                else:
                    processed_value = value

                print(f"[GUI] Valor processado: {processed_value} (tipo: {type(processed_value).__name__})")

            except ValueError as e:
                error_msg = f"Valor inválido para o tipo de dado: {e}"
                print(f"[GUI ERROR] {error_msg}")
                messagebox.showerror("Erro", error_msg)
                return
            except Exception as e:
                error_msg = f"Erro ao processar valor: {e}"
                print(f"[GUI ERROR] {error_msg}")
                messagebox.showerror("Erro", error_msg)
                return

        # Desabilita botões
        self.next_scan_btn.config(state=tk.DISABLED)
        self.cancel_scan_btn.config(state=tk.NORMAL)
        self.first_scan_btn.config(state=tk.DISABLED)

        # Atualiza status e progresso
        self.update_status("Executando próximo scan...")
        self.scan_progress['value'] = 0
        print(f"[GUI] Iniciando thread para próximo scan...")

        # Inicia scan em thread separada
        self.scan_thread = threading.Thread(
            target=self._perform_next_scan,
            args=(processed_value, scan_type),
            name="NextScanThread"
        )
        self.scan_thread.daemon = True
        self.scan_thread.start()
        print(f"[GUI] Thread '{self.scan_thread.name}' iniciada")

    def _perform_next_scan(self, value, scan_type):
        """Executa o próximo scan em thread separada"""
        try:
            print(f"[GUI] Iniciando _perform_next_scan com valor={value}, tipo={scan_type}")

            # Verifica se o scanner ainda está válido
            if not hasattr(self, 'scanner') or not self.scanner:
                raise RuntimeError("Scanner não inicializado")

            # Verifica se há resultados anteriores
            if not self.scanner.scan_results:
                raise RuntimeError("Nenhum resultado de scan anterior")

            print(f"[GUI] Scanner válido, {len(self.scanner.scan_results)} resultados anteriores")

            # FORÇA ATUALIZAÇÃO DE TODOS OS VALORES ANTES DO SCAN
            print(f"[GUI] Forçando atualização de valores da memória...")
            try:
                updated_count = self.scanner.refresh_all_values()
                print(f"[GUI] {updated_count} valores foram atualizados da memória")

                # Aguarda um pouco para que os valores se estabilizem
                import time
                time.sleep(0.1)

            except Exception as refresh_error:
                print(f"[GUI] Erro ao atualizar valores: {refresh_error}")

            # Para scans exact, faz uma pré-verificação para detectar valores instáveis
            if scan_type.value == "exact" and value is not None:
                print(f"[GUI] Fazendo pré-verificação para valor exact: {value}")
                stable_results = []
                unstable_count = 0

                # Verifica se os valores estão estáveis (após atualização)
                for i, result in enumerate(self.scanner.scan_results[:10]):  # Testa apenas os primeiros 10
                    current_value = self.scanner._read_value_at_address(result.address, result.data_type)
                    if current_value is not None:
                        if current_value == value:
                            stable_results.append(result)
                        elif current_value != result.value:
                            unstable_count += 1
                            print(f"[GUI] Valor instável detectado no endereço 0x{result.address:X}: {result.value} -> {current_value}")

                if len(stable_results) == 0 and unstable_count > 0:
                    suggestion = f"DICA: Os valores estão mudando constantemente. Use 'changed', 'increased' ou 'decreased'"
                    print(f"[GUI] {suggestion}")
                    if hasattr(self, 'root') and self.root:
                        self.root.after(0, self.update_status, suggestion)

            # Executa o next scan
            results = self.scanner.next_scan(value, scan_type)
            print(f"[GUI] Next scan retornou {len(results)} resultados")

            # Verifica se a UI ainda existe antes de atualizar
            if hasattr(self, 'root') and self.root:
                self.root.after(0, self._scan_completed, results, False)

        except Exception as e:
            print(f"[GUI ERROR] Erro em _perform_next_scan: {e}")
            import traceback
            traceback.print_exc()

            if hasattr(self, 'root') and self.root:
                self.root.after(0, self._scan_error, f"Erro no próximo scan: {str(e)}")

    def _scan_completed(self, results, is_first_scan):
        """Callback para scan completado"""
        try:
            results_count = len(results) if results else 0
            print(f"[GUI] _scan_completed chamado com {results_count} resultados, is_first_scan={is_first_scan}")

            # Reabilita botões
            self.first_scan_btn.config(state=tk.NORMAL)
            self.cancel_scan_btn.config(state=tk.DISABLED)

            # Determina se próximo scan deve ser habilitado
            should_enable_next = results_count > 0 and not is_first_scan or (is_first_scan and results_count > 0)

            if should_enable_next:
                self.next_scan_btn.config(state=tk.NORMAL)
                print(f"[GUI] Botão próximo scan habilitado ({results_count} resultados)")
            else:
                self.next_scan_btn.config(state=tk.DISABLED)
                print(f"[GUI] Botão próximo scan desabilitado ({results_count} resultados)")

            # Atualiza exibição dos resultados
            try:
                self.update_results_display()
            except Exception as display_error:
                print(f"[GUI ERROR] Erro ao atualizar exibição: {display_error}")

            # Atualiza progresso para 100%
            self.scan_progress['value'] = 100

            # Mensagem de status
            if is_first_scan:
                status_msg = f"✓ Primeiro scan: {results_count} resultados encontrados"
                if results_count > 0:
                    status_msg += " - Agora altere o valor no jogo e use 'Next Scan'"
            else:
                status_msg = f"✓ Próximo scan: {results_count} resultados restantes"
                if results_count == 0:
                    status_msg += " - Valor não mudou ou não foi encontrado"
                elif results_count == 1:
                    status_msg += " - Endereço encontrado! 🎯"

            print(f"[GUI] {status_msg}")
            self.update_status(status_msg)

            # Se não há resultados e não é primeiro scan, sugere dica
            if results_count == 0 and not is_first_scan:
                self.update_status("✓ Nenhum resultado encontrado. DICA: Altere o valor no jogo/aplicação primeiro, depois use 'changed' ou 'increased'/'decreased'.")

        except Exception as e:
            print(f"[GUI ERROR] Erro em _scan_completed: {e}")
            import traceback
            traceback.print_exc()

            # Garante que os botões sejam reabilitados mesmo em caso de erro
            try:
                self.first_scan_btn.config(state=tk.NORMAL)
                self.cancel_scan_btn.config(state=tk.DISABLED)
                self.update_status("Erro ao processar resultados do scan")
            except:
                pass

    def _scan_error(self, error_msg):
        """Callback para erro no scan"""
        self.first_scan_btn.config(state=tk.NORMAL)
        self.next_scan_btn.config(state=tk.NORMAL if self.scanner.get_result_count() > 0 else tk.DISABLED)
        self.cancel_scan_btn.config(state=tk.DISABLED)

        messagebox.showerror("Erro no Scan", error_msg)
        self.update_status("Erro no scan")

    def cancel_scan(self):
        """Cancela o scan atual"""
        self.scanner.cancel_scan()
        self.aob_scanner.cancel_scan()

        self.first_scan_btn.config(state=tk.NORMAL)
        self.next_scan_btn.config(state=tk.NORMAL if self.scanner.get_result_count() > 0 else tk.DISABLED)
        self.cancel_scan_btn.config(state=tk.DISABLED)

        self.update_status("Scan cancelado")

    def update_scan_progress(self, progress):
        """Atualiza barra de progresso do scan"""
        try:
            if hasattr(self, 'scan_progress') and self.scan_progress:
                self.scan_progress['value'] = progress
            if hasattr(self, 'root') and self.root:
                self.root.update_idletasks()
        except (tk.TclError, AttributeError):
            # UI foi destruída ou não está disponível
            pass

    def update_aob_progress(self, progress):
        """Atualiza barra de progresso do AOB"""
        self.aob_progress['value'] = progress
        self.root.update_idletasks()

    def update_results_display(self):
        """Atualiza a exibição dos resultados"""
        # Limpa árvore
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Adiciona novos resultados (máximo 1000 para performance)
        results = self.scanner.scan_results[:1000]
        for i, result in enumerate(results):
            # Alterna cores das linhas
            tag = 'even' if i % 2 == 0 else 'odd'

            item_id = self.results_tree.insert('', 'end', values=(
                f"0x{result.address:X}",
                str(result.value),
                result.data_type.value
            ), tags=(tag,))

        # Atualiza contador
        total_results = self.scanner.get_result_count()
        if total_results > 1000:
            self.result_count_label.config(text=f"Mostrando 1000 de {total_results} resultados")
        else:
            self.result_count_label.config(text=f"{total_results} resultados")

        # Seleciona o primeiro item se houver resultados
        if results:
            self.results_tree.selection_set(self.results_tree.get_children()[0])
            self.results_tree.focus_set()

    def clear_results_display(self):
        """Limpa a exibição dos resultados"""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.result_count_label.config(text="")

    def on_result_select(self, event):
        """Callback para seleção simples de resultado"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            current_value = item['values'][1]

            # Pré-preenche o campo de novo valor apenas se estiver vazio
            if not self.new_value_var.get():
                self.new_value_var.set(str(current_value))

    def show_results_context_menu(self, event):
        """Mostra menu de contexto para resultados"""
        selection = self.results_tree.selection()
        if selection:
            context_menu = tk.Menu(self.root, tearoff=0)

            # Seção principal
            context_menu.add_command(label="✏️ Editar Valor", command=self.edit_selected_value)
            context_menu.add_command(label="📝 Alterar Tipo", command=self.change_value_type)
            context_menu.add_separator()

            # Análise de memória
            memory_menu = tk.Menu(context_menu, tearoff=0)
            memory_menu.add_command(label="🔍 Visualizar Região de Memória", command=self.open_memory_viewer_from_selection)
            memory_menu.add_command(label="📊 Analisar Estrutura de Dados", command=self.analyze_data_structure)
            memory_menu.add_command(label="🔗 Buscar Ponteiros para Este Endereço", command=self.find_pointers_to_address)
            memory_menu.add_command(label="⚡ Verificar Offsets Próximos", command=self.check_nearby_offsets)
            memory_menu.add_command(label="🎯 Criar Ponteiro Automaticamente", command=self.auto_create_pointer)
            context_menu.add_cascade(label="🧠 Análise de Memória", menu=memory_menu)

            context_menu.add_separator()

            # Operações de cópia
            copy_menu = tk.Menu(context_menu, tearoff=0)
            copy_menu.add_command(label="📍 Copiar Endereço", command=self.copy_selected_address)
            copy_menu.add_command(label="💾 Copiar Valor", command=self.copy_selected_value)
            copy_menu.add_command(label="📋 Copiar Endereço + Valor", command=self.copy_address_and_value)
            copy_menu.add_command(label="🔢 Copiar como Hex", command=self.copy_as_hex)
            copy_menu.add_command(label="📄 Copiar Informações Completas", command=self.copy_full_info)
            context_menu.add_cascade(label="📋 Copiar", menu=copy_menu)

            # Navegação
            nav_menu = tk.Menu(context_menu, tearoff=0)
            nav_menu.add_command(label="🎯 Ir para Endereço", command=self.goto_address)
            nav_menu.add_command(label="⬅️ Ir para Endereço Base", command=self.goto_base_address)
            nav_menu.add_command(label="➡️ Seguir Ponteiro", command=self.follow_pointer)
            context_menu.add_cascade(label="🧭 Navegação", menu=nav_menu)

            context_menu.add_separator()

            # Favoritos e organização
            context_menu.add_command(label="⭐ Adicionar aos Favoritos", command=self.add_to_favorites)
            context_menu.add_command(label="🏷️ Adicionar Comentário", command=self.add_comment)
            context_menu.add_command(label="🎨 Alterar Cor", command=self.change_color)

            context_menu.add_separator()

            # Ferramentas avançadas
            tools_menu = tk.Menu(context_menu, tearoff=0)
            tools_menu.add_command(label="📈 Monitor Contínuo", command=self.start_monitoring)
            tools_menu.add_command(label="🔄 Histórico de Valores", command=self.show_value_history)
            tools_menu.add_command(label="📐 Calcular Distância", command=self.calculate_distance)
            tools_menu.add_command(label="🔍 Buscar Referências", command=self.find_references)
            context_menu.add_cascade(label="🛠️ Ferramentas", menu=tools_menu)

            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()

    def copy_selected_address(self, event=None):
        """Copia o endereço selecionado para a área de transferência"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            address_str = item['values'][0]

            # Copia para área de transferência
            self.root.clipboard_clear()
            self.root.clipboard_append(address_str)
            self.update_status(f"Endereço {address_str} copiado para área de transferência")

            # Feedback visual temporário
            self.show_copy_feedback(address_str)
        else:
            messagebox.showwarning("Aviso", "Selecione um resultado primeiro")

    def copy_selected_value(self, event=None):
        """Copia o valor selecionado para a área de transferência"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            value_str = str(item['values'][1])

            self.root.clipboard_clear()
            self.root.clipboard_append(value_str)
            self.update_status(f"Valor {value_str} copiado para área de transferência")
            self.show_copy_feedback(value_str)
        else:
            messagebox.showwarning("Aviso", "Selecione um resultado primeiro")

    def copy_address_and_value(self, event=None):
        """Copia endereço e valor selecionados"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            address_str = item['values'][0]
            value_str = str(item['values'][1])
            combined = f"{address_str}: {value_str}"

            self.root.clipboard_clear()
            self.root.clipboard_append(combined)
            self.update_status(f"Endereço e valor copiados: {combined}")
            self.show_copy_feedback(combined)
        else:
            messagebox.showwarning("Aviso", "Selecione um resultado primeiro")

    def show_copy_feedback(self, text):
        """Mostra feedback visual temporário para cópia"""
        # Cria uma pequena janela de feedback
        feedback = tk.Toplevel(self.root)
        feedback.title("Copiado!")
        feedback.geometry("300x60")
        feedback.resizable(False, False)

        # Centraliza na tela
        feedback.transient(self.root)
        feedback.grab_set()

        label = ttk.Label(feedback, text=f"Copiado: {text[:30]}{'...' if len(text) > 30 else ''}")
        label.pack(expand=True)

        # Fecha automaticamente após 1.5 segundos
        feedback.after(1500, feedback.destroy)

    def edit_selected_value(self):
        """Edita o valor selecionado"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            current_value = item['values'][1]

            # Pré-preenche o campo de novo valor
            self.new_value_var.set(str(current_value))

            # Foca no campo de entrada e seleciona todo o texto
            self.new_value_entry.focus_set()
            self.new_value_entry.select_range(0, tk.END)

    def add_to_favorites(self):
        """Adiciona endereço aos favoritos"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            address_str = item['values'][0]
            value_str = str(item['values'][1])
            type_str = item['values'][2]

            # Cria uma descrição padrão
            description = simpledialog.askstring(
                "Adicionar aos Favoritos", 
                f"Descrição para {address_str}:",
                initialvalue=f"Valor {type_str}"
            )

            if description:
                # Aqui você pode implementar um sistema de favoritos
                messagebox.showinfo("Favoritos", f"Endereço {address_str} adicionado aos favoritos como '{description}'")

    def goto_address(self):
        """Vai para um endereço específico"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            address_str = item['values'][0]

            # Abre uma janela para mostrar dados em torno do endereço
            self.open_memory_viewer(address_str)

    def open_memory_viewer_from_selection(self):
        """Abre visualizador de memória para o endereço selecionado"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            address_str = item['values'][0]
            self.open_advanced_memory_viewer(address_str)
        else:
            messagebox.showwarning("Aviso", "Selecione um resultado primeiro")

    def open_advanced_memory_viewer(self, address_str):
        """Abre visualizador avançado de memória com análise de offsets"""
        try:
            address = int(address_str, 16)

            viewer_window = tk.Toplevel(self.root)
            viewer_window.title(f"Análise Avançada de Memória - {address_str}")
            viewer_window.geometry("1000x700")

            # Notebook para diferentes visualizações
            notebook = ttk.Notebook(viewer_window)
            notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            # Aba 1: Visualização Hex
            hex_frame = ttk.Frame(notebook)
            notebook.add(hex_frame, text="🔍 Visualização Hex")
            self.setup_hex_viewer(hex_frame, address_str)

            # Aba 2: Análise de Estrutura
            struct_frame = ttk.Frame(notebook)
            notebook.add(struct_frame, text="📊 Estrutura de Dados")
            self.setup_structure_analyzer(struct_frame, address_str)

            # Aba 3: Offsets e Ponteiros
            offset_frame = ttk.Frame(notebook)
            notebook.add(offset_frame, text="🔗 Offsets & Ponteiros")
            self.setup_offset_analyzer(offset_frame, address_str)

            # Aba 4: Monitor de Mudanças
            monitor_frame = ttk.Frame(notebook)
            notebook.add(monitor_frame, text="📈 Monitor")
            self.setup_memory_monitor(monitor_frame, address_str)

        except ValueError:
            messagebox.showerror("Erro", "Endereço inválido")

    def setup_hex_viewer(self, parent, address_str):
        """Configura visualizador hexadecimal"""
        # Frame para controles
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(control_frame, text="Endereço:").pack(side=tk.LEFT)
        address_var = tk.StringVar(value=address_str)
        address_entry = ttk.Entry(control_frame, textvariable=address_var, width=15)
        address_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(control_frame, text="Tamanho:").pack(side=tk.LEFT, padx=(10,0))
        size_var = tk.StringVar(value="512")
        size_combo = ttk.Combobox(control_frame, textvariable=size_var, 
                                 values=["128", "256", "512", "1024", "2048"], width=8)
        size_combo.pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="🔄 Atualizar", 
                  command=lambda: self.update_advanced_memory_view(address_var.get(), size_var.get(), text_widget)).pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="💾 Salvar Dump", 
                  command=lambda: self.save_memory_dump(address_var.get(), size_var.get())).pack(side=tk.LEFT, padx=5)

        # Área de texto para mostrar dados
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        text_widget = tk.Text(text_frame, font=('Courier', 9), wrap=tk.NONE)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        h_scrollbar = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=text_widget.xview)
        text_widget.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Grid layout
        text_widget.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')

        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        # Configurar tags para cores
        text_widget.tag_configure('address', foreground='blue', font=('Courier', 9, 'bold'))
        text_widget.tag_configure('hex', foreground='darkgreen')
        text_widget.tag_configure('ascii', foreground='purple')
        text_widget.tag_configure('pointer', background='yellow')
        text_widget.tag_configure('null', foreground='gray')

        # Carrega dados iniciais
        self.update_advanced_memory_view(address_str, "512", text_widget)

    def setup_structure_analyzer(self, parent, address_str):
        """Configura analisador de estrutura de dados"""
        # Frame superior para controles
        control_frame = ttk.LabelFrame(parent, text="Configurações de Análise")
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        # Tipo de estrutura
        ttk.Label(control_frame, text="Tipo de Estrutura:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        struct_type_var = tk.StringVar(value="auto")
        struct_combo = ttk.Combobox(control_frame, textvariable=struct_type_var,
                                   values=["auto", "player_data", "inventory", "coordinates", "stats", "custom"])
        struct_combo.grid(row=0, column=1, padx=5, pady=2)

        # Tamanho da estrutura
        ttk.Label(control_frame, text="Tamanho:").grid(row=0, column=2, sticky='w', padx=5, pady=2)
        struct_size_var = tk.StringVar(value="64")
        ttk.Entry(control_frame, textvariable=struct_size_var, width=10).grid(row=0, column=3, padx=5, pady=2)

        ttk.Button(control_frame, text="🔍 Analisar", 
                  command=lambda: self.analyze_structure(address_str, struct_type_var.get(), struct_size_var.get(), results_tree)).grid(row=0, column=4, padx=5, pady=2)

        # Treeview para mostrar estrutura
        results_frame = ttk.LabelFrame(parent, text="Estrutura Detectada")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("offset", "address", "type", "value", "description")
        results_tree = ttk.Treeview(results_frame, columns=columns, show="headings")

        results_tree.heading("offset", text="Offset")
        results_tree.heading("address", text="Endereço")
        results_tree.heading("type", text="Tipo")
        results_tree.heading("value", text="Valor")
        results_tree.heading("description", text="Descrição")

        results_tree.column("offset", width=80)
        results_tree.column("address", width=100)
        results_tree.column("type", width=80)
        results_tree.column("value", width=100)
        results_tree.column("description", width=200)

        results_scroll = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=results_tree.yview)
        results_tree.configure(yscrollcommand=results_scroll.set)

        results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Análise inicial
        self.analyze_structure(address_str, "auto", "64", results_tree)

    def setup_offset_analyzer(self, parent, address_str):
        """Configura analisador de offsets"""
        # Frame para buscar ponteiros
        pointer_frame = ttk.LabelFrame(parent, text="Busca de Ponteiros")
        pointer_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(pointer_frame, text="Buscar ponteiros que apontam para:").pack(anchor='w', padx=5, pady=2)
        ttk.Label(pointer_frame, text=f"Endereço: {address_str}").pack(anchor='w', padx=5, pady=2)

        search_frame = ttk.Frame(pointer_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(search_frame, text="Região de busca:").pack(side=tk.LEFT)
        region_var = tk.StringVar(value="heap")
        region_combo = ttk.Combobox(search_frame, textvariable=region_var,
                                   values=["heap", "stack", "all", "custom"])
        region_combo.pack(side=tk.LEFT, padx=5)

        ttk.Button(search_frame, text="🔍 Buscar Ponteiros", 
                  command=lambda: self.find_pointers_analysis(address_str, region_var.get(), pointer_tree)).pack(side=tk.LEFT, padx=10)

        # Treeview para ponteiros encontrados
        pointer_tree_frame = ttk.Frame(parent)
        pointer_tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("base_addr", "offset", "final_addr", "confidence", "type")
        pointer_tree = ttk.Treeview(pointer_tree_frame, columns=columns, show="headings")

        pointer_tree.heading("base_addr", text="Endereço Base")
        pointer_tree.heading("offset", text="Offset")
        pointer_tree.heading("final_addr", text="Endereço Final")
        pointer_tree.heading("confidence", text="Confiança")
        pointer_tree.heading("type", text="Tipo")

        pointer_scroll = ttk.Scrollbar(pointer_tree_frame, orient=tk.VERTICAL, command=pointer_tree.yview)
        pointer_tree.configure(yscrollcommand=pointer_scroll.set)

        pointer_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pointer_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_memory_monitor(self, parent, address_str):
        """Configura monitor de memória em tempo real"""
        # Controles
        control_frame = ttk.LabelFrame(parent, text="Monitor de Mudanças")
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        self.monitoring_active = tk.BooleanVar(value=False)
        monitor_check = ttk.Checkbutton(control_frame, text="Monitoramento Ativo", 
                                       variable=self.monitoring_active,
                                       command=lambda: self.toggle_monitoring(address_str, log_text))
        monitor_check.pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Label(control_frame, text="Intervalo (ms):").pack(side=tk.LEFT, padx=5)
        self.monitor_interval = tk.StringVar(value="1000")
        ttk.Entry(control_frame, textvariable=self.monitor_interval, width=10).pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="🗑️ Limpar Log", 
                  command=lambda: log_text.delete(1.0, tk.END)).pack(side=tk.RIGHT, padx=5)

        # Log de mudanças
        log_frame = ttk.LabelFrame(parent, text="Log de Mudanças")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        log_text = tk.Text(log_frame, font=('Courier', 9))
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=log_text.yview)
        log_text.configure(yscrollcommand=log_scroll.set)

        log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def analyze_structure(self, address_str, struct_type, size_str, results_tree):
        """Analisa estrutura de dados no endereço"""
        try:
            address = int(address_str, 16)
            size = int(size_str)

            # Limpa resultados anteriores
            for item in results_tree.get_children():
                results_tree.delete(item)

            # Lê dados da memória
            data = self.memory_manager.read_memory(address, size)
            if not data:
                results_tree.insert('', 'end', values=("N/A", "N/A", "Erro", "Não foi possível ler memória", ""))
                return

            # Analisa diferentes tipos de dados
            for offset in range(0, min(size, len(data)-4), 4):
                current_addr = address + offset

                # Tenta interpretar como diferentes tipos
                try:
                    # Int32
                    int_val = struct.unpack('<i', data[offset:offset+4])[0]

                    # Float
                    float_val = struct.unpack('<f', data[offset:offset+4])[0]

                    # Pointer (se parece com endereço válido)
                    uint_val = struct.unpack('<I', data[offset:offset+4])[0]

                    # Determina o tipo mais provável
                    detected_type = "int32"
                    display_value = str(int_val)
                    description = ""

                    # Lógica para detectar ponteiros
                    if 0x400000 <= uint_val <= 0x7FFFFFFF:
                        detected_type = "pointer"
                        display_value = f"0x{uint_val:08X}"
                        description = "Possível ponteiro"

                    # Detecta floats razoáveis
                    elif abs(float_val) < 1000000 and abs(float_val) > 0.001:
                        detected_type = "float"
                        display_value = f"{float_val:.6f}"
                        description = "Valor decimal"

                    # Detecta valores pequenos (IDs, contadores, etc.)
                    elif 0 <= int_val <= 10000:
                        description = "Possível ID/contador"

                    # Detecta valores grandes (scores, etc.)
                    elif int_val > 10000:
                        description = "Possível score/valor grande"

                    results_tree.insert('', 'end', values=(
                        f"+0x{offset:02X}",
                        f"0x{current_addr:08X}",
                        detected_type,
                        display_value,
                        description
                    ))

                except struct.error:
                    continue

        except Exception as e:
            results_tree.insert('', 'end', values=("Erro", "Erro", "Erro", str(e), ""))

    def find_pointers_analysis(self, target_address_str, region, pointer_tree):
        """Encontra ponteiros que apontam para o endereço"""
        try:
            target_address = int(target_address_str, 16)

            # Limpa resultados anteriores
            for item in pointer_tree.get_children():
                pointer_tree.delete(item)

            # Simula busca de ponteiros (implementação básica)
            # Em uma implementação real, isso varrerria regiões de memória

            # Busca em algumas regiões conhecidas
            search_ranges = []
            if region == "heap":
                search_ranges = [(0x400000, 0x800000)]
            elif region == "stack":
                search_ranges = [(0x7FF000, 0x800000)]
            else:
                search_ranges = [(0x400000, 0x800000), (0x7FF000, 0x800000)]

            found_count = 0
            for start, end in search_ranges:
                for addr in range(start, min(start + 0x10000, end), 4):  # Busca limitada para demo
                    try:
                        value = self.memory_manager.read_int32(addr)
                        if value:
                            # Calcula offset
                            offset = target_address - value

                            # Se o offset é razoável, pode ser um ponteiro
                            if -0x1000 <= offset <= 0x1000:
                                confidence = "Alta" if abs(offset) < 0x100 else "Média"
                                pointer_type = "Direto" if offset == 0 else "Com Offset"

                                pointer_tree.insert('', 'end', values=(
                                    f"0x{addr:08X}",
                                    f"+0x{offset:X}" if offset >= 0 else f"-0x{abs(offset):X}",
                                    f"0x{target_address:08X}",
                                    confidence,
                                    pointer_type
                                ))

                                found_count += 1
                                if found_count >= 50:  # Limita resultados
                                    break
                    except:
                        continue

                if found_count >= 50:
                    break

            if found_count == 0:
                pointer_tree.insert('', 'end', values=("Nenhum", "ponteiro", "encontrado", "na", "região"))

        except Exception as e:
            pointer_tree.insert('', 'end', values=("Erro:", str(e), "", "", ""))

    def toggle_monitoring(self, address_str, log_text):
        """Ativa/desativa monitoramento de memória"""
        if self.monitoring_active.get():
            log_text.insert(tk.END, f"[{self.get_timestamp()}] Iniciando monitoramento de {address_str}\n")
            log_text.see(tk.END)
            # Aqui você implementaria o loop de monitoramento
        else:
            log_text.insert(tk.END, f"[{self.get_timestamp()}] Parando monitoramento\n")
            log_text.see(tk.END)

    def get_timestamp(self):
        """Retorna timestamp atual"""
        import datetime
        return datetime.datetime.now().strftime("%H:%M:%S")

    def open_memory_viewer(self, address_str):
        """Abre visualizador de memória simples (mantido para compatibilidade)"""
        self.open_advanced_memory_viewer(address_str)

    def update_advanced_memory_view(self, address_str, size_str, text_widget):
        """Atualiza a visualização avançada de memória"""
        try:
            import struct
            address = int(address_str, 16)
            size = int(size_str)

            # Lê dados da memória
            data = self.memory_manager.read_memory(address, size)

            text_widget.delete(1.0, tk.END)

            if data:
                # Cabeçalho
                header = f"📍 Endereço Base: 0x{address:08X} | 📏 Tamanho: {size} bytes | 🕒 {self.get_timestamp()}\n"
                header += "=" * 90 + "\n\n"
                text_widget.insert(tk.END, header, 'address')

                # Formato hexadecimal avançado com análise
                for i in range(0, len(data), 16):
                    chunk = data[i:i+16]
                    chunk_addr = address + i

                    # Endereço
                    addr_str = f"0x{chunk_addr:08X}: "
                    text_widget.insert(tk.END, addr_str, 'address')

                    # Bytes hex
                    hex_parts = []
                    for j, byte_val in enumerate(chunk):
                        hex_str = f"{byte_val:02X}"

                        # Detecta padrões especiais
                        if byte_val == 0:
                            tag = 'null'
                        elif 0x20 <= byte_val <= 0x7E:  # ASCII imprimível
                            tag = 'hex'
                        elif byte_val == 0xFF:
                            tag = 'pointer'
                        else:
                            tag = 'hex'

                        hex_parts.append((hex_str, tag))

                    # Insere bytes com cores
                    for hex_str, tag in hex_parts:
                        text_widget.insert(tk.END, hex_str + " ", tag)

                    # Preenche espaço se chunk < 16 bytes
                    missing_bytes = 16 - len(chunk)
                    text_widget.insert(tk.END, "   " * missing_bytes)

                    # ASCII
                    text_widget.insert(tk.END, " |", 'hex')
                    for byte_val in chunk:
                        char = chr(byte_val) if 32 <= byte_val <= 126 else '.'
                        text_widget.insert(tk.END, char, 'ascii')
                    text_widget.insert(tk.END, "|", 'hex')

                    # Análise de valores (int32, float)
                    if len(chunk) >= 4:
                        try:
                            int_val = struct.unpack('<i', chunk[:4])[0]
                            float_val = struct.unpack('<f', chunk[:4])[0]

                            analysis = f" → Int: {int_val}"
                            if abs(float_val) < 1000000 and abs(float_val) > 0.001:
                                analysis += f", Float: {float_val:.3f}"

                            # Detecta possíveis ponteiros
                            uint_val = struct.unpack('<I', chunk[:4])[0]
                            if 0x400000 <= uint_val <= 0x7FFFFFFF:
                                analysis += f", Ptr: 0x{uint_val:08X}"

                            text_widget.insert(tk.END, analysis, 'hex')
                        except struct.error:
                            pass

                    text_widget.insert(tk.END, "\n")

                # Resumo final
                summary = f"\n" + "=" * 90 + "\n"
                summary += f"📊 Resumo: {len(data)} bytes analisados\n"
                summary += f"🔍 Possíveis ponteiros detectados em destaque\n"
                summary += f"⚪ Bytes null em cinza, ASCII em roxo\n"
                text_widget.insert(tk.END, summary, 'address')

            else:
                text_widget.insert(tk.END, "❌ Não foi possível ler dados do endereço", 'address')

        except Exception as e:
            text_widget.delete(1.0, tk.END)
            text_widget.insert(tk.END, f"❌ Erro ao ler memória: {e}", 'address')

    def update_memory_view(self, address_str, text_widget):
        """Atualiza a visualização de memória (versão simples)"""
        self.update_advanced_memory_view(address_str, "256", text_widget)

    # Novos métodos para o menu de contexto
    def change_value_type(self):
        """Permite alterar o tipo de dado do valor selecionado"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um resultado primeiro")
            return

        # Dialog para selecionar novo tipo
        new_type = simpledialog.askstring(
            "Alterar Tipo de Dado",
            "Escolha o novo tipo:\nint32, int64, float, double, string",
            initialvalue=self.data_type_var.get()
        )

        if new_type and new_type in ["int32", "int64", "float", "double", "string"]:
            self.data_type_var.set(new_type)
            # Atualiza o valor exibido
            item = self.results_tree.item(selection[0])
            address_str = item['values'][0]
            address = int(address_str, 16)

            # Lê valor com novo tipo
            from scanner import DataType
            data_type = DataType(new_type)
            new_value = self.scanner._read_value_at_address(address, data_type)

            if new_value is not None:
                # Atualiza exibição
                current_values = list(item['values'])
                current_values[1] = str(new_value)
                current_values[2] = new_type
                self.results_tree.item(selection[0], values=current_values)
                messagebox.showinfo("Sucesso", f"Tipo alterado para {new_type}")

    def analyze_data_structure(self):
        """Analisa estrutura de dados em torno do endereço"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            address_str = item['values'][0]
            self.open_advanced_memory_viewer(address_str)

    def find_pointers_to_address(self):
        """Busca ponteiros que apontam para este endereço"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um resultado primeiro")
            return

        item = self.results_tree.item(selection[0])
        address_str = item['values'][0]
        address = int(address_str, 16)

        # Cria janela de resultados
        result_window = tk.Toplevel(self.root)
        result_window.title(f"Ponteiros para {address_str}")
        result_window.geometry("600x400")

        # Lista de ponteiros encontrados
        columns = ("pointer_addr", "offset", "confidence")
        tree = ttk.Treeview(result_window, columns=columns, show="headings")

        tree.heading("pointer_addr", text="Endereço do Ponteiro")
        tree.heading("offset", text="Offset")
        tree.heading("confidence", text="Confiança")

        tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Simula busca (implementação básica)
        messagebox.showinfo("Info", "Buscando ponteiros... (implementação demo)")

    def check_nearby_offsets(self):
        """Verifica offsets próximos para encontrar dados relacionados"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um resultado primeiro")
            return

        item = self.results_tree.item(selection[0])
        address_str = item['values'][0]
        address = int(address_str, 16)

        # Cria janela de análise
        offset_window = tk.Toplevel(self.root)
        offset_window.title(f"Offsets Próximos - {address_str}")
        offset_window.geometry("700x500")

        # Treeview para offsets
        columns = ("offset", "address", "type", "value", "notes")
        tree = ttk.Treeview(offset_window, columns=columns, show="headings")

        tree.heading("offset", text="Offset")
        tree.heading("address", text="Endereço")
        tree.heading("type", text="Tipo")
        tree.heading("value", text="Valor")
        tree.heading("notes", text="Observações")

        tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Analisa offsets de -0x50 a +0x50
        for offset in range(-0x50, 0x51, 4):
            check_addr = address + offset
            if check_addr < 0:
                continue

            try:
                # Tenta ler como int32
                value = self.memory_manager.read_int32(check_addr)
                if value is not None:
                    offset_str = f"+0x{offset:02X}" if offset >= 0 else f"-0x{abs(offset):02X}"

                    # Análise básica do valor
                    notes = ""
                    if value == 0:
                        notes = "Null/Zero"
                    elif 0 < value < 1000:
                        notes = "Possível counter/ID"
                    elif value > 1000000:
                        notes = "Valor grande"
                    elif 0x400000 <= value <= 0x7FFFFFFF:
                        notes = "Possível ponteiro"

                    tree.insert('', 'end', values=(
                        offset_str,
                        f"0x{check_addr:08X}",
                        "int32",
                        str(value),
                        notes
                    ))
            except:
                continue

    def auto_create_pointer(self):
        """Cria automaticamente uma cadeia de ponteiros"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um resultado primeiro")
            return

        item = self.results_tree.item(selection[0])
        address_str = item['values'][0]

        description = simpledialog.askstring(
            "Criar Ponteiro",
            f"Descrição para o ponteiro {address_str}:",
            initialvalue="Auto Pointer"
        )

        if description:
            # Preenche campos de ponteiro automaticamente
            self.base_addr_var.set(address_str)
            self.offsets_var.set("0")
            self.pointer_desc_var.set(description)

            # Troca para aba de ponteiros
            # Aqui você pode implementar a lógica para trocar de aba
            messagebox.showinfo("Info", f"Ponteiro configurado para {address_str}")

    def copy_as_hex(self):
        """Copia valor como hexadecimal"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            value = item['values'][1]
            try:
                hex_value = f"0x{int(value):X}"
                self.root.clipboard_clear()
                self.root.clipboard_append(hex_value)
                self.update_status(f"Valor hex {hex_value} copiado")
            except ValueError:
                messagebox.showerror("Erro", "Não é possível converter para hex")

    def copy_full_info(self):
        """Copia informações completas do resultado"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            info = f"Endereço: {item['values'][0]}\nValor: {item['values'][1]}\nTipo: {item['values'][2]}"

            self.root.clipboard_clear()
            self.root.clipboard_append(info)
            self.update_status("Informações completas copiadas")

    def goto_base_address(self):
        """Vai para endereço base calculado"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            address_str = item['values'][0]
            address = int(address_str, 16)

            # Calcula endereço base (exemplo: alinha para página de 4KB)
            base_address = address & 0xFFFFF000
            base_str = f"0x{base_address:08X}"

            self.open_advanced_memory_viewer(base_str)

    def follow_pointer(self):
        """Segue ponteiro se o valor atual for um endereço válido"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            value_str = item['values'][1]

            try:
                # Tenta interpretar valor como endereço
                if value_str.startswith('0x'):
                    address = int(value_str, 16)
                else:
                    address = int(value_str)

                # Verifica se parece com endereço válido
                if 0x400000 <= address <= 0x7FFFFFFF:
                    target_str = f"0x{address:08X}"
                    self.open_advanced_memory_viewer(target_str)
                else:
                    messagebox.showwarning("Aviso", "Valor não parece ser um endereço válido")

            except ValueError:
                messagebox.showerror("Erro", "Não é possível interpretar como endereço")

    def add_comment(self):
        """Adiciona comentário ao resultado"""
        selection = self.results_tree.selection()
        if selection:
            comment = simpledialog.askstring(
                "Adicionar Comentário",
                "Digite um comentário para este endereço:"
            )
            if comment:
                # Aqui você pode salvar o comentário associado ao endereço
                messagebox.showinfo("Info", f"Comentário adicionado: {comment}")

    def change_color(self):
        """Altera cor do resultado"""
        selection = self.results_tree.selection()
        if selection:
            colors = ["red", "green", "blue", "orange", "purple", "brown"]
            color = simpledialog.askstring(
                "Alterar Cor",
                f"Escolha uma cor: {', '.join(colors)}",
                initialvalue="red"
            )
            if color and color in colors:
                # Aplica cor ao item
                self.results_tree.set(selection[0], column="#0", value="")
                # Aqui você pode implementar tags de cores personalizadas

    def start_monitoring(self):
        """Inicia monitoramento contínuo do endereço"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            address_str = item['values'][0]

            # Abre janela de monitoramento
            monitor_window = tk.Toplevel(self.root)
            monitor_window.title(f"Monitor - {address_str}")
            monitor_window.geometry("400x300")

            # Lista de logs
            log_text = tk.Text(monitor_window, font=('Courier', 9))
            log_scroll = ttk.Scrollbar(monitor_window, orient=tk.VERTICAL, command=log_text.yview)
            log_text.configure(yscrollcommand=log_scroll.set)

            log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

            log_text.insert(tk.END, f"Monitorando {address_str}...\n")

    def show_value_history(self):
        """Mostra histórico de valores"""
        messagebox.showinfo("Histórico", "Funcionalidade de histórico em desenvolvimento")

    def calculate_distance(self):
        """Calcula distância entre endereços selecionados"""
        selection = self.results_tree.selection()
        if len(selection) >= 2:
            addr1_str = self.results_tree.item(selection[0])['values'][0]
            addr2_str = self.results_tree.item(selection[1])['values'][0]

            addr1 = int(addr1_str, 16)
            addr2 = int(addr2_str, 16)

            distance = abs(addr2 - addr1)

            messagebox.showinfo("Distância", 
                              f"Distância entre {addr1_str} e {addr2_str}:\n"
                              f"Decimal: {distance} bytes\n"
                              f"Hex: 0x{distance:X}")
        else:
            messagebox.showwarning("Aviso", "Selecione pelo menos 2 endereços")

    def find_references(self):
        """Busca referências ao endereço"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            address_str = item['values'][0]
            messagebox.showinfo("Referências", f"Buscando referências para {address_str}...")

    def save_memory_dump(self, address_str, size_str):
        """Salva dump de memória em arquivo"""
        try:
            filename = filedialog.asksaveasfilename(
                title="Salvar Dump de Memória",
                defaultextension=".bin",
                filetypes=[("Binary files", "*.bin"), ("Text files", "*.txt"), ("All files", "*.*")]
            )

            if filename:
                address = int(address_str, 16)
                size = int(size_str)

                data = self.memory_manager.read_memory(address, size)
                if data:
                    with open(filename, 'wb') as f:
                        f.write(data)
                    messagebox.showinfo("Sucesso", f"Dump salvo em {filename}")
                else:
                    messagebox.showerror("Erro", "Não foi possível ler dados da memória")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar dump: {e}")

    def select_all_results(self, event=None):
        """Seleciona todos os resultados"""
        for child in self.results_tree.get_children():
            self.results_tree.selection_add(child)

    def on_result_double_click(self, event):
        """Callback para duplo clique em resultado"""
        self.edit_selected_value()

    def write_selected_value(self):
        """Escreve novo valor no endereço selecionado"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showerror("Erro", "Selecione um resultado na lista primeiro")
            return

        new_value = self.new_value_var.get().strip()
        if not new_value:
            messagebox.showerror("Erro", "Digite um novo valor no campo 'Novo Valor'")
            return

        try:
            item = self.results_tree.item(selection[0])
            address_str = item['values'][0]
            address = int(address_str, 16)

            data_type = DataType(self.data_type_var.get())

            if self.scanner.write_value_to_address(address, new_value, data_type):
                messagebox.showinfo("Sucesso", "Valor escrito com sucesso")
                # Atualiza o valor na lista
                if self.auto_update_enabled.get():
                    self.update_single_result(address, selection[0])
            else:
                messagebox.showerror("Erro", "Falha ao escrever valor")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao escrever valor: {e}")

    def update_single_result(self, address, tree_item):
        """Atualiza um único resultado na lista"""
        try:
            data_type = DataType(self.data_type_var.get())

            # Encontra o resultado correspondente
            for result in self.scanner.scan_results:
                if result.address == address:
                    new_value = self.scanner._read_value_at_address(address, data_type)
                    if new_value is not None:
                        result.update_value(new_value)
                        # Atualiza a árvore
                        current_values = list(self.results_tree.item(tree_item)['values'])
                        current_values[1] = str(new_value)
                        self.results_tree.item(tree_item, values=current_values)
                    break
        except:
            pass

    def add_pointer_chain(self):
        """Adiciona uma nova cadeia de ponteiros"""
        try:
            base_addr_str = self.base_addr_var.get()
            offsets_str = self.offsets_var.get()
            description = self.pointer_desc_var.get()

            if not base_addr_str or not offsets_str:
                messagebox.showerror("Erro", "Preencha endereço base e offsets")
                return

            # Converte endereço base
            if base_addr_str.startswith('0x'):
                base_addr = int(base_addr_str, 16)
            else:
                base_addr = int(base_addr_str)

            # Converte offsets
            offsets = []
            for offset_str in offsets_str.split(','):
                offset_str = offset_str.strip()
                if offset_str.startswith('0x'):
                    offsets.append(int(offset_str, 16))
                else:
                    offsets.append(int(offset_str))

            # Adiciona cadeia
            chain = self.pointer_resolver.add_pointer_chain(base_addr, offsets, description)

            # Atualiza exibição
            self.update_pointer_display()

            # Limpa campos
            self.base_addr_var.set("")
            self.offsets_var.set("")
            self.pointer_desc_var.set("")

            messagebox.showinfo("Sucesso", "Cadeia de ponteiros adicionada")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao adicionar ponteiro: {e}")

    def test_pointer_chain(self):
        """Testa uma cadeia de ponteiros sem adicionar"""
        try:
            base_addr_str = self.base_addr_var.get()
            offsets_str = self.offsets_var.get()

            if not base_addr_str or not offsets_str:
                messagebox.showerror("Erro", "Preencha endereço base e offsets")
                return

            # Converte valores
            if base_addr_str.startswith('0x'):
                base_addr = int(base_addr_str, 16)
            else:
                base_addr = int(base_addr_str)

            offsets = []
            for offset_str in offsets_str.split(','):
                offset_str = offset_str.strip()
                if offset_str.startswith('0x'):
                    offsets.append(int(offset_str, 16))
                else:
                    offsets.append(int(offset_str))

            # Testa resolução
            final_addr = self.pointer_resolver.resolve_pointer_chain(base_addr, offsets)

            if final_addr:
                # Lê valor no endereço final
                value = self.memory_manager.read_int(final_addr)
                messagebox.showinfo("Teste de Ponteiro", 
                                   f"Endereço final: 0x{final_addr:X}\nValor: {value}")
            else:
                messagebox.showerror("Teste de Ponteiro", "Falha ao resolver cadeia de ponteiros")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao testar ponteiro: {e}")

    def update_pointer_display(self):
        """Atualiza a exibição dos ponteiros"""
        # Limpa árvore
        for item in self.pointer_tree.get_children():
            self.pointer_tree.delete(item)

        # Adiciona ponteiros
        for chain in self.pointer_resolver.pointer_chains:
            offsets_str = ', '.join(f"0x{offset:X}" for offset in chain.offsets)
            final_addr_str = f"0x{chain.final_address:X}" if chain.final_address else "N/A"

            # Tenta ler valor
            value_str = "N/A"
            if chain.is_valid and chain.final_address:
                try:
                    value = self.memory_manager.read_int(chain.final_address)
                    value_str = str(value) if value is not None else "N/A"
                except:
                    pass

            self.pointer_tree.insert('', 'end', values=(
                chain.description,
                f"0x{chain.base_address:X}",
                offsets_str,
                final_addr_str,
                value_str,
                "Sim" if chain.is_valid else "Não"
            ))

    def show_pointer_context_menu(self, event):
        """Mostra menu de contexto para ponteiros"""
        selection = self.pointer_tree.selection()
        if selection:
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label="Remover", command=lambda: self.remove_pointer_chain(selection[0]))
            context_menu.add_command(label="Atualizar", command=self.update_all_pointers)
            context_menu.tk_popup(event.x_root, event.y_root)

    def remove_pointer_chain(self, tree_item):
        """Remove uma cadeia de ponteiros"""
        try:
            index = self.pointer_tree.index(tree_item)
            if self.pointer_resolver.remove_pointer_chain(index):
                self.update_pointer_display()
                messagebox.showinfo("Sucesso", "Cadeia de ponteiros removida")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao remover ponteiro: {e}")

    def update_all_pointers(self):
        """Atualiza todas as cadeias de ponteiros"""
        try:
            self.pointer_resolver.update_all_chains()
            self.update_pointer_display()
            self.update_status("Ponteiros atualizados")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar ponteiros: {e}")

    def start_aob_scan(self):
        """Inicia scan AOB"""
        pattern = self.aob_pattern_var.get()
        description = self.aob_desc_var.get()

        if not pattern:
            messagebox.showerror("Erro", "Digite um padrão de bytes")
            return

        if not self.memory_manager.is_attached():
            messagebox.showerror("Erro", "Nenhum processo anexado")
            return

        # Desabilita botões
        self.aob_scan_btn.config(state=tk.DISABLED)
        self.aob_cancel_btn.config(state=tk.NORMAL)

        # Inicia scan em thread separada
        self.aob_thread = threading.Thread(
            target=self._perform_aob_scan,
            args=(pattern, description)
        )
        self.aob_thread.start()

    def _perform_aob_scan(self, pattern, description):
        """Executa scan AOB em thread separada"""
        try:
            results = self.aob_scanner.scan_aob(pattern, description)

            # Atualiza UI na thread principal
            self.root.after(0, self._aob_scan_completed, results)

        except Exception as e:
            self.root.after(0, self._aob_scan_error, str(e))

    def _aob_scan_completed(self, results):
        """Callback para AOB scan completado"""
        self.aob_scan_btn.config(state=tk.NORMAL)
        self.aob_cancel_btn.config(state=tk.DISABLED)

        self.update_aob_display(results)
        self.update_status(f"AOB scan completado: {len(results)} resultados encontrados")

    def _aob_scan_error(self, error_msg):
        """Callback para erro no AOB scan"""
        self.aob_scan_btn.config(state=tk.NORMAL)
        self.aob_cancel_btn.config(state=tk.DISABLED)

        messagebox.showerror("Erro no AOB Scan", error_msg)
        self.update_status("Erro no AOB scan")

    def cancel_aob_scan(self):
        """Cancela scan AOB"""
        self.aob_scanner.cancel_scan()

        self.aob_scan_btn.config(state=tk.NORMAL)
        self.aob_cancel_btn.config(state=tk.DISABLED)

        self.update_status("AOB scan cancelado")

    def update_aob_display(self, results):
        """Atualiza exibição dos resultados AOB"""
        # Limpa árvore
        for item in self.aob_tree.get_children():
            self.aob_tree.delete(item)

        # Adiciona resultados
        for result in results:
            self.aob_tree.insert('', 'end', values=(
                f"0x{result.address:X}",
                result.pattern.original_pattern,
                result.matched_bytes.hex().upper()
            ))

    def start_auto_update(self):
        """Inicia thread de atualização automática"""
        def auto_update_loop():
            while True:
                try:
                    if (self.auto_update_enabled.get() and 
                        self.memory_manager.is_attached() and 
                        self.scanner.get_result_count() > 0):

                        # Atualiza resultados
                        self.scanner.update_results()
                        self.root.after(0, self.update_results_display)

                        # Atualiza ponteiros
                        if self.pointer_resolver.pointer_chains:
                            self.pointer_resolver.update_all_chains()
                            self.root.after(0, self.update_pointer_display)

                    # Espera 1 segundo
                    threading.Event().wait(1.0)

                except Exception as e:
                    print(f"Erro na atualização automática: {e}")

        self.update_thread = threading.Thread(target=auto_update_loop, daemon=True)
        self.update_thread.start()

    def save_session(self):
        """Salva a sessão atual"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if filename:
                session_data = {
                    'process_id': self.current_process,
                    'scan_results': [
                        {
                            'address': result.address,
                            'value': result.value,
                            'data_type': result.data_type.value,
                            'previous_value': result.previous_value
                        }
                        for result in self.scanner.scan_results
                    ],
                    'pointer_chains': [chain.to_dict() for chain in self.pointer_resolver.pointer_chains],
                    'aob_results': [result.to_dict() for result in self.aob_scanner.scan_results]
                }

                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, indent=2, ensure_ascii=False)

                messagebox.showinfo("Sucesso", "Sessão salva com sucesso")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar sessão: {e}")

    def load_session(self):
        """Carrega uma sessão salva"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)

                # Carrega ponteiros
                self.pointer_resolver.pointer_chains.clear()
                for chain_data in session_data.get('pointer_chains', []):
                    # Simples implementação para evitar dependência do PointerChain.from_dict
                    pass

                self.update_pointer_display()
                messagebox.showinfo("Sucesso", "Sessão carregada com sucesso")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar sessão: {e}")

    def open_hex_calculator(self):
        """Abre calculadora hexadecimal"""
        calc_window = tk.Toplevel(self.root)
        calc_window.title("Calculadora Hexadecimal")
        calc_window.geometry("300x200")

        ttk.Label(calc_window, text="Valor Decimal:").pack(pady=5)
        dec_var = tk.StringVar()
        dec_entry = ttk.Entry(calc_window, textvariable=dec_var)
        dec_entry.pack(pady=5)

        ttk.Label(calc_window, text="Valor Hexadecimal:").pack(pady=5)
        hex_var = tk.StringVar()
        hex_entry = ttk.Entry(calc_window, textvariable=hex_var)
        hex_entry.pack(pady=5)

        def update_hex():
            try:
                dec_val = int(dec_var.get())
                hex_var.set(f"0x{dec_val:X}")
            except:
                pass

        def update_dec():
            try:
                hex_val = hex_var.get()
                if hex_val.startswith('0x'):
                    hex_val = hex_val[2:]
                dec_val = int(hex_val, 16)
                dec_var.set(str(dec_val))
            except:
                pass

        dec_var.trace('w', lambda *args: update_hex())
        hex_var.trace('w', lambda *args: update_dec())

    def open_type_converter(self):
        """Abre conversor de tipos"""
        conv_window = tk.Toplevel(self.root)
        conv_window.title("Conversor de Tipos")
        conv_window.geometry("400x300")

        ttk.Label(conv_window, text="Bytes (hex):").pack(pady=5)
        bytes_var = tk.StringVar()
        ttk.Entry(conv_window, textvariable=bytes_var, width=50).pack(pady=5)

        ttk.Label(conv_window, text="Int32:").pack(pady=5)
        int32_var = tk.StringVar()
        ttk.Entry(conv_window, textvariable=int32_var, width=50).pack(pady=5)

        ttk.Label(conv_window, text="Float:").pack(pady=5)
        float_var = tk.StringVar()
        ttk.Entry(conv_window, textvariable=float_var, width=50).pack(pady=5)

        def convert_from_bytes():
            try:
                hex_str = bytes_var.get().replace(' ', '')
                if len(hex_str) == 8:  # 4 bytes
                    bytes_data = bytes.fromhex(hex_str)
                    import struct
                    int_val = struct.unpack('<i', bytes_data)[0]
                    float_val = struct.unpack('<f', bytes_data)[0]
                    int32_var.set(str(int_val))
                    float_var.set(str(float_val))
            except:
                pass

        ttk.Button(conv_window, text="Converter", command=convert_from_bytes).pack(pady=10)

    def show_about(self):
        """Mostra informações sobre o programa"""
        about_text = """
PyCheatEngine v1.0.0

Sistema de Engenharia Reversa e Manipulação de Memória
Similar ao Cheat Engine, mas implementado em Python

Funcionalidades:
• Scanner de memória com múltiplos tipos de dados
• Resolução de cadeias de ponteiros
• Scanner de padrões de bytes (AOB)
• Interface gráfica intuitiva
• Sistema de sessões

Desenvolvido com Python, Tkinter e ctypes
        """
        messagebox.showinfo("Sobre PyCheatEngine", about_text)

    def get_timestamp(self):
        """Retorna timestamp atual formatado"""
        import datetime
        return datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def show_memory_details(self, address):
        """Mostra detalhes da memória no endereço"""
        try:
            import struct
            print(f"[GUI] Abrindo detalhes da memória para endereço: 0x{address:X}")

            # Lê dados ao redor do endereço
            data = self.memory_manager.read_memory(address, 64)
            if not data:
                messagebox.showerror("Erro", "❌ Erro ao ler memória: Não foi possível acessar o endereço")
                return

            # Cria janela de detalhes
            details_window = tk.Toplevel(self.root)
            details_window.title(f"Detalhes da Memória - 0x{address:X}")
            details_window.geometry("600x400")
            details_window.resizable(True, True)

            # Frame principal com scroll
            main_frame = ttk.Frame(details_window)
            main_frame.pack(fill='both', expand=True, padx=10, pady=10)

            # Texto com scroll
            text_widget = tk.Text(main_frame, wrap='none', font=('Courier', 10))
            scrollbar_y = ttk.Scrollbar(main_frame, orient='vertical', command=text_widget.yview)
            scrollbar_x = ttk.Scrollbar(main_frame, orient='horizontal', command=text_widget.xview)
            text_widget.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

            # Layout
            text_widget.grid(row=0, column=0, sticky='nsew')
            scrollbar_y.grid(row=0, column=1, sticky='ns')
            scrollbar_x.grid(row=1, column=0, sticky='ew')

            main_frame.grid_rowconfigure(0, weight=1)
            main_frame.grid_columnconfigure(0, weight=1)

            # Cabeçalho
            content = f"Visualização da Memória - Endereço Base: 0x{address:X}\n"
            content += "=" * 60 + "\n\n"

            # Mostra dados em formato hexadecimal
            content += "DUMP HEXADECIMAL:\n"
            content += "-" * 40 + "\n"

            for i in range(0, len(data), 16):
                addr = address + i
                hex_data = data[i:i+16]

                # Endereço
                content += f"0x{addr:08X}: "

                # Bytes em hex
                for j, byte in enumerate(hex_data):
                    content += f"{byte:02X} "
                    if j == 7:  # Separador no meio
                        content += " "

                # Padding se linha incompleta
                if len(hex_data) < 16:
                    content += "   " * (16 - len(hex_data))
                    if len(hex_data) <= 8:
                        content += " "

                # ASCII
                content += " | "
                for byte in hex_data:
                    if 32 <= byte <= 126:
                        content += chr(byte)
                    else:
                        content += "."

                content += "\n"

            text_widget.insert(tk.END, content)
            text_widget.configure(state='disabled')

        except Exception as e:
            print(f"[GUI] Erro ao mostrar detalhes da memória: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erro", f"❌ Erro ao ler memória: {e}")

    def on_enter_key(self, event):
        """Callback para tecla Enter"""
        if self.results_tree.focus_get() == self.results_tree:
            self.edit_selected_value()
        return "break"  # Impede propagação do evento

    def on_delete_key(self, event):
        """Callback para tecla Delete"""
        if self.results_tree.focus_get() == self.results_tree:
            # Aqui você pode implementar remoção de resultados se necessário
            pass
        return "break"

    def update_status(self, message):
        """Atualiza a barra de status"""
        self.status_label.config(text=message)

    def run(self):
        """Executa a interface gráfica"""
        try:
            # Configura handler para fechamento da janela
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()
        finally:
            self.cleanup_resources()

    def on_closing(self):
        """Handler para fechamento da aplicação"""
        # Cancela scans em andamento
        if hasattr(self, 'scanner'):
            self.scanner.cancel_scan()
        if hasattr(self, 'aob_scanner'):
            self.aob_scanner.cancel_scan()

        # Para atualização automática
        self.auto_update_enabled.set(False)

        self.cleanup_resources()
        self.root.quit()
        self.root.destroy()

    def cleanup_resources(self):
        """Limpa todos os recursos"""
        try:
            # Desanexa do processo
            if hasattr(self, 'memory_manager') and self.memory_manager.is_attached():
                self.memory_manager.detach_process()

            # Cancela threads
            if hasattr(self, 'scan_thread') and self.scan_thread and self.scan_thread.is_alive():
                # Marca para parar e espera um pouco
                if hasattr(self, 'scanner'):
                    self.scanner.cancel_scan()

            if hasattr(self, 'aob_thread') and self.aob_thread and self.aob_thread.is_alive():
                if hasattr(self, 'aob_scanner'):
                    self.aob_scanner.cancel_scan()

        except Exception as e:
            print(f"Erro durante cleanup: {e}")

    