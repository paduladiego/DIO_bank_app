from abc import ABC, abstractmethod
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone, date
import os
import re
import json
import shutil


# ========= Reuso do v2_2 =========
def limpar_tela():
    os.system("cls" if os.name == "nt" else "clear")


def formatar_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def tem_duas_casas(valor):
    return -valor.as_tuple().exponent <= 2


def limpar_cpf(cpf_raw):
    """
    Remove caracteres não numéricos do CPF.
    \\D corresponde a qualquer caractere que não seja um dígito, por vazio\nada
    """
    return re.sub(r"\D", "", cpf_raw)


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


def formatar_cpf(cpf):
    """Formata o CPF no padrão xxx.xxx.xxx-xx"""
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def checar_limpar_cpf(cpf_digitado):
    """
    Valida e limpa o CPF informado.
    - Remove caracteres não numéricos.
    - Garante que o CPF tenha 11 dígitos.
    - Se for inválido, pede novamente até o usuário digitar corretamente.
    """
    while True:
        if not cpf_digitado:
            cpf_digitado = input("Informe o CPF (somente números): ")
        cpf_raw = cpf_digitado.strip()
        cpf = limpar_cpf(cpf_raw)

        if cpf.isdigit() and len(cpf) == 11:
            return cpf  # ✅ válido

        print("❌ CPF inválido! Deve conter exatamente 11 dígitos numéricos.")
        cpf_digitado = None


# ========= Melhoria do v2_2 =========
def ofertar_saque_plus(conta, valor):
    limpar_tela()
    while True:
        print("\n=== Saque Plus ===")
        print(
            f"Deseja sacar além do limite diário por {formatar_brl(ConfigBanco.valor_sacar_plus())}?"
        )
        opcao = input("[s] Sim | [n] Não: ").lower()

        match opcao:
            case "s":
                saque_plus = SaquePlus(valor)
                # return conta.registrar_transacao(saque_plus)
                return saque_plus.executar(conta)
            case "n":
                limpar_tela()
                return False, "❌ Operação cancelada pelo usuário."
            case _:
                print("Opção inválida, tente novamente.")


def ofertar_transacao_plus(conta):
    limpar_tela()
    while True:
        print("\n=== Transação Plus ===")
        print("Você atingiu o limite diário de operações.")
        print(
            f"Deseja ativar uma Transação Plus por {formatar_brl(ConfigBanco.valor_transacao_plus())}?"
        )
        opcao = input("[s] Sim | [n] Não: ").lower()

        match opcao:
            case "s":
                trans_plus = TransacaoPlus()
                return trans_plus.executar(conta)
            case "n":
                return (
                    False,
                    "❌ Operação cancelada! Limite diário de operações atingido.",
                )
            case _:
                print("Opção inválida, tente novamente.")


# ========= Novos v3_0 =========
class ConfigBanco:
    _LIMITE_SAQUE = Decimal("500.00")
    _VALOR_SACAR_PLUS = Decimal("0.50")
    _VALOR_TRANSACAO_PLUS = Decimal("0.25")
    _VALOR_IMPRIMIR_EXTRATO = Decimal("0.00")
    _OPERACOES_DIARIAS = 10
    _SAQUES_DIARIOS = 3
    _AGENCIA_PADRAO = "0001"
    _ARQ_CONTAS = "contas_bancarias.json"
    _ARQ_TRANSACOES = "transacoes_bancarias.json"

    @classmethod
    def limite_saque(cls):
        return cls._LIMITE_SAQUE

    @classmethod
    def valor_sacar_plus(cls):
        return cls._VALOR_SACAR_PLUS

    @classmethod
    def valor_transacao_plus(cls):
        return cls._VALOR_TRANSACAO_PLUS

    @classmethod
    def operacoes_diarias(cls):
        return cls._OPERACOES_DIARIAS

    @classmethod
    def saques_diarios(cls):
        return cls._SAQUES_DIARIOS

    @classmethod
    def agencia_padrao(cls):
        return cls._AGENCIA_PADRAO

    @classmethod
    def arquivo_contas(cls):
        return cls._ARQ_CONTAS

    @classmethod
    def arquivo_transacoes(cls):
        return cls._ARQ_TRANSACOES

    @classmethod
    def valor_imprimir_extrato(cls):
        return cls._VALOR_IMPRIMIR_EXTRATO


class Transacao(ABC):
    @abstractmethod
    def executar(self, conta):
        pass


class Conta:
    def __init__(self, agencia, nro_conta, cpf):
        # Identificação da conta
        self._agencia = agencia
        self._nro_conta = nro_conta
        self._cpf = cpf

        # Variáveis Dinâmicas da Conta
        self._ultimo_dia = date.today()
        self._saldo = Decimal("0.00")
        self._transacao_plus = 0
        self._nro_operacoes = 0
        self._nro_saques = 0
        self._extrato = []

    def _id(self):
        return f"{self._cpf}-{self._agencia}-{self._nro_conta}"

    def carregar_bd_conta(self):
        arq = ConfigBanco.arquivo_transacoes()
        if not os.path.exists(arq):
            return
        try:
            with open(arq, "r", encoding="utf-8") as f:
                dados = json.load(f)
            conta = dados.get(self._id())
            if conta:
                self._ultimo_dia = date.fromisoformat(conta["ultimo_dia"])
                self._saldo = Decimal(conta["saldo"])
                self._transacao_plus = conta["transacao_plus"]
                self._nro_operacoes = conta["numero_operacoes"]
                self._nro_saques = conta["numero_saques"]
                self._extrato = [
                    (tipo, Decimal(valor), datetime.fromisoformat(data))
                    for tipo, valor, data in conta["extrato"]
                ]
        except json.JSONDecodeError:
            pass

    def salvar_bd_conta(self):
        arq = ConfigBanco.arquivo_transacoes()
        backup = None
        try:
            if os.path.exists(arq):
                backup = arq + ".bkp"
                shutil.copy(arq, backup)

            try:
                with open(arq, "r", encoding="utf-8") as f:
                    conteudo = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                conteudo = {}

            conteudo[self._id()] = {
                "ultimo_dia": self._ultimo_dia.isoformat(),
                "saldo": str(self._saldo),
                "transacao_plus": self._transacao_plus,
                "numero_operacoes": self._nro_operacoes,
                "numero_saques": self._nro_saques,
                "extrato": [
                    (tipo, str(valor), data.isoformat())
                    for tipo, valor, data in self._extrato
                ],
            }

            with open(arq, "w", encoding="utf-8") as f:
                json.dump(conteudo, f, indent=2, ensure_ascii=False)

            if backup:
                os.remove(backup)
            return True
        except Exception as e:
            print("❌ Erro ao salvar transações:", e)
            if backup and os.path.exists(backup):
                shutil.move(backup, arq)
            return False

    def saldo_atual(self):
        return self._saldo

    def pode_operar(self):
        limite_total = ConfigBanco.operacoes_diarias() + self._transacao_plus
        return self._nro_operacoes < limite_total

    def registrar_transacao(self, transacao: Transacao):
        # verifica limite de operações
        if not self.pode_operar():
            return ofertar_transacao_plus(self)

        ok, msg = transacao.executar(self)
        # só incrementa contador se a operação realmente ocorreu

        if ok:
            self._nro_operacoes += 1

        return msg

    def resetar_contadores(self):
        hoje = date.today()
        if hoje != self._ultimo_dia:
            self._ultimo_dia = hoje
            self._transacao_plus = 0
            self._nro_operacoes = 0
            self._nro_saques = 0
            return True, (
                f"✔️ Contadores diários resetados. "
                f"Você possui {ConfigBanco.operacoes_diarias()} operações e "
                f"{ConfigBanco.saques_diarios()} saques hoje."
            )
        return False, "❌ Ainda no mesmo dia, nada a resetar."

    def exibir_extrato(self):
        if not self._extrato:
            print("❌ Não foram realizadas movimentações.")
        else:
            print("\n=== EXTRATO ===")
            for tipo, valor, data in self._extrato:
                data_local = data.astimezone()
                data_formatada = data_local.strftime("%d/%m/%Y %H:%M:%S")
                sinal = "+" if valor > 0 else "-"
                # print(f"{tipo}: {sinal}{formatar_brl(abs(valor))} | {data_formatada}")
                valor_fmt = f"{sinal}{formatar_brl(abs(valor))}"
                # coluna tipo = 18 caracteres, valor = 15 caracteres
                print(f"{tipo:<18}| {valor_fmt:<15}|  {data_formatada}")

            print(f"\nSaldo atual: {formatar_brl(self._saldo)}")
            print(
                f"\nOperações hoje: {self._nro_operacoes}/{ConfigBanco.operacoes_diarias() + self._transacao_plus}"
            )
            print(f"Saques hoje: {self._nro_saques}/{ConfigBanco.saques_diarios()}")
            print("=== FIM DO EXTRATO ===")

    def imprimir_extrato(self):
        if not self._extrato:
            print("❌ Não foram realizadas movimentações.")
        else:
            taxa_imp = ConfigBanco.valor_imprimir_extrato()
            self._nro_operacoes += 1
            self._saldo -= taxa_imp
            self._extrato.append(
                ("Imprimir Extrato", -taxa_imp, datetime.now(timezone.utc))
            )
            self.exibir_extrato()

    def __str__(self):
        return f"Agência: {self._agencia} | Conta: {self._nro_conta}"


class ValidadorValor:
    @staticmethod
    def ler_valor(msg_entrada):
        """Chegar input do usuário e retornar Decimal válido"""
        while True:
            valor_digitado = input(msg_entrada).replace(",", ".")

            # rejeitar letras e notação exponencial
            if any(c.isalpha() for c in valor_digitado):
                limpar_tela()
                print("Entrada inválida! O valor não pode conter letras.")
                continue
            try:
                valor = Decimal(valor_digitado)
                ok, msg = ValidadorValor.validar(valor)
                if ok:
                    return valor
                else:
                    print(msg)
            except InvalidOperation:
                limpar_tela()
                print(
                    "Entrada inválida! Digite apenas números positivos, com até duas casas decimais."
                )

    @staticmethod
    def validar(valor):
        """Valida regra de negócio em qualquer Decimal"""
        if not isinstance(valor, Decimal):
            return False, "❌ Valor deve ser Decimal."
        if valor <= 0:
            return False, "❌ Valor deve ser positivo."
        if not tem_duas_casas(valor):
            return False, "❌ Valor deve ter até duas casas decimais."
        return True, ""


class SaquePlus(Transacao):
    def __init__(self, valor):
        self.valor = valor

    def executar(self, conta):
        # valida saldo suficiente para o valor + taxa extra
        taxa = ConfigBanco.valor_sacar_plus()
        valor_total = self.valor + taxa

        if valor_total > conta._saldo:
            return False, "❌ Saldo insuficiente para Saque Plus."

        conta._saldo -= valor_total
        conta._nro_saques += 1
        conta._extrato.append(("Saque Plus", -self.valor, datetime.now(timezone.utc)))
        conta._extrato.append(("Taxa Saque Plus", -taxa, datetime.now(timezone.utc)))

        return (
            True,
            f"✔️ Saque Plus de {formatar_brl(self.valor)} realizado com taxa de {formatar_brl(taxa)}.",
        )


class TransacaoPlus(Transacao):
    def executar(self, conta):
        taxa = ConfigBanco.valor_transacao_plus()

        if taxa > conta._saldo:
            return False, "❌ Saldo insuficiente para ativar Transação Plus."

        conta._saldo -= taxa
        conta._transacao_plus += 1
        conta._extrato.append(("Transação Plus", -taxa, datetime.now(timezone.utc)))

        return (
            True,
            f"✔️ Transação Plus ativada por {formatar_brl(taxa)}.\n Você ativou +1 operação extra para hoje.",
        )


class Deposito(Transacao):
    def __init__(self, valor):
        self.valor = valor  # público, informação do usuário

    def executar(self, conta):
        ok, msg = ValidadorValor.validar(self.valor)
        if not ok:
            return False, msg

        conta._saldo += self.valor
        conta._extrato.append(("Depósito", self.valor, datetime.now(timezone.utc)))
        return True, f"✔️ Depósito de {formatar_brl(self.valor)} realizado."


class Saque(Transacao):
    def __init__(self, valor):
        self.valor = valor

    def executar(self, conta):
        ok, msg = ValidadorValor.validar(self.valor)
        if not ok:
            return False, msg

        # 1. Limite de valor por saque (segurança)
        if self.valor > ConfigBanco.limite_saque():
            return (
                False,
                f"❌ Saque acima do limite de {formatar_brl(ConfigBanco.limite_saque())}",
            )

        # 2. Saldo insuficiente
        if self.valor > conta._saldo:
            return False, "❌ Saldo insuficiente."

        # 3. Limite de número de saques → oferta Saque Plus
        if conta._nro_saques >= ConfigBanco.saques_diarios():
            return ofertar_saque_plus(conta, self.valor)

        # 4. Saque normal
        conta._saldo -= self.valor
        conta._nro_saques += 1
        conta._extrato.append(("Saque", -self.valor, datetime.now(timezone.utc)))
        return True, f"✔️ Saque de {formatar_brl(self.valor)} realizado."


class Usuario:
    def __init__(self, cpf, nome, data_nascimento, endereco):
        self.cpf = cpf
        self.nome = nome
        self.data_nascimento = data_nascimento
        self.endereco = endereco
        self.contas = []

    def adicionar_conta(self, conta):
        self.contas.append(conta)

    def listar_contas(self):
        if not self.contas:
            return "❌ Nenhuma conta encontrada para este CPF."
        return "\n".join(str(conta) for conta in self.contas)


class DadosBanco:
    def __init__(self):
        self.usuarios = []
        dados = self.carregar_bd_usuario()

        for cpf, dados_user in dados.items():
            usuario = Usuario(
                cpf,
                dados_user["nome"],
                dados_user["data_nascimento"],
                dados_user["endereco"],
            )
            for conta in dados_user["contas"]:
                c = Conta(conta["agencia"], conta["numero_conta"], cpf)
                c.carregar_bd_conta()
                usuario.adicionar_conta(c)

            self.usuarios.append(usuario)

    # métodos públicos de usuários
    def carregar_bd_usuario(self):
        arq = ConfigBanco.arquivo_contas()
        if not os.path.exists(arq):
            return {}
        try:
            with open(arq, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def salvar_bd_usuario(self, dados):
        arq = ConfigBanco.arquivo_contas()
        backup = None
        try:
            if os.path.exists(arq):
                backup = arq + ".bkp"
                shutil.copy(arq, backup)

            with open(arq, "w", encoding="utf-8") as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)

            if backup:
                os.remove(backup)
        except Exception as e:
            print("❌ Erro ao salvar contas:", e)
            if backup and os.path.exists(backup):
                shutil.move(backup, arq)

    # métodos da contas
    def buscar_usuario(self, cpf):
        return next((user for user in self.usuarios if user.cpf == cpf), None)

    def criar_usuario(
        self, cpf_digitado, nome=None, data_nascimento=None, endereco=None
    ):
        cpf = checar_limpar_cpf(cpf_digitado)

        # já existe?
        if self.buscar_usuario(cpf):
            return False, f"❌ Já existe usuário com esse CPF {formatar_cpf(cpf)}."

        # se não veio nome ainda, estamos no fluxo interativo → pedir dados
        if not nome:
            print("\n=== Cadastro de Novo Usuário ===")
            nome = input("Nome completo: ").strip()
            data_nascimento = input("Data nascimento (DD/MM/AAAA): ").strip()
            endereco = input("Endereço (logradouro, nº - bairro - cidade/UF): ").strip()

        # cria usuário
        usuario = Usuario(cpf, nome, data_nascimento, endereco)
        self.usuarios.append(usuario)

        # salva no JSON
        dados_json = self.carregar_bd_usuario()
        dados_json[cpf] = {
            "cpf": cpf,
            "nome": nome,
            "data_nascimento": data_nascimento,
            "endereco": endereco,
            "contas": [],
        }
        self.salvar_bd_usuario(dados_json)

        return (
            True,
            f"✔️ Usuário {usuario.nome} criado com sucesso (CPF {formatar_cpf(cpf)}).",
        )

    def criar_conta(self, cpf_digitado):
        cpf = checar_limpar_cpf(cpf_digitado)
        usuario = self.buscar_usuario(cpf)
        if not usuario:
            return False, "❌ Usuário não encontrado."

        # listar contas existentes do usuário
        if usuario.contas:
            print(
                f"\nContas já existentes para {usuario.nome} (CPF {formatar_cpf(cpf)}):"
            )
            print(usuario.listar_contas())
        else:
            print(f"\nUsuário {usuario.nome} ainda não possui contas.")

        # confirmação
        opcao = input("Deseja criar uma nova conta? [s/n]: ").lower().strip()
        if opcao != "s":
            limpar_tela()
            return False, "❌ Operação cancelada pelo usuário."

        # 🔑 gerar número sequencial global
        todos_numeros = [c._nro_conta for u in self.usuarios for c in u.contas]
        novo_numero = max(todos_numeros, default=0) + 1

        # cria a nova conta
        conta = Conta(ConfigBanco.agencia_padrao(), novo_numero, usuario.cpf)
        usuario.adicionar_conta(conta)

        # atualizar JSON
        dados_json = self.carregar_bd_usuario()
        if cpf in dados_json:
            dados_json[cpf]["contas"].append(
                {"agencia": conta._agencia, "numero_conta": conta._nro_conta}
            )
            self.salvar_bd_usuario(dados_json)

        return True, f"✔️ Nova conta criada: {conta}"

    def listar_contas(self, cpf_digitado):
        cpf = checar_limpar_cpf(cpf_digitado)
        usuario = self.buscar_usuario(cpf)
        if not usuario:
            return False, f"❌ Nenhum usuário encontrado com CPF {formatar_cpf(cpf)}."
        return True, usuario.listar_contas()

    def acessar_conta(self, cpf_digitado, agencia, nro_conta):
        cpf = checar_limpar_cpf(cpf_digitado)
        usuario = self.buscar_usuario(cpf)
        if not usuario:
            return False, f"❌ Usuário não encontrado com CPF {formatar_cpf(cpf)}."

        for conta in usuario.contas:
            if conta._agencia == agencia and conta._nro_conta == int(nro_conta):
                return True, conta

        return False, f"❌ Agência ou conta inválida para o CPF {formatar_cpf(cpf)}."

    def salvar_dados_conta(self):
        dados_json = {}
        for usuario in self.usuarios:
            dados_json[usuario.cpf] = {
                "cpf": usuario.cpf,
                "nome": usuario.nome,
                "data_nascimento": usuario.data_nascimento,
                "endereco": usuario.endereco,
                "contas": [
                    {"agencia": c._agencia, "numero_conta": c._nro_conta}
                    for c in usuario.contas
                ],
            }
        self.salvar_bd_usuario(dados_json)


# Menus
def menu_conta(conta: Conta):
    while True:
        mudou, msg = conta.resetar_contadores()
        if mudou:
            print(msg)
            conta.salvar_bd_conta()  # persistir virada de dia

        print(f"\n=== MENU CONTA {conta} ===")
        print("[d] Depositar")
        print("[s] Sacar")
        print("[e] Exibir extrato")
        print("[i] Imprimir extrato")
        print("[v] Voltar")

        opcao = input("Escolha uma opção: ").lower().strip()
        limpar_tela()

        match opcao:
            case "d":
                valor = ValidadorValor.ler_valor("Informe o valor do depósito: ")
                resultado = conta.registrar_transacao(Deposito(valor))
                print(resultado)
                if "✔️" in resultado:  # só salva se deu certo
                    conta.salvar_bd_conta()

            case "s":
                valor = ValidadorValor.ler_valor("Informe o valor do saque: ")
                resultado = conta.registrar_transacao(Saque(valor))
                print(resultado)
                if "✔️" in resultado:  # só salva se deu certo
                    conta.salvar_bd_conta()

            case "e":
                conta.exibir_extrato()

            case "i":
                conta.imprimir_extrato()
                conta.salvar_bd_conta()  # sempre salva, pois consome operação

            case "v":
                print("Voltando ao menu inicial...")
                # só salva se houver diferença desde o último salvamento
                if conta._extrato or conta._nro_operacoes > 0 or conta._nro_saques > 0:
                    conta.salvar_bd_conta()
                break

            case _:
                print("Opção inválida.")


if __name__ == "__main__":
    banco = DadosBanco()

    while True:
        print("\n=== MENU INICIAL ===")
        print("[nu] Novo usuário")
        print("[nc] Nova conta")
        print("[lc] Listar contas")
        print("[ac] Acessar conta")
        print("[q] Sair")

        opcao = input("Escolha uma opção: ").lower().strip()
        limpar_tela()

        match opcao:
            case "nu":
                cpf = input("CPF: ")
                ok, msg = banco.criar_usuario(cpf)
                print(msg)

            case "nc":
                cpf = input("CPF do usuário: ")
                ok, msg = banco.criar_conta(cpf)
                print(msg)

            case "lc":
                cpf = input("CPF: ")
                ok, msg = banco.listar_contas(cpf)
                print(msg)

            case "ac":
                cpf = input("CPF: ")
                ag = input("Agência: ")
                nro = input("Número da conta: ")
                ok, conta = banco.acessar_conta(cpf, ag, nro)
                if ok:
                    menu_conta(conta)  # chamamos função do menu de operações
                else:
                    print(conta)  # aqui 'conta' contém a mensagem de erro

            case "q":
                print("aguarde enquanto encerramos o banco...")
                # salvar os usuários e contas antes de sair
                dados_json = banco.carregar_bd_usuario()
                for usuario in banco.usuarios:
                    dados_json[usuario.cpf] = {
                        "cpf": usuario.cpf,
                        "nome": usuario.nome,
                        "data_nascimento": usuario.data_nascimento,
                        "endereco": usuario.endereco,
                        "contas": [
                            {"agencia": c._agencia, "numero_conta": c._nro_conta}
                            for c in usuario.contas
                        ],
                    }
                banco.salvar_bd_usuario(dados_json)
                print("Obrigado por utilizar nosso sistema bancário!")
                break
            case _:
                print("Opção inválida.")
