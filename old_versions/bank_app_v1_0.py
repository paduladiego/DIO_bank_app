# variáveis Sacar, depositar, saldo, extrato, limite, numero_saques, LIMITE_SAQUES
# funções sacar, depositar, exibir_extrato, menu, validar_numero, validar_valor
# **Operação de depósito**
#   Deve ser possível depositar valores positivos para a minha conta bancária.
#   A v1 do projeto trabalha apenas com 1 usuário, dessa forma nao precisamos nos preocupar em identificar
#       qual é o número da agência e conta bancária. Todos os depósitos devem ser armazenados em uma variável e
#       exibidos na operação de extrato.
# ** Operação de saque **
#   O sistema deve permitir realizar 3 saques diários com limite máximo de R$ 500,00 por saque. Caso o usuário
#       não tenha saldo em conta, o sistema deve exibir uma mensagem informando que não será possível sacar o
#       dinheiro por falta de saldo. Todos os saques devem ser armazenados em uma variável e exibidos na operação
#       de extrato.
# **Operação de extrato**
#   Essa operação deve listar todos os depósitos e saques realizados na conta. No fim da listagem deve ser exibido
#       o saldo atual da conta. Se o extrato estiver em branco, exibir a mensagem: Não foram realizadas movimentações.
#   Os valores devem ser exibidos utilizando o formato R$ xxx.xx, exemplo: 1500.45 = R$ 1500.45
from decimal import Decimal, getcontext, InvalidOperation
import os

saldo = Decimal("0.00")
limite_saque = Decimal("500.00")
saques_diarios = 3
numero_saques = 0
extrato = []


def limpar_tela():
    """Limpa a tela do terminal."""
    os.system("cls" if os.name == "nt" else "clear")


def formatar_brl(valor):
    """Formata o valor Decimal para o formato brasileiro R$ xxx,xx"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def tem_duas_casas(valor: Decimal) -> bool:
    """Verifica se o Decimal tem até duas casas decimais."""
    return -valor.as_tuple().exponent <= 2


def checar_valor(mensagem: str) -> Decimal:
    while True:
        valor_digitado = input(mensagem).replace(",", ".")
        try:
            valor = Decimal(valor_digitado)
            return valor
        except InvalidOperation:
            limpar_tela()
            print(
                "Entrada inválida! Digite apenas números positivos, com até duas casas decimais."
            )


def depositar(valor):
    """Realiza um depósito na conta bancária."""
    global saldo, extrato
    if isinstance(valor, Decimal) and valor > 0 and tem_duas_casas(valor):
        saldo += valor
        extrato.append(("Depósito", valor))
        return f"Depósito de {formatar_brl(valor)} realizado com sucesso."
    else:
        return "Operação cancelada! Informar valor positivo com duas casas decimais."


def sacar_alem_limite_diario(valor):
    """Verifica se o valor do saque excede o limite por saque."""
    global saques_diarios, numero_saques
    while True:
        print("\n=== Saque Plus ===")
        print("Deseja sacar além do limite diário com apenas adicional R$ 0,50?")
        print("[s] Sim")
        print("[n] Não")
        opcao = input("Escolha uma opção: ").lower()
        match opcao:
            case "s":
                return Decimal(valor) + Decimal("0.50")
            case "n":
                return "Operação cancelada! Número máximo de saques diários atingido."
            case _:
                print("Opção inválida, tente novamente.")


def sacar(valor):
    """Realiza um saque na conta bancária."""
    global saldo, numero_saques, saques_diarios, limite_saque, extrato

    if valor > limite_saque:
        return f"Operação cancelada! O valor do saque excede o limite de R$ {limite_saque:.2f} por saque."

    if numero_saques >= saques_diarios:
        sacar_plus = sacar_alem_limite_diario(valor)
        if isinstance(sacar_plus, Decimal):
            valor = sacar_plus
        else:
            return sacar_plus

    if valor > saldo:
        return "Operação cancelada! Saldo insuficiente."

    if valor <= 0 or not tem_duas_casas(valor):
        return (
            "Operação cancelada! Informar valor positivo com até duas casas decimais."
        )

    saldo -= valor
    numero_saques += 1
    extrato.append(("Saque", valor))
    return f"Saque de {formatar_brl(valor)} realizado com sucesso."
    # implementar limite diario acumulado pois posso fazer muito saques pequenos e passar do limite diario


def exibir_extrato():
    global extrato, saldo
    if not extrato:
        print("Não foram realizadas movimentações.")
    else:
        print("\n=== EXTRATO ===")
        for tipo, valor in extrato:
            print(f"{tipo}: {formatar_brl(valor)}")
        print(f"\nSaldo atual: {formatar_brl(saldo)}")


if __name__ == "__main__":
    while True:
        print("\n=== MENU ===")
        print("[d] Depositar")
        print("[s] Sacar")
        print("[e] Extrato")
        print("[q] Sair")

        opcao = input("Escolha uma opção: ").lower()
        limpar_tela()
        match opcao:
            case "d":
                valor = checar_valor("Informe o valor do depósito: ")
                print(depositar(valor))

            case "s":
                valor = checar_valor("Informe o valor do saque: ")
                print(sacar(valor))

            case "e":
                exibir_extrato()

            case "q":
                print("Obrigado por utilizar nosso sistema bancário!")
                break

            case _:
                print("Opção inválida, tente novamente.")
