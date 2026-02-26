# CredMonit - Gestor de Cartão de Crédito

Aplicação desktop em Python para gestão inteligente de um cartão de crédito específico com ciclos de faturação automáticos e pagamentos FIFO.

## 🎯 Funcionalidades Principais

### Ciclo de Faturação Inteligente
- **Até dia 6**: Compras registadas até ao dia 6 (inclusive) vencem no dia 26 do mês atual
- **Após dia 6**: Compras após o dia 6 vencem no dia 26 do mês seguinte

### Sistema de Pagamentos FIFO
- Os pagamentos são aplicados nas compras mais antigas primeiro (First In, First Out)
- Rastreamento parcial de pagamentos - é possível pagar apenas parte de uma compra

### Dashboard Intuitivo
- Visualização do total em dívida
- Destaque do montante a pagar no próximo ciclo (dia 26)
- Tabela scrollable com todas as compras

## 🛠️ Requisitos

- Python 3.8+
- customtkinter
- sqlite3 (incluído no Python)

## 📦 Instalação

### 1. Clonar ou descarregar o repositório
```bash
cd CredMonit
```

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

## 🚀 Utilização

### Executar a aplicação
```bash
python cred_monit.py
```

### Interface da Aplicação

#### Painel Esquerdo - Adicionar Compra
1. Preencher a **Descrição** (ex: "Supermercado", "Restaurante")
2. Inserir o **Valor** em euros
3. Configurar a **Data de Compra** (por padrão, a data de hoje)
4. Clicar em "Adicionar Compra"

#### Painel Direito - Tabela de Compras
Exibe todas as compras com:
- Data da compra
- Descrição
- Valor original
- Valor em dívida (após pagamentos)
- Data de vencimento
- Status (pending/paid)
- Botão para eliminar

#### Registar Pagamento
1. Inserir o montante a pagar
2. Clicar em "Registar Pagamento (FIFO)"
3. O sistema autoabate nas compras mais antigas

## 💾 Base de Dados

A aplicação utiliza SQLite com a tabela `transactions`:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER | ID único |
| description | TEXT | Descrição da compra |
| amount | REAL | Valor original |
| remaining_amount | REAL | Valor ainda em dívida |
| purchase_date | TEXT | Data da compra |
| due_date | TEXT | Data de vencimento (calculada) |
| status | TEXT | 'pending' ou 'paid' |
| created_at | TIMESTAMP | Quando foi registada |

O ficheiro de base de dados (`cred_monit.db`) é criado automaticamente no primeiro arranque.

## 🎨 Interface

- **Tema escuro** para conforto visual
- **Tabela scrollable** para múltiplas compras
- **Cores destacadas** para compras do ciclo atual
- **Validação de dados** em tempo real

## 📝 Exemplos de Uso

### Exemplo 1: Compra no ciclo atual
1. Data de hoje: 15 de fevereiro
2. Compra registada no dia 10 (antes do dia 6)
3. **Vencimento**: 26 de fevereiro (mês atual)

### Exemplo 2: Compra no próximo ciclo
1. Data de hoje: 15 de fevereiro
2. Compra registada no dia 15 (após o dia 6)
3. **Vencimento**: 26 de março (mês seguinte)

### Exemplo 3: Pagamento FIFO
1. Compra A: €100 (dia 1) - Vencia 26/fev
2. Compra B: €50 (dia 10) - Vencia 26/fev
3. Pagamento de €120:
   - Compra A reduz para €0 (paga completamente)
   - Compra B reduz para €30 (paga €20 dos €50)

## 🔧 Estrutura do Código

```
cred_monit.py
├── DatabaseManager
│   ├── init_database()          # Inicializar SQLite
│   ├── add_transaction()        # Adicionar compra
│   ├── get_all_transactions()   # Listar tudo
│   ├── process_payment()        # Atualizar após pagamento
│   └── ...
├── Funções Utilitárias
│   ├── calculate_due_date()     # Calcular vencimento
│   ├── get_next_due_date()      # Próximo dia 26
│   └── get_current_cycle_due_date()
└── CredCardApp (customtkinter)
    ├── setup_ui()               # Construir interface
    ├── setup_form()             # Formulário de compra
    ├── setup_table()            # Tabela scrollable
    ├── add_purchase()           # Callback do formulário
    ├── process_payment()        # Callback de pagamento
    └── refresh_data()           # Atualizar dashboard
```

## 📋 Notas Importantes

- As datas devem ser inseridas no formato **YYYY-MM-DD** (ex: 2026-02-26)
- O sistema considera o **dia 26 como data de vencimento padrão** para cada ciclo
- Os pagamentos aplicam-se **automaticamente nas compras mais antigas** (FIFO)
- Compras **eliminadas não podem ser recuperadas** (sem lixeira de reciclagem)

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'customtkinter'"
```bash
pip install --upgrade customtkinter
```

### A base de dados está corrompida
Elimine o ficheiro `cred_monit.db` e o programa criará uma nova na próxima execução.

### Scroll do rato não funciona
Este é um comportamento padrão - use a scrollbar no lado direito ou as teclas de seta.

## 📄 Licença

Código de demonstração - livre para usar e modificar.

---

**Desenvolvido com ❤️ em Python**
