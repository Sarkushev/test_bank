"""
Система банковского счёта.

Деньги хранятся в Decimal, а не во float: так нет ошибок округления
вида 0.1 + 0.2 = 0.30000000000000004. Суммы принимаются с точностью
до копеек (не более 2 знаков после запятой).
"""

from decimal import Decimal, InvalidOperation


# ---------- Исключения ----------

class BankError(Exception):
    """Базовая ошибка банковской системы."""


class InvalidOwnerError(BankError, ValueError):
    """Некорректное имя владельца."""


class InvalidAccountNumberError(BankError, ValueError):
    """Некорректный номер счёта."""


class InvalidAmountError(BankError, ValueError):
    """Некорректная сумма операции (не число, <= 0, больше 2 знаков после запятой)."""


class InsufficientFundsError(BankError):
    """Недостаточно средств на счёте."""


class InvalidTransferError(BankError):
    """Перевод невозможен (неверный получатель, перевод самому себе)."""


# ---------- Вспомогательные функции ----------

def to_amount(value) -> Decimal:
    """
    Приводит значение к положительной сумме Decimal.
    Допустимы int, float, Decimal. Не допустимы: bool, str, None, NaN, inf,
    числа <= 0 и числа с более чем 2 знаками после запятой.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise InvalidAmountError("Сумма должна быть числом")

    try:
        # str() для float, чтобы 0.1 стало Decimal('0.1'), а не длинный хвост
        amount = value if isinstance(value, Decimal) else Decimal(str(value))
    except InvalidOperation:
        raise InvalidAmountError("Сумма должна быть числом")

    if not amount.is_finite():
        raise InvalidAmountError("Сумма должна быть конечным числом")
    if amount <= 0:
        raise InvalidAmountError("Сумма должна быть больше нуля")
    if amount != amount.quantize(Decimal("0.01")):
        raise InvalidAmountError("Сумма не может содержать более 2 знаков после запятой")

    return amount


# ---------- Банковский счёт ----------

class BankAccount:
    """Банковский счёт: владелец, номер, баланс."""

    def __init__(self, owner: str, account_number: str):
        if not isinstance(owner, str) or not owner.strip():
            raise InvalidOwnerError("Имя владельца должно быть непустой строкой")
        if not isinstance(account_number, str) or not account_number.strip():
            raise InvalidAccountNumberError("Номер счёта должен быть непустой строкой")

        self._owner = owner.strip()
        self._account_number = account_number.strip()
        self._balance = Decimal("0")

    # --- данные счёта (только чтение) ---

    @property
    def owner(self) -> str:
        return self._owner

    @property
    def account_number(self) -> str:
        return self._account_number

    # --- операции ---

    def deposit(self, amount) -> Decimal:
        """Пополнение счёта. Возвращает новый баланс."""
        amount = to_amount(amount)
        self._balance += amount
        return self._balance

    def withdraw(self, amount) -> Decimal:
        """Снятие средств. Нельзя снять больше, чем есть на счёте."""
        amount = to_amount(amount)
        if amount > self._balance:
            raise InsufficientFundsError(
                f"Недостаточно средств: на счёте {self._balance}, запрошено {amount}"
            )
        self._balance -= amount
        return self._balance

    def transfer(self, other: "BankAccount", amount) -> None:
        """
        Перевод на другой счёт.
        Все проверки выполняются ДО изменения балансов, поэтому при ошибке
        состояние обоих счетов остаётся прежним.
        """
        if not isinstance(other, BankAccount):
            raise InvalidTransferError("Получатель должен быть банковским счётом")
        if other is self or other.account_number == self.account_number:
            raise InvalidTransferError("Нельзя переводить деньги на тот же счёт")

        amount = to_amount(amount)
        if amount > self._balance:
            raise InsufficientFundsError(
                f"Недостаточно средств: на счёте {self._balance}, запрошено {amount}"
            )

        self._balance -= amount
        other._balance += amount

    # --- получение информации ---

    def get_balance(self) -> Decimal:
        return self._balance

    def is_empty(self) -> bool:
        """Счёт пуст, если баланс равен нулю."""
        return self._balance == 0

    def __repr__(self) -> str:
        return (f"BankAccount(owner={self._owner!r}, "
                f"account_number={self._account_number!r}, balance={self._balance})")
