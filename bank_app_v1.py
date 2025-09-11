# variaveis Sacar, depositar, saldo, extrato, limite, numero_saques, LIMITE_SAQUES
# funcoes sacar, depositar, exibir_extrato, menu, validar_numero, validar_valor
# **Operação de depósito**
# Deve ser possível depositar valores positivos para a minha conta bancária.
# A v1 do projeto trabalha apenas com 1 usuário, dessa forma nao precisamos nos preocupar em identificar
# qual é o número da agência e conta bancária. Todos os depósitos devem ser armazenados em uma variável e
# exibidos na operação de extrato.
# ** Operação de saque **
# O sistema deve permitir realizar 3 saques diários com limite máximo de R$ 500,00 por saque. Caso o usuário não tenha saldo em conta, o sistema deve exibir uma mensagem informando que não será possível sacar o dinheiro por falta de saldo. Todos os saques devem ser armazenados em uma variável e exibidos na operação de extrato.
# **Operação de extrato**
# Essa operação deve listar todos os depósitos e saques realizados na conta. No fim da listagem deve ser exibido o saldo atual da conta. Se o extrato estiver em branco, exibir a mensagem: Não foram realizadas movimentações.
# Os valores devem ser exibidos utilizando o formato R$ xxx.xx, exemplo: 1500.45 = R$ 1500.45
from decimal import Decimal, getcontext
import os

saldo = Decimal("0.00")
limite_saque = Decimal("500.00")
saques_diários = 3
numero_saques = 0
extrato = []


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def tem_duas_casas(valor: Decimal) -> bool:
    """Verifica se o Decimal tem até duas casas decimais."""
    return -valor.as_tuple().exponent <= 2


def depositar(valor):
    global saldo
    global extrato
    if isinstance(valor, Decimal) and valor > 0 and tem_duas_casas(valor):
        saldo += valor
        extrato.append(("Depósito", valor))
        print(f"Depósito de R$ {valor:.2f} realizado com sucesso.")
        print(extrato)
    else:
        print("Operação cancelada! Informar valor positivo com duas casas decimal.")


def exibir_extrato():
    global extrato
    if not extrato:
        print("Não foram realizadas movimentações.")
    else:
        print("\n=== EXTRATO ===")
        for tipo, valor in extrato:
            print(f"{tipo}: R$ {valor:.2f}")
        print(f"\nSaldo atual: R$ {saldo:.2f}")


def sacar():
    pass


def extrato():
    pass


if __name__ == "__main__":
    while True:
        print("\n=== MENU ===")
        print("[d] Depositar")
        print("[s] Sacar")
        print("[e] Extrato")
        print("[q] Sair")

        opcao = input("Escolha uma opção: ").lower()
        clear_screen()
        match opcao:
            case "d":
                valor = Decimal(
                    input("Informe o valor do depósito: ").replace(",", ".")
                )

                depositar(valor)

            case "s":
                valor = Decimal(input("Informe o valor do saque: ").replace(",", "."))
                print(sacar(valor))

            case "e":
                exibir_extrato()

            case "q":
                print("Obrigado por utilizar nosso sistema bancário!")
                break

            case _:
                print("Opção inválida, tente novamente.")
