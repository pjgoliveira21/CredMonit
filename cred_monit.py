import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from typing import List, Tuple

import customtkinter as ctk


class DatabaseManager:
    def __init__(self, db_name: str = "cred_monit.db"):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
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
                """
            )
            conn.commit()

    def add_transaction(self, description: str, amount: float, purchase_date: str) -> bool:
        try:
            due_date = calculate_due_date(purchase_date)
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO transactions
                    (description, amount, remaining_amount, purchase_date, due_date, status)
                    VALUES (?, ?, ?, ?, ?, 'pending')
                    """,
                    (description, amount, amount, purchase_date, due_date),
                )
                conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao adicionar transacao: {e}")
            return False

    def get_all_transactions(self) -> List[Tuple]:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, description, amount, remaining_amount, purchase_date, due_date, status
                FROM transactions
                ORDER BY purchase_date ASC
                """
            )
            return cursor.fetchall()

    def get_pending_transactions(self) -> List[Tuple]:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, description, amount, remaining_amount, purchase_date, due_date, status
                FROM transactions
                WHERE status = 'pending'
                ORDER BY purchase_date ASC
                """
            )
            return cursor.fetchall()

    def update_transaction_amount(self, transaction_id: int, remaining_amount: float, status: str = "pending"):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE transactions
                SET remaining_amount = ?, status = ?
                WHERE id = ?
                """,
                (remaining_amount, status, transaction_id),
            )
            conn.commit()

    def get_total_remaining(self) -> float:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT SUM(remaining_amount)
                FROM transactions
                WHERE status = 'pending'
                """
            )
            result = cursor.fetchone()
            return result[0] if result[0] is not None else 0.0

    def get_next_due_total(self) -> float:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            next_due_date = get_next_due_date()
            cursor.execute(
                """
                SELECT SUM(remaining_amount)
                FROM transactions
                WHERE status = 'pending' AND due_date = ?
                """,
                (next_due_date,),
            )
            result = cursor.fetchone()
            return result[0] if result[0] is not None else 0.0

    def delete_transaction(self, transaction_id: int) -> bool:
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
                conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao eliminar transacao: {e}")
            return False


def calculate_due_date(purchase_date_str: str) -> str:
    try:
        purchase_date = datetime.strptime(purchase_date_str, "%Y-%m-%d")
        if purchase_date.day <= 6:
            due_date = purchase_date.replace(day=26)
        elif purchase_date.month == 12:
            due_date = purchase_date.replace(year=purchase_date.year + 1, month=1, day=26)
        else:
            due_date = purchase_date.replace(month=purchase_date.month + 1, day=26)
        return due_date.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"Erro ao calcular data de vencimento: {e}")
        return ""


def get_next_due_date() -> str:
    today = datetime.now()
    if today.day <= 26:
        next_due = today.replace(day=26)
    elif today.month == 12:
        next_due = today.replace(year=today.year + 1, month=1, day=26)
    else:
        next_due = today.replace(month=today.month + 1, day=26)
    return next_due.strftime("%Y-%m-%d")


def get_current_cycle_due_date() -> str:
    today = datetime.now()
    if today.day <= 26:
        return today.replace(day=26).strftime("%Y-%m-%d")
    if today.month == 12:
        return datetime(today.year + 1, 1, 26).strftime("%Y-%m-%d")
    return datetime(today.year, today.month + 1, 26).strftime("%Y-%m-%d")


class CredCardApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CredMonit - Gestao de Cartao de Credito")
        self.geometry("1040x760")
        self.resizable(False, False)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.db = DatabaseManager()
        self.credit_limit = 150.0

        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        self.configure(fg_color="#0f141c")

        self.main_container = ctk.CTkFrame(self, fg_color="#111a25", corner_radius=10)
        self.main_container.pack(fill="both", expand=True, padx=8, pady=8)

        self.form_frame = ctk.CTkFrame(self.main_container, width=300, fg_color="#2d3037")
        self.form_frame.pack(side="left", fill="y", padx=(0, 8))
        self.form_frame.pack_propagate(False)

        self.right_frame = ctk.CTkFrame(self.main_container, fg_color="#1a1f2b")
        self.right_frame.pack(side="right", fill="both", expand=True)

        self.setup_form()
        self.setup_overview_panel()
        self.setup_movements()
        self.setup_payment_section()

    def setup_form(self):
        ctk.CTkLabel(self.form_frame, text="Adicionar Compra", font=("Segoe UI", 26, "bold")).pack(pady=(18, 12))

        ctk.CTkLabel(self.form_frame, text="Descricao:", font=("Segoe UI", 16)).pack(
            pady=(6, 0), padx=14, anchor="w"
        )
        self.description_entry = ctk.CTkEntry(self.form_frame, width=268, font=("Segoe UI", 16), height=36)
        self.description_entry.pack(pady=4, padx=14)

        ctk.CTkLabel(self.form_frame, text="Valor (EUR):", font=("Segoe UI", 16)).pack(
            pady=(6, 0), padx=14, anchor="w"
        )
        self.amount_entry = ctk.CTkEntry(self.form_frame, width=268, font=("Segoe UI", 16), height=36)
        self.amount_entry.pack(pady=4, padx=14)

        ctk.CTkLabel(self.form_frame, text="Data (AAAA-MM-DD):", font=("Segoe UI", 16)).pack(
            pady=(6, 0), padx=14, anchor="w"
        )
        self.date_entry = ctk.CTkEntry(self.form_frame, width=268, font=("Segoe UI", 16), height=36)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.pack(pady=4, padx=14)

        ctk.CTkButton(
            self.form_frame,
            text="Adicionar Compra",
            command=self.add_purchase,
            font=("Segoe UI", 16, "bold"),
            height=40,
            fg_color="#2f95f2",
            hover_color="#1f7ed5",
        ).pack(pady=14, padx=14)

        ctk.CTkFrame(self.form_frame, height=2, fg_color="#424756").pack(fill="x", pady=10, padx=14)

        ctk.CTkLabel(self.form_frame, text="Regra de Faturacao", font=("Segoe UI", 18, "bold")).pack(
            pady=(8, 4), padx=14, anchor="w"
        )
        ctk.CTkLabel(
            self.form_frame,
            text="Compra ate dia 6: vencimento dia 26 (mes atual)\n\nCompra apos dia 6: vencimento dia 26 (mes seguinte)",
            justify="left",
            font=("Segoe UI", 15),
            text_color="#e9edf7",
            wraplength=264,
        ).pack(pady=(0, 8), padx=14, anchor="w")

    def setup_overview_panel(self):
        self.overview_frame = ctk.CTkFrame(self.right_frame, fg_color="#111722", corner_radius=10)
        self.overview_frame.pack(fill="x", padx=8, pady=(8, 6))

        top_line = ctk.CTkFrame(self.overview_frame, fg_color="transparent")
        top_line.pack(fill="x", padx=10, pady=(8, 4))

        ctk.CTkLabel(top_line, text="Caixa Isic", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(top_line, text="4124 **** **** 3338", font=("Segoe UI", 14)).pack(anchor="w")
        ctk.CTkLabel(top_line, text="Paulo Oliveira", font=("Segoe UI", 14, "bold")).pack(anchor="w")

        content_line = ctk.CTkFrame(self.overview_frame, fg_color="transparent")
        content_line.pack(fill="x", padx=8, pady=(2, 10))

        self.stats_frame = ctk.CTkFrame(content_line, fg_color="transparent")
        self.stats_frame.pack(side="left", fill="both", expand=True, padx=(4, 10))

        self.available_value_label = ctk.CTkLabel(
            self.stats_frame, text="0,00 EUR", font=("Segoe UI", 22, "bold"), text_color="#7fd9ff"
        )
        self.used_value_label = ctk.CTkLabel(
            self.stats_frame, text="0,00 EUR", font=("Segoe UI", 22, "bold"), text_color="#f0f3ff"
        )
        self.next_due_value_label = ctk.CTkLabel(
            self.stats_frame, text="0,00 EUR", font=("Segoe UI", 20, "bold"), text_color="#4ca3ff"
        )

        ctk.CTkLabel(self.stats_frame, text="Disponivel", font=("Segoe UI", 15)).pack(anchor="w", pady=(4, 0))
        self.available_value_label.pack(anchor="w", pady=(0, 6))
        ctk.CTkLabel(self.stats_frame, text="Utilizado", font=("Segoe UI", 15)).pack(anchor="w")
        self.used_value_label.pack(anchor="w", pady=(0, 6))
        ctk.CTkLabel(self.stats_frame, text="A pagar no dia 26", font=("Segoe UI", 15)).pack(anchor="w")
        self.next_due_value_label.pack(anchor="w")

        ring_holder = ctk.CTkFrame(content_line, fg_color="transparent")
        ring_holder.pack(side="right", padx=(0, 8), pady=2)

        self.ring_canvas = tk.Canvas(
            ring_holder,
            width=210,
            height=210,
            bg="#111722",
            highlightthickness=0,
            bd=0,
        )
        self.ring_canvas.pack()

    def setup_movements(self):
        movements_frame = ctk.CTkFrame(self.right_frame, fg_color="#111722", corner_radius=10)
        movements_frame.pack(fill="both", expand=True, padx=8, pady=(0, 6))

        ctk.CTkLabel(movements_frame, text="Movimentos", font=("Segoe UI", 24, "bold")).pack(
            anchor="w", padx=12, pady=(8, 2)
        )
        ctk.CTkLabel(
            movements_frame,
            text="Conta cartao",
            font=("Segoe UI", 14),
            text_color="#aeb6c7",
        ).pack(anchor="w", padx=12, pady=(0, 6))

        self.table_body = ctk.CTkScrollableFrame(
            movements_frame,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color="#2e3a4f",
            scrollbar_button_hover_color="#405274",
        )
        self.table_body.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.transaction_rows = []

    def setup_payment_section(self):
        payment_frame = ctk.CTkFrame(self.right_frame, fg_color="#111722", corner_radius=10)
        payment_frame.pack(fill="x", padx=8, pady=(0, 8))

        ctk.CTkLabel(payment_frame, text="Pagamento Manual", font=("Segoe UI", 18, "bold")).pack(pady=(8, 6))

        input_frame = ctk.CTkFrame(payment_frame, fg_color="transparent")
        input_frame.pack(pady=(0, 10))

        ctk.CTkLabel(input_frame, text="Montante (EUR):", font=("Segoe UI", 14)).pack(side="left", padx=(5, 8))
        self.payment_amount_entry = ctk.CTkEntry(input_frame, width=150, font=("Segoe UI", 14), height=32)
        self.payment_amount_entry.pack(side="left", padx=6)

        ctk.CTkButton(
            input_frame,
            text="Registar (FIFO)",
            command=self.process_payment,
            fg_color="#2E7D32",
            hover_color="#1f6125",
            font=("Segoe UI", 14, "bold"),
            width=150,
            height=32,
        ).pack(side="left", padx=6)

    def format_currency(self, amount: float) -> str:
        return f"{amount:.2f}".replace(".", ",") + " EUR"

    def draw_credit_ring(self, used_amount: float):
        used_ratio = 0 if self.credit_limit <= 0 else min(max(used_amount / self.credit_limit, 0), 1)
        available_amount = max(self.credit_limit - used_amount, 0)

        self.ring_canvas.delete("all")

        x1, y1, x2, y2 = 20, 20, 190, 190
        ring_width = 18

        self.ring_canvas.create_oval(x1, y1, x2, y2, outline="#f1f0e6", width=ring_width)
        self.ring_canvas.create_arc(
            x1,
            y1,
            x2,
            y2,
            start=90,
            extent=-360 * used_ratio,
            style="arc",
            outline="#5ab9ff",
            width=ring_width,
        )
        self.ring_canvas.create_text(105, 88, text="Disponivel", fill="#f1f4fb", font=("Segoe UI", 14, "bold"))
        self.ring_canvas.create_text(
            105,
            112,
            text=self.format_currency(available_amount),
            fill="#f1f4fb",
            font=("Segoe UI", 18, "bold"),
        )

    def add_purchase(self):
        description = self.description_entry.get().strip()
        amount_str = self.amount_entry.get().strip()
        purchase_date = self.date_entry.get().strip()

        if not description or not amount_str or not purchase_date:
            messagebox.showerror("Erro", "Todos os campos sao obrigatorios.")
            return

        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError("O valor deve ser positivo.")

            datetime.strptime(purchase_date, "%Y-%m-%d")

            if self.db.add_transaction(description, amount, purchase_date):
                messagebox.showinfo("Sucesso", "Compra adicionada com sucesso.")
                self.description_entry.delete(0, tk.END)
                self.amount_entry.delete(0, tk.END)
                self.date_entry.delete(0, tk.END)
                self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
                self.refresh_data()
            else:
                messagebox.showerror("Erro", "Falha ao adicionar compra.")
        except ValueError as e:
            messagebox.showerror("Erro", f"Dados invalidos: {e}")

    def process_payment(self):
        payment_str = self.payment_amount_entry.get().strip()
        if not payment_str:
            messagebox.showerror("Erro", "Insira um montante.")
            return

        try:
            payment_amount = float(payment_str)
            if payment_amount <= 0:
                raise ValueError("O montante deve ser positivo.")

            pending_transactions = self.db.get_pending_transactions()
            if not pending_transactions:
                messagebox.showinfo("Aviso", "Nao ha compras pendentes para pagar.")
                return

            remaining_payment = payment_amount
            for trans_id, _desc, _amount, remaining_amount, _purchase_date, _due_date, _status in pending_transactions:
                if remaining_payment <= 0:
                    break

                if remaining_payment >= remaining_amount:
                    remaining_payment -= remaining_amount
                    self.db.update_transaction_amount(trans_id, 0, "paid")
                else:
                    self.db.update_transaction_amount(trans_id, remaining_amount - remaining_payment, "pending")
                    remaining_payment = 0

            messagebox.showinfo(
                "Sucesso",
                f"Pagamento de {payment_amount:.2f} EUR registado.\nSaldo remanescente: {remaining_payment:.2f} EUR",
            )
            self.payment_amount_entry.delete(0, tk.END)
            self.refresh_data()
        except ValueError as e:
            messagebox.showerror("Erro", f"Dados invalidos: {e}")

    def delete_transaction(self, transaction_id: int):
        if messagebox.askyesno("Confirmar", "Tem a certeza que deseja eliminar esta compra?"):
            if self.db.delete_transaction(transaction_id):
                messagebox.showinfo("Sucesso", "Compra eliminada.")
                self.refresh_data()
            else:
                messagebox.showerror("Erro", "Falha ao eliminar compra.")

    def refresh_data(self):
        for row in self.transaction_rows:
            row.destroy()
        self.transaction_rows.clear()

        total_remaining = self.db.get_total_remaining()
        next_due_total = self.db.get_next_due_total()

        self.available_value_label.configure(text=self.format_currency(max(self.credit_limit - total_remaining, 0)))
        self.used_value_label.configure(text=self.format_currency(total_remaining))
        self.next_due_value_label.configure(text=self.format_currency(next_due_total))
        self.draw_credit_ring(total_remaining)

        transactions = self.db.get_all_transactions()
        current_cycle_due = get_current_cycle_due_date()

        if not transactions:
            empty_state = ctk.CTkLabel(self.table_body, text="Sem movimentos", font=("Segoe UI", 15), text_color="#b9c0cf")
            empty_state.pack(anchor="w", padx=8, pady=8)
            self.transaction_rows.append(empty_state)
            return

        for trans_id, description, amount, remaining_amount, purchase_date, due_date, status in reversed(transactions):
            if status == "paid":
                fg_color = "#173326"
            elif due_date == current_cycle_due:
                fg_color = "#3a2a1a"
            else:
                fg_color = "#1b2431"

            row_frame = ctk.CTkFrame(self.table_body, fg_color=fg_color, corner_radius=6)
            row_frame.pack(fill="x", padx=4, pady=3)

            content_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            content_frame.pack(side="left", fill="x", expand=True, padx=(10, 0), pady=8)

            description_text = description.upper() if len(description) <= 30 else description[:30].upper() + "..."
            ctk.CTkLabel(content_frame, text=description_text, font=("Segoe UI", 15, "bold"), anchor="w").pack(anchor="w")

            status_label = "PAGO" if status == "paid" else "PENDENTE"
            details_text = f"{purchase_date}  |  Venc.: {due_date}  |  {status_label}"
            ctk.CTkLabel(
                content_frame,
                text=details_text,
                font=("Segoe UI", 12),
                text_color="#a9b2c4",
                anchor="w",
            ).pack(anchor="w", pady=(2, 0))

            amount_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            amount_frame.pack(side="right", padx=(0, 8), pady=8)

            ctk.CTkLabel(
                amount_frame,
                text=f"Inicial: {amount:.2f} EUR",
                font=("Segoe UI", 12),
                text_color="#a9b2c4",
                width=150,
                anchor="e",
            ).pack(anchor="e")

            remaining_color = "#7ce6a7" if status == "paid" else "#f4f7ff"
            ctk.CTkLabel(
                amount_frame,
                text=f"Divida: {remaining_amount:.2f} EUR",
                font=("Segoe UI", 14, "bold"),
                text_color=remaining_color,
                width=150,
                anchor="e",
            ).pack(anchor="e", pady=(1, 0))

            ctk.CTkButton(
                row_frame,
                text="X",
                width=34,
                height=30,
                font=("Segoe UI", 13, "bold"),
                fg_color="#8B0000",
                command=lambda tid=trans_id: self.delete_transaction(tid),
            ).pack(side="right", padx=8, pady=8)

            self.transaction_rows.append(row_frame)


def main():
    app = CredCardApp()
    app.mainloop()


if __name__ == "__main__":
    main()
