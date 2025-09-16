from decimal import Decimal, getcontext, InvalidOperation
from datetime import datetime, timezone
import os

saldo = Decimal("0.00")
limite_saque = Decimal("500.00")
valor_sacar_plus = Decimal("0.50")
valor_transacao_plus = Decimal("0.50")
transacao_plus = 0
operacoes_diarias = 10
numero_operacoes = 0
saques_diarios = 3
numero_saques = 0
extrato = []


def operacoes_diarias_totais():
    return operacoes_diarias + transacao_plus


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
                limpar_tela()
                extrato.append(
                    ("Sacar Plus", valor_sacar_plus, datetime.now(timezone.utc))
                )
                return Decimal(valor)
            case "n":
                limpar_tela()
                return "Operação cancelada! Número máximo de saques diários atingido."
            case _:
                print("Opção inválida, tente novamente.")


def transacao_alem_limite_diario():
    """Verifica se o valor do saque excede o limite por saque."""
    global transacao_plus
    while True:
        print("\n=== Transação Plus ===")
        print(
            "Você atingiu o limite diário de operações bancárias. \nGaranta sua transação além do limite por apenas R$ 0,50?"
        )
        print("[s] Sim")
        print("[n] Não")
        opcao = input("Escolha uma opção: ").lower()
        match opcao:
            case "s":
                limpar_tela()
                transacao_plus += 1
                extrato.append(
                    ("Transação Plus", valor_transacao_plus, datetime.now(timezone.utc))
                )
                return "Transação Plus ativada com sucesso."

            case "n":
                limpar_tela()
                return (
                    "Operação cancelada! Número máximo de operações diárias atingida."
                )
            case _:
                print("Opção inválida, tente novamente.")


def registrar_operações(opcao: str) -> bool:
    global transacao_plus, oeperacoes_diarias, numero_operacoes
    if opcao in ("d", "s", "e"):
        if numero_operacoes >= operacoes_diarias_totais():
            print("Limite diário de operações atingido.")
            print(f"Operação nº {numero_operacoes}/{operacoes_diarias}")
            resultado = transacao_alem_limite_diario()
            print(resultado)
            return False
    return True


def depositar(valor):
    """Realiza um depósito na conta bancária."""
    global saldo, extrato, numero_operacoes
    if isinstance(valor, Decimal) and valor > 0 and tem_duas_casas(valor):
        saldo += valor
        numero_operacoes += 1
        extrato.append(("Depósito", valor, datetime.now(timezone.utc)))
        return f"Depósito de {formatar_brl(valor)} realizado com sucesso."
    else:
        return "Operação cancelada! Informar valor positivo com duas casas decimais."


def sacar(valor):
    """Realiza um saque na conta bancária."""
    global saldo, numero_saques, saques_diarios, limite_saque, extrato, numero_operacoes

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
    numero_operacoes += 1
    extrato.append(("Saque", valor, datetime.now(timezone.utc)))
    return f"Saque de {formatar_brl(valor)} realizado com sucesso."
    # implementar limite diario acumulado pois posso fazer muito saques pequenos e passar do limite diario


def exibir_extrato():
    global extrato, saldo, numero_operacoes, operacoes_diarias, numero_saques, saques_diarios
    if not extrato:
        print("Não foram realizadas movimentações.")
    else:
        numero_operacoes += 1
        extrato.append(("Exibir Extrato", Decimal("0.00"), datetime.now(timezone.utc)))
        print("\n=== EXTRATO ===")
        for tipo, valor, data in extrato:
            data_local = data.astimezone()
            data_formatada = data_local.strftime("%d/%m/%Y %H:%M:%S")
            print(f"{tipo}: {formatar_brl(valor)} - {data_formatada}")
        print(f"\nSaldo atual: {formatar_brl(saldo)}")
        print(f"\nNúmero de operações hoje: {numero_operacoes}/{operacoes_diarias}")
        print(f"Número de saques hoje: {numero_saques}/{saques_diarios}")
        print("=== FIM DO EXTRATO ===")


if __name__ == "__main__":
    while True:
        print("\n=== MENU ===")
        print("[d] Depositar")
        print("[s] Sacar")
        print("[e] Extrato")
        print("[q] Sair")

        opcao = input("Escolha uma opção: ").lower()
        limpar_tela()

        if not registrar_operações(opcao):
            continue

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
