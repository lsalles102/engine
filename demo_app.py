#!/usr/bin/env python3
"""
PyCheatEngine - Aplicação de Demonstração
Demonstra todas as funcionalidades do sistema em um ambiente controlado
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import random
import struct
from typing import Dict, List

class DemoProcess:
    """Simula um processo para demonstração"""
    
    def __init__(self):
        self.memory = bytearray(1024 * 1024)  # 1MB de memória simulada
        self.base_address = 0x400000
        
        # Inicializa com dados de exemplo
        self._initialize_demo_data()
        
        # Thread para simular mudanças de valores
        self.running = True
        self.update_thread = threading.Thread(target=self._update_values, daemon=True)
        self.update_thread.start()
    
    def _initialize_demo_data(self):
        """Inicializa dados de demonstração na memória"""
        # Player stats na posição 0x1000
        offset = 0x1000
        
        # HP (int32) = 100
        self.write_int32(offset, 100)
        
        # MP (int32) = 50  
        self.write_int32(offset + 4, 50)
        
        # Score (int64) = 12345
        self.write_int64(offset + 8, 12345)
        
        # Speed (float) = 5.5
        self.write_float(offset + 16, 5.5)
        
        # Name (string) = "Player"
        name_bytes = "Player\x00".encode('utf-8')
        self.memory[offset + 20:offset + 20 + len(name_bytes)] = name_bytes
        
        # Adiciona padrão AOB na posição 0x2000
        aob_pattern = bytes([0x48, 0x8B, 0x05, 0x12, 0x34, 0x56, 0x78, 0x48, 0x89])
        self.memory[0x2000:0x2000 + len(aob_pattern)] = aob_pattern
    
    def _update_values(self):
        """Simula mudanças automáticas de valores"""
        while self.running:
            try:
                # Muda score aleatoriamente
                current_score = self.read_int64(0x1008)
                if current_score is not None:
                    new_score = current_score + random.randint(-10, 10)
                    self.write_int64(0x1008, max(0, new_score))
                
                # Muda speed ligeiramente
                current_speed = self.read_float(0x1010)
                if current_speed is not None:
                    new_speed = current_speed + random.uniform(-0.1, 0.1)
                    self.write_float(0x1010, max(0.1, min(10.0, new_speed)))
                
                time.sleep(1)
            except:
                break
    
    def read_memory(self, address: int, size: int) -> bytes:
        """Lê dados da memória simulada"""
        offset = address - self.base_address
        if 0 <= offset < len(self.memory) and offset + size <= len(self.memory):
            return bytes(self.memory[offset:offset + size])
        return b''
    
    def write_memory(self, address: int, data: bytes) -> bool:
        """Escreve dados na memória simulada"""
        offset = address - self.base_address
        if 0 <= offset < len(self.memory) and offset + len(data) <= len(self.memory):
            self.memory[offset:offset + len(data)] = data
            return True
        return False
    
    def read_int32(self, address: int) -> int:
        data = self.read_memory(address, 4)
        return struct.unpack('<i', data)[0] if len(data) == 4 else None
    
    def write_int32(self, address: int, value: int) -> bool:
        data = struct.pack('<i', value)
        return self.write_memory(address, data)
    
    def read_int64(self, address: int) -> int:
        data = self.read_memory(address, 8)
        return struct.unpack('<q', data)[0] if len(data) == 8 else None
    
    def write_int64(self, address: int, value: int) -> bool:
        data = struct.pack('<q', value)
        return self.write_memory(address, data)
    
    def read_float(self, address: int) -> float:
        data = self.read_memory(address, 4)
        return struct.unpack('<f', data)[0] if len(data) == 4 else None
    
    def write_float(self, address: int, value: float) -> bool:
        data = struct.pack('<f', value)
        return self.write_memory(address, data)
    
    def stop(self):
        self.running = False

class PyCheatEngineDemo:
    """Interface de demonstração do PyCheatEngine"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PyCheatEngine - Demonstração Funcional")
        self.root.geometry("1000x700")
        
        # Processo de demonstração
        self.demo_process = DemoProcess()
        
        # Resultados de scan
        self.scan_results = []
        
        self.setup_ui()
        
        # Timer para atualização automática
        self.auto_update_enabled = tk.BooleanVar(value=True)
        self.start_auto_update()
    
    def setup_ui(self):
        """Configura a interface"""
        # Notebook principal
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Aba Scanner
        self.setup_scanner_tab(notebook)
        
        # Aba Ponteiros
        self.setup_pointer_tab(notebook)
        
        # Aba AOB
        self.setup_aob_tab(notebook)
        
        # Status bar
        self.status_label = ttk.Label(self.root, text="Conectado ao processo de demonstração")
        self.status_label.pack(side=tk.BOTTOM, pady=2)
    
    def setup_scanner_tab(self, parent):
        """Configura aba do scanner"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="Scanner de Memória")
        
        # Painel esquerdo
        left_panel = ttk.LabelFrame(frame, text="Configurações")
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        ttk.Label(left_panel, text="Tipo de Dado:").pack(anchor=tk.W)
        self.data_type_var = tk.StringVar(value="int32")
        ttk.Combobox(left_panel, textvariable=self.data_type_var,
                    values=["int32", "int64", "float", "string"],
                    state="readonly").pack(pady=2)
        
        ttk.Label(left_panel, text="Valor:").pack(anchor=tk.W)
        self.scan_value_var = tk.StringVar()
        ttk.Entry(left_panel, textvariable=self.scan_value_var).pack(pady=2)
        
        ttk.Button(left_panel, text="Primeiro Scan", 
                  command=self.first_scan).pack(pady=5)
        ttk.Button(left_panel, text="Scan: Aumentou", 
                  command=lambda: self.next_scan("increased")).pack(pady=2)
        ttk.Button(left_panel, text="Scan: Diminuiu", 
                  command=lambda: self.next_scan("decreased")).pack(pady=2)
        ttk.Button(left_panel, text="Scan: Inalterado", 
                  command=lambda: self.next_scan("unchanged")).pack(pady=2)
        
        # Valores de exemplo
        ttk.Separator(left_panel, orient='horizontal').pack(fill=tk.X, pady=10)
        ttk.Label(left_panel, text="Valores de Exemplo:", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        ttk.Label(left_panel, text="HP: 100 (endereço 0x401000)", foreground="blue").pack(anchor=tk.W)
        ttk.Label(left_panel, text="MP: 50 (endereço 0x401004)", foreground="blue").pack(anchor=tk.W)
        ttk.Label(left_panel, text="Score: varia (endereço 0x401008)", foreground="blue").pack(anchor=tk.W)
        ttk.Label(left_panel, text="Speed: ~5.5 (endereço 0x401010)", foreground="blue").pack(anchor=tk.W)
        
        # Painel direito - resultados
        right_panel = ttk.LabelFrame(frame, text="Resultados")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Lista de resultados
        columns = ("address", "value", "type")
        self.results_tree = ttk.Treeview(right_panel, columns=columns, show="headings")
        self.results_tree.heading("address", text="Endereço")
        self.results_tree.heading("value", text="Valor")
        self.results_tree.heading("type", text="Tipo")
        
        scrollbar = ttk.Scrollbar(right_panel, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Controles de escrita
        write_frame = ttk.Frame(right_panel)
        write_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(write_frame, text="Novo Valor:").pack(side=tk.LEFT)
        self.new_value_var = tk.StringVar()
        ttk.Entry(write_frame, textvariable=self.new_value_var).pack(side=tk.LEFT, padx=5)
        ttk.Button(write_frame, text="Escrever", command=self.write_value).pack(side=tk.LEFT)
        
        ttk.Checkbutton(write_frame, text="Auto-Update", 
                       variable=self.auto_update_enabled).pack(side=tk.RIGHT)
    
    def setup_pointer_tab(self, parent):
        """Configura aba de ponteiros"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="Ponteiros")
        
        config_frame = ttk.LabelFrame(frame, text="Criar Cadeia de Ponteiros")
        config_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(config_frame, text="Endereço Base:").pack(side=tk.LEFT)
        self.base_addr_var = tk.StringVar(value="0x401000")
        ttk.Entry(config_frame, textvariable=self.base_addr_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(config_frame, text="Offsets:").pack(side=tk.LEFT)
        self.offsets_var = tk.StringVar(value="0")
        ttk.Entry(config_frame, textvariable=self.offsets_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(config_frame, text="Testar Ponteiro", 
                  command=self.test_pointer).pack(side=tk.LEFT, padx=5)
        
        # Resultado do ponteiro
        self.pointer_result = ttk.Label(frame, text="", font=("Arial", 10))
        self.pointer_result.pack(pady=10)
        
        # Exemplo
        example_frame = ttk.LabelFrame(frame, text="Exemplo de Uso")
        example_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(example_frame, text="Para acessar HP diretamente:").pack(anchor=tk.W)
        ttk.Label(example_frame, text="Base: 0x401000, Offset: 0", foreground="blue").pack(anchor=tk.W)
        ttk.Label(example_frame, text="Resultado final: valor no endereço 0x401000", foreground="green").pack(anchor=tk.W)
    
    def setup_aob_tab(self, parent):
        """Configura aba AOB"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="Scanner AOB")
        
        config_frame = ttk.LabelFrame(frame, text="Busca de Padrão de Bytes")
        config_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(config_frame, text="Padrão (hex):").pack(anchor=tk.W)
        self.aob_pattern_var = tk.StringVar(value="48 8B 05 ?? ?? ?? ?? 48 89")
        ttk.Entry(config_frame, textvariable=self.aob_pattern_var, width=50).pack(pady=2)
        
        ttk.Button(config_frame, text="Buscar Padrão", 
                  command=self.search_aob).pack(pady=5)
        
        # Resultados AOB
        self.aob_results = tk.Text(frame, height=15, width=80)
        self.aob_results.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Exemplo
        example_text = """Exemplo de padrão encontrado:
Endereço: 0x402000
Padrão: 48 8B 05 ?? ?? ?? ?? 48 89
Bytes encontrados: 48 8B 05 12 34 56 78 48 89

Wildcards (??) permitem buscar padrões com bytes variáveis.
"""
        self.aob_results.insert(tk.END, example_text)
    
    def first_scan(self):
        """Realiza primeiro scan"""
        try:
            value_str = self.scan_value_var.get()
            data_type = self.data_type_var.get()
            
            if not value_str:
                messagebox.showerror("Erro", "Digite um valor para buscar")
                return
            
            # Converte valor
            if data_type == "int32":
                target_value = int(value_str)
            elif data_type == "int64":
                target_value = int(value_str)
            elif data_type == "float":
                target_value = float(value_str)
            else:
                target_value = value_str
            
            # Busca na memória simulada
            self.scan_results.clear()
            base = self.demo_process.base_address
            
            # Verifica endereços conhecidos
            addresses_to_check = []
            for addr in range(base + 0x1000, base + 0x2000, 4):
                addresses_to_check.append(addr)
            
            for address in addresses_to_check:
                try:
                    if data_type == "int32":
                        current_value = self.demo_process.read_int32(address)
                    elif data_type == "int64":
                        current_value = self.demo_process.read_int64(address)
                    elif data_type == "float":
                        current_value = self.demo_process.read_float(address)
                    else:
                        continue
                    
                    if current_value == target_value:
                        self.scan_results.append({
                            'address': address,
                            'value': current_value,
                            'previous_value': current_value,
                            'type': data_type
                        })
                except:
                    continue
            
            self.update_results_display()
            self.status_label.config(text=f"Primeiro scan: {len(self.scan_results)} resultados encontrados")
            
        except ValueError:
            messagebox.showerror("Erro", "Valor inválido para o tipo selecionado")
    
    def next_scan(self, scan_type):
        """Realiza próximo scan"""
        if not self.scan_results:
            messagebox.showerror("Erro", "Execute um primeiro scan antes")
            return
        
        filtered_results = []
        
        for result in self.scan_results:
            address = result['address']
            previous_value = result['value']
            data_type = result['type']
            
            # Lê valor atual
            try:
                if data_type == "int32":
                    current_value = self.demo_process.read_int32(address)
                elif data_type == "int64":
                    current_value = self.demo_process.read_int64(address)
                elif data_type == "float":
                    current_value = self.demo_process.read_float(address)
                else:
                    continue
                
                # Aplica filtro
                keep = False
                if scan_type == "increased" and current_value > previous_value:
                    keep = True
                elif scan_type == "decreased" and current_value < previous_value:
                    keep = True
                elif scan_type == "unchanged" and current_value == previous_value:
                    keep = True
                
                if keep:
                    result['previous_value'] = result['value']
                    result['value'] = current_value
                    filtered_results.append(result)
                    
            except:
                continue
        
        self.scan_results = filtered_results
        self.update_results_display()
        self.status_label.config(text=f"Next scan ({scan_type}): {len(self.scan_results)} resultados restantes")
    
    def update_results_display(self):
        """Atualiza exibição de resultados"""
        # Limpa árvore
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Adiciona resultados
        for result in self.scan_results:
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
            new_value_str = self.new_value_var.get()
            if not new_value_str:
                messagebox.showerror("Erro", "Digite um novo valor")
                return
            
            # Encontra resultado selecionado
            item_values = self.results_tree.item(selection[0])['values']
            address_str = item_values[0]
            address = int(address_str, 16)
            
            # Encontra resultado correspondente
            result = None
            for r in self.scan_results:
                if r['address'] == address:
                    result = r
                    break
            
            if not result:
                messagebox.showerror("Erro", "Resultado não encontrado")
                return
            
            # Converte e escreve valor
            data_type = result['type']
            if data_type == "int32":
                new_value = int(new_value_str)
                success = self.demo_process.write_int32(address, new_value)
            elif data_type == "int64":
                new_value = int(new_value_str)
                success = self.demo_process.write_int64(address, new_value)
            elif data_type == "float":
                new_value = float(new_value_str)
                success = self.demo_process.write_float(address, new_value)
            else:
                messagebox.showerror("Erro", "Tipo não suportado para escrita")
                return
            
            if success:
                result['value'] = new_value
                self.update_results_display()
                messagebox.showinfo("Sucesso", f"Valor escrito no endereço {address_str}")
            else:
                messagebox.showerror("Erro", "Falha ao escrever valor")
                
        except ValueError:
            messagebox.showerror("Erro", "Valor inválido")
    
    def test_pointer(self):
        """Testa cadeia de ponteiros"""
        try:
            base_str = self.base_addr_var.get()
            offsets_str = self.offsets_var.get()
            
            # Converte endereço base
            if base_str.startswith('0x'):
                base_addr = int(base_str, 16)
            else:
                base_addr = int(base_str)
            
            # Converte offsets
            offsets = []
            for offset_str in offsets_str.split(','):
                offset_str = offset_str.strip()
                if offset_str.startswith('0x'):
                    offsets.append(int(offset_str, 16))
                else:
                    offsets.append(int(offset_str))
            
            # Resolve ponteiro (simplificado para demonstração)
            final_address = base_addr + offsets[0] if offsets else base_addr
            
            # Lê valor no endereço final
            value = self.demo_process.read_int32(final_address)
            
            if value is not None:
                result_text = f"Ponteiro resolvido com sucesso!\n"
                result_text += f"Endereço base: {base_str}\n"
                result_text += f"Offsets: {offsets_str}\n"
                result_text += f"Endereço final: 0x{final_address:08X}\n"
                result_text += f"Valor encontrado: {value}"
                self.pointer_result.config(text=result_text, foreground="green")
            else:
                self.pointer_result.config(text="Falha ao resolver ponteiro", foreground="red")
                
        except ValueError:
            self.pointer_result.config(text="Erro: valores inválidos", foreground="red")
    
    def search_aob(self):
        """Busca padrão AOB"""
        pattern_str = self.aob_pattern_var.get()
        
        if not pattern_str:
            messagebox.showerror("Erro", "Digite um padrão")
            return
        
        try:
            # Converte padrão para bytes
            pattern_parts = pattern_str.split()
            pattern_bytes = []
            
            for part in pattern_parts:
                if part == "??":
                    pattern_bytes.append(None)  # Wildcard
                else:
                    pattern_bytes.append(int(part, 16))
            
            # Busca na memória
            found_addresses = []
            memory = self.demo_process.memory
            
            for i in range(len(memory) - len(pattern_bytes) + 1):
                match = True
                for j, pattern_byte in enumerate(pattern_bytes):
                    if pattern_byte is not None and memory[i + j] != pattern_byte:
                        match = False
                        break
                
                if match:
                    address = self.demo_process.base_address + i
                    found_addresses.append(address)
            
            # Exibe resultados
            self.aob_results.delete(1.0, tk.END)
            
            if found_addresses:
                self.aob_results.insert(tk.END, f"Padrão encontrado em {len(found_addresses)} endereço(s):\n\n")
                
                for addr in found_addresses:
                    self.aob_results.insert(tk.END, f"Endereço: 0x{addr:08X}\n")
                    
                    # Mostra bytes encontrados
                    offset = addr - self.demo_process.base_address
                    found_bytes = memory[offset:offset + len(pattern_bytes)]
                    hex_str = ' '.join(f'{b:02X}' for b in found_bytes)
                    self.aob_results.insert(tk.END, f"Bytes: {hex_str}\n\n")
            else:
                self.aob_results.insert(tk.END, "Padrão não encontrado na memória.")
                
        except ValueError:
            messagebox.showerror("Erro", "Padrão inválido")
    
    def start_auto_update(self):
        """Inicia atualização automática dos resultados"""
        def update_loop():
            while True:
                if self.auto_update_enabled.get() and self.scan_results:
                    try:
                        # Atualiza valores dos resultados
                        for result in self.scan_results:
                            address = result['address']
                            data_type = result['type']
                            
                            if data_type == "int32":
                                current_value = self.demo_process.read_int32(address)
                            elif data_type == "int64":
                                current_value = self.demo_process.read_int64(address)
                            elif data_type == "float":
                                current_value = self.demo_process.read_float(address)
                            else:
                                continue
                            
                            if current_value is not None:
                                result['value'] = current_value
                        
                        # Atualiza display na thread principal
                        self.root.after(0, self.update_results_display)
                        
                    except:
                        pass
                
                time.sleep(2)  # Atualiza a cada 2 segundos
        
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()
    
    def run(self):
        """Executa a aplicação"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()
    
    def on_closing(self):
        """Cleanup ao fechar"""
        self.demo_process.stop()
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    print("=== PyCheatEngine - Demonstração Funcional ===")
    print("Esta demonstração simula todas as funcionalidades principais:")
    print("• Scanner de memória com diferentes tipos de dados")
    print("• Comparações avançadas (aumentou, diminuiu, inalterado)")
    print("• Resolução de cadeias de ponteiros")
    print("• Scanner AOB com suporte a wildcards")
    print("• Interface gráfica completa")
    print("\nAbrindo interface gráfica...")
    
    app = PyCheatEngineDemo()
    app.run()