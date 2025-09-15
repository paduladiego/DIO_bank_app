# Sistema Bancário em Python Desafio DIO
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
