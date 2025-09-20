from decimal import Decimal, getcontext, InvalidOperation
from datetime import datetime, timezone, date
import os
import json

# BKP
arquivo_dados_saida = "state.json"

# variáveis fixas
limite_saque = Decimal("500.00")
valor_sacar_plus = Decimal("0.50")
valor_transacao_plus = Decimal("0.50")
operacoes_diarias = 10
saques_diarios = 3

# Variáveis dinâmicas
ultimo_dia = date.today()
saldo = Decimal("0.00")
transacao_plus = 0
numero_operacoes = 0
numero_saques = 0
extrato = []


def carregar_dados_de_entrada():
    try:
        with open(arquivo_dados_saida, "r") as arquivo:
            dados = json.load(arquivo)
            ultimo_dia = date.fromisoformat(dados["ultimo_dia"])
            saldo = Decimal(dados["saldo"])
            transacao_plus = dados["transacao_plus"]
            numero_operacoes = dados["numero_operacoes"]
            numero_saques = dados["numero_saques"]
            extrato = [
                (tipo, Decimal(valor), datetime.fromisoformat(data))
                for tipo, valor, data in dados["extrato"]
            ]
    except FileNotFoundError:
        ultimo_dia = date.today()
        saldo = Decimal("0.00")
        transacao_plus = 0
        numero_operacoes = 0
        numero_saques = 0
        extrato = []

    return ultimo_dia, saldo, transacao_plus, numero_operacoes, numero_saques, extrato


def armazenar_dados_de_saida(
    ultimo_dia, saldo, transacao_plus, numero_operacoes, numero_saques, extrato
):
    dados = {
        "ultimo_dia": ultimo_dia.isoformat(),
        "saldo": str(saldo),
        "transacao_plus": transacao_plus,
        "numero_operacoes": numero_operacoes,
        "numero_saques": numero_saques,
        "extrato": [
            (tipo, str(valor), data.isoformat()) for tipo, valor, data in extrato
        ],
    }
    with open(arquivo_dados_saida, "w") as arquivo:
        json.dump(dados, arquivo, indent=2)


def resetar_contadores_diarios(
    ultimo_dia,
    transacao_plus,
    numero_operacoes,
    numero_saques,
    operacoes_diarias,
    saques_diarios,
):
    hoje = date.today()
    if hoje != ultimo_dia:
        transacao_plus = 0
        numero_operacoes = 0
        numero_saques = 0
        ultimo_dia = hoje
        print(
            f"""Contadores diários foram resetados. Você possuí: \n
               - {operacoes_diarias} operações hoje.
               - {saques_diarios} saques hoje."""
        )
    return ultimo_dia, transacao_plus, numero_operacoes, numero_saques


def operacoes_diarias_totais(operacoes_diarias, transacao_plus):
    operacoes_totais = operacoes_diarias + transacao_plus
    return operacoes_totais


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
        if any(c.isalpha() for c in valor_digitado):
            limpar_tela()
            print("Entrada inválida! O valor não pode conter letras.")
            continue
        try:
            valor = Decimal(valor_digitado)
            return valor
        except InvalidOperation:
            limpar_tela()
            print(
                "Entrada inválida! Digite apenas números positivos, com até duas casas decimais."
            )


def checar_saldo(saldo, valor):
    if saldo <= 0:
        return False, "Operação cancelada! Saldo insuficiente."
    if saldo < valor:
        falta = valor - saldo
        return (
            False,
            f"Operação cancelada! Saldo insuficiente, faltam {formatar_brl(falta)}",
        )
    return True, ""


def sacar_alem_limite_diario(saldo, valor, extrato, valor_sacar_plus):
    """Verifica se o valor do saque excede o limite por saque."""
    while True:
        print("\n=== Saque Plus ===")
        print("Deseja sacar além do limite diário com apenas adicional R$ 0,50?")
        print("[s] Sim")
        print("[n] Não")
        opcao = input("Escolha uma opção: ").lower()
        match opcao:
            case "s":
                ok, msg = checar_saldo(saldo, valor_sacar_plus)
                if not ok:
                    limpar_tela()
                    print(msg)
                    return None

                limpar_tela()
                saldo -= valor_sacar_plus
                extrato.append(
                    ("Sacar Plus", valor_sacar_plus, datetime.now(timezone.utc))
                )
                return saldo, valor
            case "n":
                limpar_tela()
                return "Operação cancelada! Número máximo de saques diários atingido."
            case _:
                print("Opção inválida, tente novamente.")


def transacao_alem_limite_diario(transacao_plus, saldo, extrato, valor_transacao_plus):
    """Verifica se o valor do saque excede o limite por saque."""
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
                ok, msg = checar_saldo(saldo, valor_transacao_plus)
                if not ok:
                    limpar_tela()
                    # print(msg)
                    return (
                        transacao_plus,
                        saldo,
                        extrato,
                        msg,
                    )

                limpar_tela()
                transacao_plus += 1
                saldo -= valor_transacao_plus
                extrato.append(
                    (
                        "Transação Plus",
                        valor_transacao_plus,
                        datetime.now(timezone.utc),
                    )
                )
                return (
                    transacao_plus,
                    saldo,
                    extrato,
                    "Transação Plus ativada com sucesso.\n Você pode continuar suas operações.",
                )
            case "n":
                limpar_tela()
                return (
                    transacao_plus,
                    saldo,
                    extrato,
                    (
                        "Operação cancelada! Número máximo de operações diárias atingida."
                    ),
                )
            case _:
                print("Opção inválida, tente novamente.")


def registrar_operacoes(
    opcao: str,
    numero_operacoes: int,
    transacao_plus: int,
    operacoes_diarias: int,
) -> bool:
    """
    Apenas valida se ainda é possível realizar a operação.
    Não chama transação plus nem altera estado.
    """
    limite_total = operacoes_diarias_totais(operacoes_diarias, transacao_plus)
    if opcao in ("d", "s", "i") and numero_operacoes >= limite_total:
        return False
    return True


def depositar(valor, saldo, extrato, numero_operacoes, /):
    """Realiza um depósito na conta bancária."""
    if isinstance(valor, Decimal) and valor > 0 and tem_duas_casas(valor):
        saldo += valor
        numero_operacoes += 1
        extrato.append(("Depósito", valor, datetime.now(timezone.utc)))
        return (
            saldo,
            extrato,
            numero_operacoes,
            f"Depósito de {formatar_brl(valor)} realizado com sucesso.",
        )
    else:
        return (
            saldo,
            extrato,
            numero_operacoes,
            """=== Operação cancelada! ===
            Informar valor positivo com duas casas decimais.""",
        )


def sacar(
    *,
    valor,
    saldo,
    limite_saque,
    numero_saques,
    extrato,
    numero_operacoes,
    saques_diarios,
    valor_sacar_plus,
):
    """Realiza um saque na conta bancária."""
    if valor > limite_saque:
        return (
            saldo,
            extrato,
            numero_saques,
            numero_operacoes,
            f"Operação cancelada! O valor do saque excede o limite de R$ {limite_saque:.2f} por saque.",
        )

    if numero_saques >= saques_diarios:
        resultado = sacar_alem_limite_diario(saldo, valor, extrato, valor_sacar_plus)
        if resultado is None:
            return (
                saldo,
                extrato,
                numero_saques,
                numero_operacoes,
                "Operação cancelada! Saldo insuficiente.",
            )
        else:
            saldo, valor = resultado

    if valor > saldo:
        return (
            saldo,
            extrato,
            numero_saques,
            numero_operacoes,
            "Operação cancelada! Saldo insuficiente.",
        )

    if valor <= 0 or not tem_duas_casas(valor):
        return (
            saldo,
            extrato,
            numero_saques,
            numero_operacoes,
            """=== Operação cancelada! === 
            Informar valor positivo com até duas casas decimais.""",
        )

    saldo -= valor
    numero_saques += 1
    numero_operacoes += 1
    extrato.append(("Saque", valor, datetime.now(timezone.utc)))
    return (
        saldo,
        extrato,
        numero_saques,
        numero_operacoes,
        f"Saque de {formatar_brl(valor)} realizado com sucesso.",
    )
    # implementar limite diario acumulado pois posso fazer muito saques pequenos e passar do limite diario


def imprimir_extrato(
    extrato, saldo, numero_operacoes, operacoes_diarias, numero_saques, saques_diarios
):
    """imprime o extrato, registra no histórico e incrementa número de operações."""
    if not extrato:
        print("Não foram realizadas movimentações.")
    else:
        numero_operacoes += 1
        extrato.append(
            ("Imprimir Extrato", Decimal("0.00"), datetime.now(timezone.utc))
        )
        print("\n=== EXTRATO ===")
        for tipo, valor, data in extrato:
            data_local = data.astimezone()
            data_formatada = data_local.strftime("%d/%m/%Y %H:%M:%S")
            print(f"{tipo}: {formatar_brl(valor)} - {data_formatada}")
        print(f"\nSaldo atual: {formatar_brl(saldo)}")
        print(f"\nNúmero de operações hoje: {numero_operacoes}/{operacoes_diarias}")
        print(f"Número de saques hoje: {numero_saques}/{saques_diarios}")
        print("=== FIM DO EXTRATO ===")
    return extrato, numero_operacoes


def exibir_extrato(
    extrato, saldo, numero_operacoes, operacoes_diarias, numero_saques, saques_diarios
):
    """Exibe o extrato apenas na tela, não registra histórico e não incrementa operações."""
    if not extrato:
        print("Não foram realizadas movimentações.")
    else:
        print("\n=== EXIBIR EXTRATO ===")
        for tipo, valor, data in extrato:
            data_local = data.astimezone()
            data_formatada = data_local.strftime("%d/%m/%Y %H:%M:%S")
            print(f"{tipo}: {formatar_brl(valor)} - {data_formatada}")
        print(f"\nSaldo atual: {formatar_brl(saldo)}")
        print(f"\nNúmero de operações hoje: {numero_operacoes}/{operacoes_diarias}")
        print(f"Número de saques hoje: {numero_saques}/{saques_diarios}")
        print("=== FIM DO EXIBIR EXTRATO ===")
        return None


if __name__ == "__main__":
    (ultimo_dia, saldo, transacao_plus, numero_operacoes, numero_saques, extrato) = (
        carregar_dados_de_entrada()
    )

    while True:
        ultimo_dia, transacao_plus, numero_operacoes, numero_saques = (
            resetar_contadores_diarios(
                ultimo_dia,
                transacao_plus,
                numero_operacoes,
                numero_saques,
                operacoes_diarias,
                saques_diarios,
            )
        )

        print("\n=== MENU ===")
        print("[d] Depositar")
        print("[s] Sacar")
        print("[e] Exibir extrato (somente tela)")
        print("[i] Imprimir extrato (consome operação)")
        print("[q] Sair")

        opcao = input("Escolha uma opção: ").lower()
        limpar_tela()

        # Valida limite. Se atingiu, oferece Transação Plus uma única vez.
        if not registrar_operacoes(
            opcao, numero_operacoes, transacao_plus, operacoes_diarias
        ):
            transacao_plus, saldo, extrato, msg = transacao_alem_limite_diario(
                transacao_plus, saldo, extrato, valor_transacao_plus
            )
            print(msg)
            if "cancelada" in msg:
                continue

        match opcao:
            case "d":
                valor = checar_valor("Informe o valor do depósito: ")
                saldo, extrato, numero_operacoes, msg = depositar(
                    valor, saldo, extrato, numero_operacoes
                )
                print(msg)

            case "s":
                valor = checar_valor("Informe o valor do saque: ")
                saldo, extrato, numero_saques, numero_operacoes, msg = sacar(
                    saldo=saldo,
                    valor=valor,
                    extrato=extrato,
                    limite_saque=limite_saque,
                    numero_saques=numero_saques,
                    saques_diarios=saques_diarios,
                    numero_operacoes=numero_operacoes,
                    valor_sacar_plus=valor_sacar_plus,
                )
                print(msg)

            case "e":
                exibir_extrato(
                    extrato,
                    saldo,
                    numero_operacoes,
                    operacoes_diarias,
                    numero_saques,
                    saques_diarios,
                )

            case "i":
                extrato, numero_operacoes = imprimir_extrato(
                    extrato,
                    saldo,
                    numero_operacoes,
                    operacoes_diarias,
                    numero_saques,
                    saques_diarios,
                )

            case "q":
                armazenar_dados_de_saida(
                    ultimo_dia,
                    saldo,
                    transacao_plus,
                    numero_operacoes,
                    numero_saques,
                    extrato,
                )
                print("Obrigado por utilizar nosso sistema bancário!")
                break

            case _:
                print("Opção inválida, tente novamente.")
