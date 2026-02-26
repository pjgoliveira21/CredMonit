import customtkinter as ctk
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, scrolledtext
from typing import List, Tuple, Optional
import locale

# Configurar locale para português
locale.setlocale(locale.LC_TIME, 'pt_PT.UTF-8')


class DatabaseManager:
    """Gerir a base de dados SQLite para as transações."""
    
    def __init__(self, db_name: str = "cred_monit.db"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Inicializar a base de dados com a tabela de transações."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    amount REAL NOT NULL,
                    remaining_amount REAL NOT NULL,
                    purchase_date TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def add_transaction(self, description: str, amount: float, purchase_date: str) -> bool:
        """Adicionar uma nova transação."""
        try:
            due_date = calculate_due_date(purchase_date)
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO transactions 
                    (description, amount, remaining_amount, purchase_date, due_date, status)
                    VALUES (?, ?, ?, ?, ?, 'pending')
                """, (description, amount, amount, purchase_date, due_date))
                conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao adicionar transação: {e}")
            return False
    
    def get_all_transactions(self) -> List[Tuple]:
        """Obter todas as transações."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, description, amount, remaining_amount, purchase_date, due_date, status
                FROM transactions
                ORDER BY purchase_date ASC
            """)
            return cursor.fetchall()
    
    def get_pending_transactions(self) -> List[Tuple]:
        """Obter apenas as transações pendentes."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, description, amount, remaining_amount, purchase_date, due_date, status
                FROM transactions
                WHERE status = 'pending'
                ORDER BY purchase_date ASC
            """)
            return cursor.fetchall()
    
    def update_transaction_amount(self, transaction_id: int, remaining_amount: float, status: str = 'pending'):
        """Atualizar o valor em dívida de una transação."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE transactions
                SET remaining_amount = ?, status = ?
                WHERE id = ?
            """, (remaining_amount, status, transaction_id))
            conn.commit()
    
    def get_total_remaining(self) -> float:
        """Obter o total de dívida pendente."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(remaining_amount)
                FROM transactions
                WHERE status = 'pending'
            """)
            result = cursor.fetchone()
            return result[0] if result[0] is not None else 0.0
    
    def get_next_due_total(self) -> float:
        """Obter o total a pagar no próximo dia 26."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            next_due_date = get_next_due_date()
            cursor.execute("""
                SELECT SUM(remaining_amount)
                FROM transactions
                WHERE status = 'pending' AND due_date = ?
            """, (next_due_date,))
            result = cursor.fetchone()
            return result[0] if result[0] is not None else 0.0
    
    def delete_transaction(self, transaction_id: int) -> bool:
        """Eliminar uma transação."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
                conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao eliminar transação: {e}")
            return False


def calculate_due_date(purchase_date_str: str) -> str:
    """
    Calcular a data de vencimento com base na regra do dia 6 e dia 26.
    
    Regra:
    - Compra até dia 6 (inclusive) → vencimento dia 26 do mês atual
    - Compra após dia 6 → vencimento dia 26 do mês seguinte
    """
    try:
        purchase_date = datetime.strptime(purchase_date_str, "%Y-%m-%d")
        day = purchase_date.day
        
        if day <= 6:
            # Vencimento no dia 26 do mês atual
            due_date = purchase_date.replace(day=26)
        else:
            # Vencimento no dia 26 do mês seguinte
            if purchase_date.month == 12:
                due_date = purchase_date.replace(year=purchase_date.year + 1, month=1, day=26)
            else:
                due_date = purchase_date.replace(month=purchase_date.month + 1, day=26)
        
        return due_date.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"Erro ao calcular data de vencimento: {e}")
        return ""


def get_next_due_date() -> str:
    """Obter a próxima data de vencimento (dia 26)."""
    today = datetime.now()
    
    if today.day <= 26:
        # O próximo vencimento é no dia 26 do mês atual
        next_due = today.replace(day=26)
    else:
        # O próximo vencimento é no dia 26 do mês seguinte
        if today.month == 12:
            next_due = today.replace(year=today.year + 1, month=1, day=26)
        else:
            next_due = today.replace(month=today.month + 1, day=26)
    
    return next_due.strftime("%Y-%m-%d")


def get_current_cycle_due_date() -> str:
    """Obter a data de vencimento do ciclo atual (anterior ao próximo dia 26)."""
    today = datetime.now()
    
    if today.day <= 26:
        # O ciclo atual termina no dia 26 do mês atual
        return today.replace(day=26).strftime("%Y-%m-%d")
    else:
        # O ciclo atual já passou, o próximo é no mês que vem
        if today.month == 12:
            return datetime(today.year + 1, 1, 26).strftime("%Y-%m-%d")
        else:
            return datetime(today.year, today.month + 1, 26).strftime("%Y-%m-%d")


class CredCardApp(ctk.CTk):
    """Aplicação Desktop para gestão de cartão de crédito."""
    
    def __init__(self):
        super().__init__()
        
        self.title("CredMonit - Gestão de Cartão de Crédito")
        self.geometry("950x650")
        self.resizable(False, False)
        
        # Tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Base de dados
        self.db = DatabaseManager()
        
        # Setup UI
        self.setup_ui()
        self.refresh_data()
    
    def setup_ui(self):
        """Configurar a interface do utilizador."""
        
        # Frame superior - Dashboard
        self.dashboard_frame = ctk.CTkFrame(self)
        self.dashboard_frame.pack(fill="x", padx=8, pady=8)
        
        self.dashboard_label = ctk.CTkLabel(
            self.dashboard_frame,
            text="",
            font=("Arial", 13, "bold"),
            text_color="#FFD700"
        )
        self.dashboard_label.pack(fill="x", pady=4)
        
        # Frame com duas colunas - Formulário e Listagem
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        
        # Coluna esquerda - Formulário
        self.form_frame = ctk.CTkFrame(self.main_container, width=280)
        self.form_frame.pack(side="left", fill="y", padx=(0, 8))
        self.form_frame.pack_propagate(False)
        
        self.setup_form()
        
        # Coluna direita - Tabela e Pagamentos
        self.right_frame = ctk.CTkFrame(self.main_container)
        self.right_frame.pack(side="right", fill="both", expand=True)
        
        self.setup_table()
        self.setup_payment_section()
    
    def setup_form(self):
        """Configurar o formulário de adicionar compra."""
        
        form_title = ctk.CTkLabel(
            self.form_frame,
            text="Adicionar Compra",
            font=("Arial", 13, "bold")
        )
        form_title.pack(pady=8)
        
        # Descrição
        ctk.CTkLabel(self.form_frame, text="Descrição:", font=("Arial", 11)).pack(pady=(8, 0), padx=10, anchor="w")
        self.description_entry = ctk.CTkEntry(self.form_frame, width=260, font=("Arial", 11))
        self.description_entry.pack(pady=3, padx=10)
        
        # Valor
        ctk.CTkLabel(self.form_frame, text="Valor (€):", font=("Arial", 11)).pack(pady=(8, 0), padx=10, anchor="w")
        self.amount_entry = ctk.CTkEntry(self.form_frame, width=260, font=("Arial", 11))
        self.amount_entry.pack(pady=3, padx=10)
        
        # Data de Compra
        ctk.CTkLabel(self.form_frame, text="Data (AAAA-MM-DD):", font=("Arial", 11)).pack(pady=(8, 0), padx=10, anchor="w")
        self.date_entry = ctk.CTkEntry(self.form_frame, width=260, font=("Arial", 11))
        # Preenchimento automático com data de hoje
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.pack(pady=3, padx=10)
        
        # Botão Adicionar
        add_button = ctk.CTkButton(
            self.form_frame,
            text="Adicionar Compra",
            command=self.add_purchase,
            font=("Arial", 11, "bold"),
            height=32
        )
        add_button.pack(pady=12, padx=10)
        
        # Separador
        ctk.CTkFrame(self.form_frame, height=2).pack(fill="x", pady=8, padx=10)
        
        # Informações úteis
        info_title = ctk.CTkLabel(
            self.form_frame,
            text="Regra de Faturação",
            font=("Arial", 11, "bold")
        )
        info_title.pack(pady=(6, 2), padx=10, anchor="w")

        info_body = ctk.CTkLabel(
            self.form_frame,
            text="Compra até dia 6: vencimento dia 26 (mês atual)\n\nCompra após dia 6: vencimento dia 26 (mês seguinte)",
            justify="left",
            font=("Arial", 11),
            wraplength=250
        )
        info_body.pack(pady=(0, 8), padx=10, anchor="w")
    
    def setup_table(self):
        """Configurar a tabela de compras."""
        
        table_title = ctk.CTkLabel(
            self.right_frame,
            text="Compras Registadas",
            font=("Arial", 13, "bold")
        )
        table_title.pack(pady=6)
        
        # Frame para a tabela
        table_frame = ctk.CTkFrame(self.right_frame)
        table_frame.pack(fill="both", expand=True, pady=3)

        # Cabeçalho fixo
        header_frame = ctk.CTkFrame(table_frame, fg_color="#1f1f1f")
        header_frame.pack(fill="x", padx=3, pady=(3, 0))

        headers = ["Data", "Descrição", "Valor", "Dívida", "Vencimento", "Status", ""]
        header_widths = [85, 150, 80, 80, 90, 75, 50]

        for header, width in zip(headers, header_widths):
            h = ctk.CTkLabel(
                header_frame,
                text=header,
                font=("Arial", 12, "bold"),
                width=width,
                anchor="w"
            )
            h.pack(side="left", padx=4)

        # Corpo da tabela (sem scroll)
        self.table_body = ctk.CTkFrame(table_frame, fg_color="#2B2B2B")
        self.table_body.pack(fill="both", expand=True, padx=3, pady=(3, 0))
        
        # Armazenar referências para as transações
        self.transaction_rows = []
    
    def setup_payment_section(self):
        """Configurar a secção de pagamento."""
        
        payment_frame = ctk.CTkFrame(self.right_frame)
        payment_frame.pack(fill="x", pady=6)
        
        payment_title = ctk.CTkLabel(
            payment_frame,
            text="Registar Pagamento",
            font=("Arial", 12, "bold")
        )
        payment_title.pack(pady=4)
        
        # Valor de Pagamento
        input_frame = ctk.CTkFrame(payment_frame, fg_color="transparent")
        input_frame.pack(pady=3)
        
        ctk.CTkLabel(input_frame, text="Montante (€):", font=("Arial", 11)).pack(side="left", padx=(5, 5))
        self.payment_amount_entry = ctk.CTkEntry(input_frame, width=150, font=("Arial", 11))
        self.payment_amount_entry.pack(side="left", padx=5)
        
        # Botão Registar Pagamento
        payment_button = ctk.CTkButton(
            input_frame,
            text="Registar (FIFO)",
            command=self.process_payment,
            fg_color="#2E7D32",
            font=("Arial", 11, "bold"),
            width=130,
            height=28
        )
        payment_button.pack(side="left", padx=5)
    
    def add_purchase(self):
        """Adicionar uma nova compra."""
        description = self.description_entry.get().strip()
        amount_str = self.amount_entry.get().strip()
        purchase_date = self.date_entry.get().strip()
        
        if not description or not amount_str or not purchase_date:
            messagebox.showerror("Erro", "Todos os campos são obrigatórios!")
            return
        
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError("O valor deve ser positivo!")
            
            # Validar data
            datetime.strptime(purchase_date, "%Y-%m-%d")
            
            if self.db.add_transaction(description, amount, purchase_date):
                messagebox.showinfo("Sucesso", "Compra adicionada com sucesso!")
                self.description_entry.delete(0, tk.END)
                self.amount_entry.delete(0, tk.END)
                self.date_entry.delete(0, tk.END)
                self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
                self.refresh_data()
            else:
                messagebox.showerror("Erro", "Falha ao adicionar compra!")
        except ValueError as e:
            messagebox.showerror("Erro", f"Dados inválidos: {e}")
    
    def process_payment(self):
        """Processar um pagamento (FIFO)."""
        payment_str = self.payment_amount_entry.get().strip()
        
        if not payment_str:
            messagebox.showerror("Erro", "Insira um montante!")
            return
        
        try:
            payment_amount = float(payment_str)
            if payment_amount <= 0:
                raise ValueError("O montante deve ser positivo!")
            
            pending_transactions = self.db.get_pending_transactions()
            if not pending_transactions:
                messagebox.showinfo("Aviso", "Não há compras pendentes para pagar!")
                return
            
            remaining_payment = payment_amount
            
            # Aplicar pagamento nas compras mais antigas (FIFO)
            for transaction in pending_transactions:
                if remaining_payment <= 0:
                    break
                
                trans_id, description, amount, remaining_amount, purchase_date, due_date, status = transaction
                
                # Abater o pagamento
                if remaining_payment >= remaining_amount:
                    # Paga a compra completamente
                    remaining_payment -= remaining_amount
                    self.db.update_transaction_amount(trans_id, 0, 'paid')
                else:
                    # Paga parcialmente
                    new_remaining = remaining_amount - remaining_payment
                    self.db.update_transaction_amount(trans_id, new_remaining, 'pending')
                    remaining_payment = 0
            
            messagebox.showinfo(
                "Sucesso",
                f"Pagamento de €{payment_amount:.2f} registado!\nSaldo remanescente: €{remaining_payment:.2f}"
            )
            self.payment_amount_entry.delete(0, tk.END)
            self.refresh_data()
        
        except ValueError as e:
            messagebox.showerror("Erro", f"Dados inválidos: {e}")
    
    def delete_transaction(self, transaction_id: int):
        """Eliminar uma transação."""
        if messagebox.askyesno("Confirmar", "Tem a certeza que deseja eliminar esta compra?"):
            if self.db.delete_transaction(transaction_id):
                messagebox.showinfo("Sucesso", "Compra eliminada!")
                self.refresh_data()
            else:
                messagebox.showerror("Erro", "Falha ao eliminar compra!")
    
    def refresh_data(self):
        """Atualizar os dados exibidos."""
        # Limpar tabela
        for row in self.transaction_rows:
            row.destroy()
        self.transaction_rows.clear()
        
        # Atualizar dashboard
        total_remaining = self.db.get_total_remaining()
        next_due_total = self.db.get_next_due_total()
        next_due_date = get_next_due_date()
        
        dashboard_text = f"Total em Dívida: €{total_remaining:.2f}  |  Total a Pagar no Dia 26 ({next_due_date}): €{next_due_total:.2f}"
        self.dashboard_label.configure(text=dashboard_text)
        
        # Atualizar tabela
        transactions = self.db.get_all_transactions()
        current_cycle_due = get_current_cycle_due_date()
        
        for transaction in transactions:
            trans_id, description, amount, remaining_amount, purchase_date, due_date, status = transaction
            
            # Determinar cor de fundo baseado no status e data de vencimento
            is_current_cycle = due_date == current_cycle_due
            fg_color = "#2B2B2B"
            
            if status == "paid":
                fg_color = "#1a3a1a"
            elif is_current_cycle:
                fg_color = "#3a2a1a"  # Destaque para o ciclo atual
            
            row_frame = ctk.CTkFrame(self.table_body, fg_color=fg_color, corner_radius=4)
            row_frame.pack(fill="x", padx=3, pady=2)
            
            # Dados da linha
            row_data = [
                purchase_date,
                description[:23] + "..." if len(description) > 23 else description,
                f"€{amount:.2f}",
                f"€{remaining_amount:.2f}",
                due_date,
                status.upper(),
                ""
            ]
            
            column_widths = [85, 150, 80, 80, 90, 75, 50]
            
            for i, (data, width) in enumerate(zip(row_data, column_widths)):
                label = ctk.CTkLabel(
                    row_frame,
                    text=data,
                    font=("Arial", 11),
                    width=width,
                    anchor="w"
                )
                label.pack(side="left", padx=4, pady=4)
            
            # Botão Eliminar
            delete_btn = ctk.CTkButton(
                row_frame,
                text="X",
                width=42,
                height=26,
                font=("Arial", 11, "bold"),
                fg_color="#8B0000",
                command=lambda tid=trans_id: self.delete_transaction(tid)
            )
            delete_btn.pack(side="left", padx=4)
            
            self.transaction_rows.append(row_frame)


def main():
    """Função principal."""
    app = CredCardApp()
    app.mainloop()


if __name__ == "__main__":
    main()
