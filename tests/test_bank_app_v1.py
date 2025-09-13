import pytest  # pyright: ignore[reportMissingImports]
from decimal import Decimal
import bank_app_v1


@pytest.fixture(autouse=True)
def reset_estado():
    bank_app_v1.saldo = Decimal("0.00")
    bank_app_v1.extrato = []


def test_depositar_valor_positivo():
    bank_app_v1.depositar(Decimal("100.00"))
    assert bank_app_v1.saldo == Decimal("100.00")
    assert bank_app_v1.extrato[-1] == ("Depósito", Decimal("100.00"))


def test_depositar_valor_negativo():
    valor_inicial = bank_app_v1.saldo
    bank_app_v1.depositar(Decimal("-50.00"))
    assert bank_app_v1.saldo == valor_inicial  # saldo não deve mudar


def test_depositar_valor_casa_decimal():
    valor_inicial = bank_app_v1.saldo
    bank_app_v1.depositar(Decimal("50.00322"))
    assert bank_app_v1.saldo == valor_inicial  # saldo não deve mudar


def test_sacar_valor_negativo():
    bank_app_v1.depositar(Decimal("100.00"))
    mensagem = bank_app_v1.sacar(Decimal("-20.00"))
    assert (
        mensagem
        == "Operação cancelada! Informar valor positivo com até duas casas decimais."
    )
    assert bank_app_v1.saldo == Decimal("100.00")  # saldo não deve mudar
