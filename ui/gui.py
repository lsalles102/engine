"""
Interface Gráfica para PyCheatEngine
Implementa uma GUI completa usando Tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading
import json
import os
from typing import List, Dict, Any, Optional

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
        self.results_tree.heading("value", text="Valor")
        self.results_tree.heading("type", text="Tipo")
        
        self.results_tree.column("address", width=120)
        self.results_tree.column("value", width=100)
        self.results_tree.column("type", width=80)
        
        # Scrollbar para resultados
        results_scroll = ttk.Scrollbar(results_group, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scroll.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind para duplo clique
        self.results_tree.bind('<Double-1>', self.on_result_double_click)
        
        # Controles de valor
        value_frame = ttk.Frame(right_frame)
        value_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(value_frame, text="Novo Valor:").pack(side=tk.LEFT)
        self.new_value_var = tk.StringVar()
        ttk.Entry(value_frame, textvariable=self.new_value_var, width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(value_frame, text="Escrever Valor", 
                  command=self.write_selected_value).pack(side=tk.LEFT, padx=5)
        
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
                status_msg = f"Primeiro scan completado: {results_count} resultados encontrados"
            else:
                status_msg = f"Próximo scan completado: {results_count} resultados restantes"
                
            print(f"[GUI] {status_msg}")
            self.update_status(status_msg)
            
            # Se não há resultados e não é primeiro scan, sugere dica
            if results_count == 0 and not is_first_scan:
                self.update_status("Nenhum resultado encontrado. Tente alterar o valor no jogo e faça outro scan.")
                
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
        for result in results:
            self.results_tree.insert('', 'end', values=(
                f"0x{result.address:X}",
                str(result.value),
                result.data_type.value
            ))
        
        # Atualiza contador
        total_results = self.scanner.get_result_count()
        if total_results > 1000:
            self.result_count_label.config(text=f"Mostrando 1000 de {total_results} resultados")
        else:
            self.result_count_label.config(text=f"{total_results} resultados")
    
    def clear_results_display(self):
        """Limpa a exibição dos resultados"""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.result_count_label.config(text="")
    
    def on_result_double_click(self, event):
        """Callback para duplo clique em resultado"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            address_str = item['values'][0]
            current_value = item['values'][1]
            
            # Pré-preenche o campo de novo valor
            self.new_value_var.set(str(current_value))
    
    def write_selected_value(self):
        """Escreve novo valor no endereço selecionado"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showerror("Erro", "Selecione um resultado primeiro")
            return
        
        new_value = self.new_value_var.get()
        if not new_value:
            messagebox.showerror("Erro", "Digite um novo valor")
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
                    chain = PointerChain.from_dict(chain_data)
                    self.pointer_resolver.pointer_chains.append(chain)
                
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
