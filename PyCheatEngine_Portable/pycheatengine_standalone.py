#!/usr/bin/env python3
"""
PyCheatEngine - Versão Standalone para Compilação
Versão otimizada e autocontida para gerar executável
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import random
import struct
import os
import sys

class GameMemorySimulator:
    """Simula memória de um jogo para demonstração"""
    
    def __init__(self):
        self.memory = {}
        self.base_addr = 0x400000
        
        # Valores simulados do jogo
        self.memory[0x400000] = 100     # HP
        self.memory[0x400004] = 50      # MP
        self.memory[0x400008] = 12345   # Score
        self.memory[0x40000C] = 5.5     # Speed
        self.memory[0x400010] = "Player" # Name
        
        # Thread para simular mudanças
        self.running = True
        self.update_thread = threading.Thread(target=self._simulate_changes, daemon=True)
        self.update_thread.start()
    
    def _simulate_changes(self):
        """Simula mudanças nos valores"""
        while self.running:
            try:
                # Score varia aleatoriamente
                self.memory[0x400008] += random.randint(-5, 10)
                # Speed varia ligeiramente
                self.memory[0x40000C] += random.uniform(-0.1, 0.1)
                self.memory[0x40000C] = max(1.0, min(10.0, self.memory[0x40000C]))
                time.sleep(2)
            except:
                break
    
    def read_value(self, address, data_type="int"):
        """Lê valor do endereço"""
        if address in self.memory:
            return self.memory[address]
        return None
    
    def write_value(self, address, value):
        """Escreve valor no endereço"""
        self.memory[address] = value
        return True
    
    def stop(self):
        self.running = False

class MemoryScanner:
    """Scanner de memória simplificado"""
    
    def __init__(self, memory_sim):
        self.memory_sim = memory_sim
        self.scan_results = []
    
    def first_scan(self, value, data_type="int"):
        """Primeiro scan por valor"""
        self.scan_results.clear()
        
        # Busca em endereços conhecidos
        test_addresses = [0x400000, 0x400004, 0x400008, 0x40000C]
        
        for addr in test_addresses:
            current_value = self.memory_sim.read_value(addr, data_type)
            if current_value is not None:
                if data_type == "int" and isinstance(current_value, int) and current_value == value:
                    self.scan_results.append({'address': addr, 'value': current_value, 'type': data_type})
                elif data_type == "float" and isinstance(current_value, float) and abs(current_value - value) < 0.01:
                    self.scan_results.append({'address': addr, 'value': current_value, 'type': data_type})
        
        return len(self.scan_results)
    
    def next_scan(self, scan_type):
        """Próximo scan com filtro"""
        if not self.scan_results:
            return 0
        
        filtered_results = []
        
        for result in self.scan_results:
            addr = result['address']
            old_value = result['value']
            current_value = self.memory_sim.read_value(addr, result['type'])
            
            if current_value is None:
                continue
            
            keep = False
            if scan_type == "increased" and current_value > old_value:
                keep = True
            elif scan_type == "decreased" and current_value < old_value:
                keep = True
            elif scan_type == "unchanged" and current_value == old_value:
                keep = True
            
            if keep:
                result['value'] = current_value
                filtered_results.append(result)
        
        self.scan_results = filtered_results
        return len(self.scan_results)

class PyCheatEngineGUI:
    """Interface gráfica principal"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PyCheatEngine - Memory Scanner")
        self.root.geometry("800x600")
        
        # Simulador de memória
        self.memory_sim = GameMemorySimulator()
        self.scanner = MemoryScanner(self.memory_sim)
        
        self.setup_ui()
        
        # Auto-update
        self.auto_update_enabled = True
        self.start_auto_update()
    
    def setup_ui(self):
        """Configura interface"""
        # Menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Sobre", command=self.show_about)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.root.quit)
        
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Painel de controles
        control_frame = ttk.LabelFrame(main_frame, text="Scanner de Memória")
        control_frame.pack(fill=tk.X, pady=5)
        
        # Tipo de dado
        ttk.Label(control_frame, text="Tipo:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.data_type_var = tk.StringVar(value="int")
        type_combo = ttk.Combobox(control_frame, textvariable=self.data_type_var, 
                                 values=["int", "float"], state="readonly", width=10)
        type_combo.grid(row=0, column=1, padx=5, pady=2)
        
        # Valor para buscar
        ttk.Label(control_frame, text="Valor:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.value_var = tk.StringVar()
        value_entry = ttk.Entry(control_frame, textvariable=self.value_var, width=15)
        value_entry.grid(row=0, column=3, padx=5, pady=2)
        
        # Botões de scan
        ttk.Button(control_frame, text="Primeiro Scan", 
                  command=self.first_scan).grid(row=0, column=4, padx=5, pady=2)
        ttk.Button(control_frame, text="Aumentou", 
                  command=lambda: self.next_scan("increased")).grid(row=1, column=0, padx=5, pady=2)
        ttk.Button(control_frame, text="Diminuiu", 
                  command=lambda: self.next_scan("decreased")).grid(row=1, column=1, padx=5, pady=2)
        ttk.Button(control_frame, text="Inalterado", 
                  command=lambda: self.next_scan("unchanged")).grid(row=1, column=2, padx=5, pady=2)
        
        # Lista de resultados
        results_frame = ttk.LabelFrame(main_frame, text="Resultados")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Treeview para resultados
        columns = ("address", "value", "type")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=15)
        self.results_tree.heading("address", text="Endereço")
        self.results_tree.heading("value", text="Valor")
        self.results_tree.heading("type", text="Tipo")
        
        self.results_tree.column("address", width=150)
        self.results_tree.column("value", width=100)
        self.results_tree.column("type", width=80)
        
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Controles de escrita
        write_frame = ttk.Frame(results_frame)
        write_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(write_frame, text="Novo Valor:").pack(side=tk.LEFT)
        self.new_value_var = tk.StringVar()
        ttk.Entry(write_frame, textvariable=self.new_value_var, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(write_frame, text="Escrever", command=self.write_value).pack(side=tk.LEFT)
        
        # Status
        self.status_var = tk.StringVar(value="Conectado ao processo de demonstração")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(side=tk.BOTTOM, pady=5)
        
        # Valores de exemplo
        example_frame = ttk.LabelFrame(main_frame, text="Valores de Exemplo")
        example_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(example_frame, text="HP: 100 (0x400000) | MP: 50 (0x400004) | Score: varia (0x400008) | Speed: ~5.5 (0x40000C)", 
                 foreground="blue").pack(pady=5)
    
    def first_scan(self):
        """Executa primeiro scan"""
        try:
            value_str = self.value_var.get().strip()
            if not value_str:
                messagebox.showerror("Erro", "Digite um valor para buscar")
                return
            
            data_type = self.data_type_var.get()
            
            if data_type == "int":
                value = int(value_str)
            elif data_type == "float":
                value = float(value_str)
            else:
                messagebox.showerror("Erro", "Tipo não suportado")
                return
            
            count = self.scanner.first_scan(value, data_type)
            self.update_results_display()
            self.status_var.set(f"Primeiro scan: {count} resultados encontrados")
            
        except ValueError:
            messagebox.showerror("Erro", "Valor inválido para o tipo selecionado")
    
    def next_scan(self, scan_type):
        """Executa próximo scan"""
        if not self.scanner.scan_results:
            messagebox.showerror("Erro", "Execute um primeiro scan antes")
            return
        
        count = self.scanner.next_scan(scan_type)
        self.update_results_display()
        self.status_var.set(f"Next scan ({scan_type}): {count} resultados restantes")
    
    def update_results_display(self):
        """Atualiza exibição dos resultados"""
        # Limpa lista
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Adiciona resultados
        for result in self.scanner.scan_results:
            self.results_tree.insert('', 'end', values=(
                f"0x{result['address']:08X}",
                str(result['value']),
                result['type']
            ))
    
    def write_value(self):
        """Escreve novo valor"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showerror("Erro", "Selecione um resultado")
            return
        
        try:
            new_value_str = self.new_value_var.get().strip()
            if not new_value_str:
                messagebox.showerror("Erro", "Digite um novo valor")
                return
            
            # Pega endereço selecionado
            item_values = self.results_tree.item(selection[0])['values']
            address_str = item_values[0]
            address = int(address_str, 16)
            
            # Encontra resultado correspondente
            result = None
            for r in self.scanner.scan_results:
                if r['address'] == address:
                    result = r
                    break
            
            if not result:
                messagebox.showerror("Erro", "Resultado não encontrado")
                return
            
            # Converte valor
            if result['type'] == "int":
                new_value = int(new_value_str)
            elif result['type'] == "float":
                new_value = float(new_value_str)
            else:
                messagebox.showerror("Erro", "Tipo não suportado")
                return
            
            # Escreve valor
            if self.memory_sim.write_value(address, new_value):
                result['value'] = new_value
                self.update_results_display()
                messagebox.showinfo("Sucesso", f"Valor escrito no endereço {address_str}")
            else:
                messagebox.showerror("Erro", "Falha ao escrever valor")
                
        except ValueError:
            messagebox.showerror("Erro", "Valor inválido")
    
    def start_auto_update(self):
        """Inicia atualização automática"""
        def update_loop():
            while self.auto_update_enabled:
                try:
                    if self.scanner.scan_results:
                        # Atualiza valores
                        for result in self.scanner.scan_results:
                            addr = result['address']
                            current_value = self.memory_sim.read_value(addr, result['type'])
                            if current_value is not None:
                                result['value'] = current_value
                        
                        # Atualiza display
                        self.root.after(0, self.update_results_display)
                    
                    time.sleep(3)
                except:
                    break
        
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()
    
    def show_about(self):
        """Mostra informações"""
        about_text = """PyCheatEngine v1.0.0

Sistema de Engenharia Reversa e Manipulação de Memória

Funcionalidades:
• Scanner de memória em tempo real
• Comparações avançadas (aumentou, diminuiu, inalterado)
• Escrita de valores na memória
• Interface gráfica intuitiva

Esta é uma versão de demonstração que simula um processo de jogo
com valores que mudam automaticamente para teste das funcionalidades.

Desenvolvido em Python com Tkinter
"""
        messagebox.showinfo("Sobre PyCheatEngine", about_text)
    
    def run(self):
        """Executa aplicação"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()
    
    def on_closing(self):
        """Cleanup ao fechar"""
        self.auto_update_enabled = False
        self.memory_sim.stop()
        self.root.quit()
        self.root.destroy()

def main():
    """Função principal"""
    print("PyCheatEngine - Memory Scanner")
    print("Iniciando interface gráfica...")
    
    app = PyCheatEngineGUI()
    app.run()

if __name__ == "__main__":
    main()