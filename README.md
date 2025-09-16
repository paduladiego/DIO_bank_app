# Sistema Bancário em Python Desafio DIO

<details>
  <summary><b>Bank Application v1</b></summary>

# Bank Application v1

Este projeto é uma aplicação bancária simples desenvolvida em **Python**, com foco em operações básicas para um único usuário.  
A versão 1 implementa as seguintes funcionalidades:

---

## Funcionalidades

### Depósito
- Permite ao usuário realizar depósitos de valores positivos, que são registrados no extrato.

### Saque
- O usuário pode realizar até **3 saques diários**, com limite máximo de **R$ 500,00** por saque.  
- Caso o limite diário seja excedido, é oferecida a opção de saque adicional com uma taxa extra de **R$ 0,50**.  
- Saques só são permitidos se houver saldo suficiente e o valor for positivo.

### Extrato
- Exibe todas as movimentações (depósitos e saques) realizadas, mostrando o saldo atual.  
- Se não houver movimentações, informa ao usuário.

---

## Regras de Negócio
- Apenas valores **positivos** e com até **duas casas decimais** são aceitos para depósito e saque.  
- O sistema trabalha com apenas **um usuário**, sem necessidade de agência ou número de conta.  
- Todas as operações são registradas em **memória** (não há persistência em banco de dados).

---

## Estrutura do Código
- Utiliza o módulo **decimal** para garantir precisão nos valores monetários.  
- Funções separadas para cada operação: **depósito, saque, extrato e validação de valores**.  
- Interface simples via terminal, com **menu interativo**.

---

## Testes
- Testes automatizados com **pytest** garantem o funcionamento correto das operações de depósito e saque, incluindo casos de erro e validação de regras.  

---

**Bank Application v1** é uma base sólida para evoluir o sistema, permitindo futuras melhorias como múltiplos usuários, persistência de dados e interface gráfica.

</details>

<details>
  <summary><b>Bank Application v2</b></summary>

# Bank Application v2

Esta versão aprimora a aplicação bancária simples desenvolvida em **Python**, trazendo novas regras, persistência de dados e correções importantes em relação à **v1**.  
Agora o sistema mantém o histórico mesmo após reiniciar, calcula dinamicamente os limites de operações e garante estabilidade em todas as funções.

---

## Novidades da v2

- Implementado cálculo dinâmico de operações diárias com `operacoes_diarias_totais()` que considera `transacao_plus`.
- Persistência em **JSON** (`state.json`) para salvar e carregar saldo, extrato e contadores de forma confiável.
- Correção crítica no carregamento do `extrato`: sempre inicializado como **lista mutável**, evitando erros em `.append()`.
- Função `carregar_dados_de_entrada()` agora atualiza diretamente as variáveis globais (`saldo`, `extrato`, `numero_operacoes`, etc.).
- Incremento de `numero_operacoes` revisado em `depositar`, `sacar` e `exibir_extrato`.
- Registro adicional no extrato para operações especiais:
  - `Transação Plus` (expansão do limite de operações por R$ 0,50).
  - `Saque Plus` (saque além do limite diário de 3 operações, também com taxa de R$ 0,50).
  - `Exibir Extrato` (consulta registrada no histórico).
- Padronização de funções (`limpar_tela`, `formatar_brl`, `checar_valor`) e nomes de variáveis (`valor_sacar_plus`, `valor_transacao_plus`).

---

## Funcionalidades

### Depósito
- Permite ao usuário realizar depósitos de valores positivos, registrados no extrato e salvos em JSON.
- Valida entradas com até duas casas decimais.

### Saque
- O usuário pode realizar até **3 saques diários**, com limite máximo de **R$ 500,00** por saque.
- Se o limite de saques for atingido, é oferecido o `Saque Plus` com taxa de **R$ 0,50**.
- Caso o valor seja maior que o saldo, o saque é recusado.

### Transações diárias
- O sistema limita a **10 operações diárias**, mas o usuário pode comprar uma `Transação Plus` por **R$ 0,50**, aumentando esse limite.
- As operações válidas que contam para o limite incluem depósito, saque e consulta ao extrato.

### Extrato
- Exibe todas as movimentações registradas (`Depósito`, `Saque`, `Saque Plus`, `Transação Plus`, `Exibir Extrato`).
- Informa o saldo atual, número de operações realizadas e número de saques feitos.
- Se não houver movimentações, informa ao usuário.

---

## Regras de Negócio
- Apenas valores **positivos** e com até duas casas decimais são aceitos para depósito e saque.
- O sistema funciona para **um único usuário** (não há múltiplas contas).
- Todas as operações são registradas em **JSON** para garantir histórico após reinício.
- Consultar o extrato também conta como uma operação diária.

---

## Estrutura do Código
- Uso de `Decimal` para precisão monetária.
- Funções principais:
  - `depositar(valor)`
  - `sacar(valor)`
  - `exibir_extrato()`
  - `registrar_operações(opcao)`
  - `transacao_alem_limite_diario()`
  - `sacar_alem_limite_diario(valor)`
- Funções auxiliares:
  - `carregar_dados_de_entrada()` (atualiza globais)
  - `armazenar_dados_de_saida()`
  - `limpar_tela()`
  - `formatar_brl(valor)`
  - `tem_duas_casas(valor)`
  - `checar_valor(mensagem)`
- Menu interativo via terminal.

---

**Bank Application v2** traz robustez, persistência e flexibilidade ao sistema, preparando o terreno para futuras melhorias como suporte a múltiplos usuários e banco de dados.

</details>


<details>
  <summary><b>Bank Application v3</b></summary>

em breve

</details>
