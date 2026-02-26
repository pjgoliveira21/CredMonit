# CredMonit - Gestor de Cartão de Crédito

Aplicação desktop para gestão de cartão de crédito com ciclos de faturação automáticos e pagamentos FIFO.

## 🚀 Como Usar

1. Execute o ficheiro `cred_monit.exe`
2. A aplicação abre automaticamente com interface gráfica

### Adicionar Compra
- Preencha a descrição, valor e data da compra
- Clique em "Adicionar Compra"

### Registar Pagamento
- Insira o montante a pagar
- Clique em "Registar Pagamento (FIFO)"
- O pagamento é aplicado automaticamente nas compras mais antigas primeiro

### Eliminar Compra
- Clique no botão de eliminar na linha da compra desejada

## 📋 Regras de Ciclo de Faturação

- **Compras até dia 6**: Vencem no dia 26 do mês atual
- **Compras após dia 6**: Vencem no dia 26 do mês seguinte

## ⚠️ Importante

**O ficheiro `cred_monit.db` deve estar sempre no mesmo diretório do executável.** Este ficheiro contém todos os dados das compras e pagamentos. Sem ele, a aplicação iniciará com uma base de dados vazia.
