from decimal import Decimal, getcontext, InvalidOperation
from datetime import datetime, timezone, date
import os
import shutil
import json
import re

# BKP
arquivo_transacoes_bancarias = "transacoes_bancarias.json"
arquivo_contas_bancarias = "contas_bancarias.json"

# variáveis fixas
limite_saque = Decimal("500.00")
valor_sacar_plus = Decimal("0.50")
valor_transacao_plus = Decimal("0.50")
operacoes_diarias = 10
saques_diarios = 3
agencia = "0001"

# Variáveis dinâmicas
ultimo_dia = date.today()
saldo = Decimal("0.00")
transacao_plus = 0
numero_operacoes = 0
numero_saques = 0
extrato = []
agencia_logada = None
conta_logada = None
cpf_logado = None
usuarios = []
contas_bancarias = []


def limpar_cpf(cpf_raw):
    """
    Remove caracteres não numéricos do CPF.
    \\D corresponde a qualquer caractere que não seja um dígito, por vazio\nada
    """
    return re.sub(r"\D", "", cpf_raw)


def carregar_dados_transacoes(
    cpf_logado, agencia_logada, conta_logada, arquivo_transacoes_bancarias
):
    user_id = f"{cpf_logado}-{agencia_logada}-{conta_logada}"

    try:
        with open(arquivo_transacoes_bancarias, "r", encoding="utf-8") as arquivo:
            conteudo = json.load(arquivo)

            if user_id not in conteudo:
                raise FileNotFoundError("Conta não encontrada no arquivo")

            dados = conteudo[user_id]
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

    return (
        ultimo_dia,
        saldo,
        transacao_plus,
        numero_operacoes,
        numero_saques,
        extrato,
    )


def armazenar_dados_transacoes(
    cpf_logado,
    agencia_logada,
    conta_logada,
    ultimo_dia,
    saldo,
    transacao_plus,
    numero_operacoes,
    numero_saques,
    extrato,
    arquivo_transacoes_bancarias,
):
    # ID
    user_id = f"{cpf_logado}-{agencia_logada}-{conta_logada}"

    # registro
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
    backup_file: None
    try:
        # backup para Rollback
        if os.path.exists(arquivo_transacoes_bancarias):
            backup_file = arquivo_transacoes_bancarias + ".bkp"
            shutil.copy(arquivo_transacoes_bancarias, backup_file)

        # conteúdo atual
        try:
            with open(
                arquivo_transacoes_bancarias, "r", encoding="utf-8"
            ) as arquivo_json:
                conteudo = json.load(arquivo_json)
                if not isinstance(conteudo, dict):
                    conteudo = {}
        except (FileNotFoundError, json.JSONDecodeError):
            conteudo = {}

        # remover reistro
        conteudo.pop(user_id, None)
        # adiciona registro
        conteudo[user_id] = dados

        # registar
        with open(arquivo_transacoes_bancarias, "w", encoding="utf-8") as arquivo_json:
            json.dump(conteudo, arquivo_json, indent=2, ensure_ascii=False)

        # Se deu tudo certo, remove backup
        if backup_file:
            os.remove(backup_file)

    except Exception as e:
        print("❌ Erro ao salvar, recuperando dados...", e)
        # Restaurar backup
        if backup_file and os.path.exists(backup_file):
            shutil.move(backup_file, arquivo_transacoes_bancarias)
        raise


def armazenar_dados_contas(usuarios, contas_bancarias, arquivo_contas_bancarias):
    dados = {}

    # montar dict com cpf como chave
    for usuario in usuarios:
        cpf = usuario["cpf"]
        contas_no_cpf = [
            {"agencia": conta["agencia"], "numero_conta": conta["numero_conta"]}
            for conta in contas_bancarias
            if conta["cpf"] == cpf
        ]
        dados[cpf] = {
            "cpf": cpf,
            "nome": usuario["nome"],
            "data_nascimento": usuario["data_nascimento"],
            "endereco": usuario["endereco"],
            "contas": contas_no_cpf,
        }
    backup_file = None

    try:
        # bkp rollback
        if os.path.exists(arquivo_contas_bancarias):
            backup_file = arquivo_contas_bancarias + ".bkp"
            shutil.copy(arquivo_contas_bancarias, backup_file)

        # salvar json
        with open(arquivo_contas_bancarias, "w", encoding="utf-8") as arquivo_json:
            json.dump(dados, arquivo_json, indent=2, ensure_ascii=False)

        if backup_file:
            os.remove(backup_file)

    except Exception as e:
        print("❌ Erro ao salvar, recuperando dados...", e)


def carregar_dados_bancarios(arquivo_contas_bancarias):
    if not os.path.exists(arquivo_contas_bancarias):
        return [], []

    try:
        with open(arquivo_contas_bancarias, "r", encoding="utf-8") as arquivo:
            conteudo = json.load(arquivo)

        usuarios = []
        contas_bancarias = []

        for cpf, dados in conteudo.items():
            usuarios.append(
                {
                    "cpf": cpf,
                    "nome": dados["nome"],
                    "data_nascimento": dados["data_nascimento"],
                    "endereco": dados["endereco"],
                }
            )
            for conta in dados["contas"]:
                contas_bancarias.append(
                    {
                        "agencia": conta["agencia"],
                        "numero_conta": conta["numero_conta"],
                        "cpf": cpf,
                    }
                )

        return usuarios, contas_bancarias
    except (FileNotFoundError, json.JSONDecodeError):
        return [], []


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


def menu_conta(
    cpf_logado,
    agencia_logada,
    conta_logada,
    ultimo_dia,
    saldo,
    transacao_plus,
    numero_operacoes,
    numero_saques,
    extrato,
    operacoes_diarias,
    saques_diarios,
    valor_sacar_plus,
    valor_transacao_plus,
    limite_saque,
):
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
                valor_checado = checar_valor("Informe o valor do saque: ")
                saldo, extrato, numero_saques, numero_operacoes, msg = sacar(
                    saldo=saldo,
                    valor=valor_checado,
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
                armazenar_dados_transacoes(
                    cpf_logado,
                    agencia_logada,
                    conta_logada,
                    ultimo_dia,
                    saldo,
                    transacao_plus,
                    numero_operacoes,
                    numero_saques,
                    extrato,
                    arquivo_transacoes_bancarias,
                )
                print("Voltadno ao menu inicial!")
                return (
                    cpf_logado,
                    agencia_logada,
                    conta_logada,
                    ultimo_dia,
                    saldo,
                    transacao_plus,
                    numero_operacoes,
                    numero_saques,
                    extrato,
                )

            case _:
                print("Opção inválida, tente novamente.")


def checar_limpar_cpf(cpf_digitado):
    """
    Valida e limpa o CPF informado.
    - Remove caracteres não numéricos.
    - Garante que o CPF tenha 11 dígitos.
    - Se for inválido, pede novamente até o usuário digitar corretamente.
    - ainda não cehca o validador
    """
    while True:
        # se não recebeu nada (ou foi inválido antes), pede de novo
        if not cpf_digitado:
            cpf_digitado = input("Informe o CPF (somente números): ")

        cpf_raw = cpf_digitado.strip()
        cpf = limpar_cpf(cpf_raw)  # remove pontos e traços

        if cpf.isdigit() and len(cpf) == 11:
            return cpf  # ✅ válido → retorna já limpo

        print("❌ CPF inválido! Deve conter exatamente 11 dígitos numéricos.")
        # força pedir de novo no próximo loop
        cpf_digitado = None


def formatar_cpf(cpf):
    """Formata o CPF no padrão xxx.xxx.xxx-xx"""
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def checar_cpf_cadastrado(cpf, usuarios):
    for cpf_lista in usuarios:
        if cpf_lista["cpf"] == cpf:
            return True, "✔️ Já existe usuário com esse CPF!"
    return False, "❌ CPF não existe como usuário, Favor Cadastrar!."


def gerar_novo_numero_conta(contas_bancarias):
    return contas_bancarias[-1]["numero_conta"] + 1


def criar_usuario(usuarios):
    print("\n==== Cadastro de Usuário ====")
    # solicitar cpf
    cpf_digitado = input("Informe o CPF (somente números): ")
    cpf = checar_limpar_cpf(cpf_digitado)
    # validar se cpf já existe
    existe, msg = checar_cpf_cadastrado(cpf, usuarios)
    if existe:
        print(msg)
        return usuarios
    # solicitar nome, data nascimento, endereço
    nome = input("Informe o nome completo: ").strip()
    data_nascimento = input("Informe a data de nascimento (DD/MM/AAAA): ").strip()
    endereco = input(
        "Informe o endereço (logradouro, nº - bairro - cidade/UF): "
    ).strip()
    # adicionar em uma lista de usuários como dicionário {}
    usuario = {
        "cpf": cpf,
        "nome": nome,
        "data_nascimento": data_nascimento,
        "endereco": endereco,
    }
    usuarios.append(usuario)
    # print("Usuário criado com sucesso!")
    print("Usuário criado com sucesso!")


def listar_contas(cpf, contas_bancarias):
    cpf_busca = checar_limpar_cpf(cpf)
    print(f"\n==== Contas com CPF {formatar_cpf(cpf_busca)} ====")
    contas_encontradas = [
        conta for conta in contas_bancarias if conta["cpf"] == cpf_busca
    ]
    if not contas_encontradas:
        print("❌ Nenhuma conta encontrada para este CPF.")
        return
    for conta in contas_encontradas:
        print(f" --- Agência: {conta['agencia']} | Conta: {conta['numero_conta']}")


def criar_conta(agencia, usuarios, contas_bancarias, cpf_digitado):
    print("\n==== Cadastro de Conta ====")
    # valida CPF do usuário
    cpf = checar_limpar_cpf(cpf_digitado)
    print(f"✔️ CPF Válido {formatar_cpf(cpf)}")
    # veja se cadastro do cpf não existe
    nao_existe, msg = checar_cpf_cadastrado(cpf, usuarios)
    if not nao_existe:
        print(msg)
        return
    # confirma criação de nova conta
    while True:
        limpar_tela()
        print(f"Confirma a criação de uma nova conta para:")
        listar_contas(cpf, contas_bancarias)
        print("\n=== Confirmação ===")
        print("[s] Sim")
        print("[n] Não")
        opcao = input("Escolha uma opção: ").lower()
        match opcao:
            case "s":
                # cria conta com número sequencial
                novo_numero_conta = gerar_novo_numero_conta(contas_bancarias)
                print(f" --- Agência: {agencia} | Conta: {novo_numero_conta}")
                contas_bancarias.append(
                    {"agencia": agencia, "numero_conta": novo_numero_conta, "cpf": cpf}
                )
                print("✔️ Conta criada com sucesso!")
                # adiciona em uma lista de contas como dicionário {}

                return
            case "n":
                print("Operação cancelada pelo usuário.")
                return
            case _:
                print("Opção inválida, operação cancelada.")
                return


def acessar_conta(usuarios, contas_bancarias, cpf_digitado):
    cpf = checar_limpar_cpf(cpf_digitado)

    # chama listar_contas apenas para exibir na tela
    listar_contas(cpf, contas_bancarias)

    # também filtra as contas do CPF (para validação)
    contas_encontradas = [c for c in contas_bancarias if c["cpf"] == cpf]
    if not contas_encontradas:
        return None, None, None

    # escolher conta
    agencia_logada = input("Informe a agência: ").strip()
    try:
        conta_logada = int(input("Informe o número da conta: ").strip())
    except ValueError:
        print("❌ Número de conta inválido.")
        return None, None, None

    # validar se pertence ao CPF
    conta_valida = next(
        (
            c
            for c in contas_encontradas
            if c["agencia"] == agencia_logada and c["numero_conta"] == conta_logada
        ),
        None,
    )

    if not conta_valida:
        print("❌ Agência ou conta inválida para este CPF.")
        return None, None, None

    print("✔️ Acesso autorizado!")
    return cpf, agencia_logada, conta_logada


if __name__ == "__main__":
    usuarios, contas_bancarias = carregar_dados_bancarios(arquivo_contas_bancarias)
    while True:
        print("\n=== MENU INICIAL ===")
        print("[ac] Acessar conta")
        print("[lc] Listar contas")
        print("[nc] Nova conta")
        print("[nu] Novo usuário")
        print("[q] Sair")

        opcao = input("Escolha uma opção: ").lower().strip()
        limpar_tela()

        match opcao:
            case "nu":
                criar_usuario(usuarios)

            case "nc":
                cpf_digitado = input("Informe o CPF do usuário: ")
                criar_conta(agencia, usuarios, contas_bancarias, cpf_digitado)

            case "lc":
                cpf_digitado = input("Informe o CPF para listar as contas: ")
                cpf = checar_limpar_cpf(cpf_digitado)
                listar_contas(cpf, contas_bancarias)

            case "ac":
                cpf_digitado = input("Informe o CPF: ")
                cpf_logado, agencia_logada, conta_logada = acessar_conta(
                    usuarios, contas_bancarias, cpf_digitado
                )

                if not (cpf_logado and agencia_logada and conta_logada is not None):
                    # falhou login/acesso; volta ao menu
                    continue

                # carrega transações dessa conta
                (
                    ultimo_dia,
                    saldo,
                    transacao_plus,
                    numero_operacoes,
                    numero_saques,
                    extrato,
                ) = carregar_dados_transacoes(
                    cpf_logado,
                    agencia_logada,
                    conta_logada,
                    arquivo_transacoes_bancarias,
                )

                # chama menu de operações da conta
                menu_conta(
                    cpf_logado,
                    agencia_logada,
                    conta_logada,
                    ultimo_dia,
                    saldo,
                    transacao_plus,
                    numero_operacoes,
                    numero_saques,
                    extrato,
                    operacoes_diarias,
                    saques_diarios,
                    valor_sacar_plus,
                    valor_transacao_plus,
                    limite_saque,
                )

            case "q":
                armazenar_dados_contas(
                    usuarios, contas_bancarias, arquivo_contas_bancarias
                )
                print("Armazenando dados...")
                print("Obrigado por utilizar nosso sistema bancário!")
                break

            case _:
                print("Opção inválida, tente novamente.")
