"""
Модульные тесты банковского счёта (unittest).

Запуск:  python -m unittest test_bank_account -v
"""

import unittest
from decimal import Decimal

from bank_account import (
    BankAccount,
    InvalidOwnerError,
    InvalidAccountNumberError,
    InvalidAmountError,
    InsufficientFundsError,
    InvalidTransferError,
)

# Значения, которые не должны приниматься как сумма
BAD_AMOUNTS = [
    ("ноль", 0),
    ("отрицательное целое", -100),
    ("отрицательное дробное", -0.01),
    ("строка", "100"),
    ("None", None),
    ("список", [100]),
    ("bool True", True),
    ("NaN", float("nan")),
    ("бесконечность", float("inf")),
    ("больше 2 знаков", 10.001),
]


class TestCreateAccount(unittest.TestCase):
    """Создание счёта."""

    def test_owner_is_stored(self):
        acc = BankAccount("Иван Петров", "ACC-001")
        self.assertEqual(acc.owner, "Иван Петров")

    def test_account_number_is_stored(self):
        acc = BankAccount("Иван Петров", "ACC-001")
        self.assertEqual(acc.account_number, "ACC-001")

    def test_initial_balance_is_zero(self):
        acc = BankAccount("Иван Петров", "ACC-001")
        self.assertEqual(acc.get_balance(), 0)

    def test_owner_and_number_are_trimmed(self):
        acc = BankAccount("  Иван  ", "  ACC-001 ")
        self.assertEqual(acc.owner, "Иван")
        self.assertEqual(acc.account_number, "ACC-001")

    def test_empty_owner_rejected(self):
        for owner in ("", "   ", None, 123):
            with self.subTest(owner=owner):
                with self.assertRaises(InvalidOwnerError):
                    BankAccount(owner, "ACC-001")

    def test_empty_account_number_rejected(self):
        for number in ("", "   ", None, 123):
            with self.subTest(number=number):
                with self.assertRaises(InvalidAccountNumberError):
                    BankAccount("Иван", number)

    def test_owner_cannot_be_changed_directly(self):
        acc = BankAccount("Иван", "ACC-001")
        with self.assertRaises(AttributeError):
            acc.owner = "Другой"

    def test_account_number_cannot_be_changed_directly(self):
        acc = BankAccount("Иван", "ACC-001")
        with self.assertRaises(AttributeError):
            acc.account_number = "ACC-999"

    def test_accounts_are_independent(self):
        a = BankAccount("А", "1")
        b = BankAccount("Б", "2")
        a.deposit(100)
        self.assertEqual(b.get_balance(), 0)


class TestDeposit(unittest.TestCase):
    """Пополнение счёта."""

    def setUp(self):
        self.acc = BankAccount("Иван", "ACC-001")

    def test_deposit_increases_balance(self):
        self.acc.deposit(100)
        self.assertEqual(self.acc.get_balance(), 100)

    def test_deposit_returns_new_balance(self):
        self.assertEqual(self.acc.deposit(250), 250)

    def test_multiple_deposits_accumulate(self):
        self.acc.deposit(100)
        self.acc.deposit(50)
        self.acc.deposit(25)
        self.assertEqual(self.acc.get_balance(), 175)

    def test_deposit_minimal_amount(self):
        self.acc.deposit(0.01)
        self.assertEqual(self.acc.get_balance(), Decimal("0.01"))

    def test_deposit_fractional_amount(self):
        self.acc.deposit(100.50)
        self.assertEqual(self.acc.get_balance(), Decimal("100.50"))

    def test_deposit_has_no_float_errors(self):
        self.acc.deposit(0.1)
        self.acc.deposit(0.2)
        self.assertEqual(self.acc.get_balance(), Decimal("0.3"))

    def test_deposit_accepts_decimal(self):
        self.acc.deposit(Decimal("10.25"))
        self.assertEqual(self.acc.get_balance(), Decimal("10.25"))

    def test_deposit_large_amount(self):
        self.acc.deposit(10**12)
        self.assertEqual(self.acc.get_balance(), 10**12)

    def test_invalid_deposit_rejected(self):
        for name, value in BAD_AMOUNTS:
            with self.subTest(case=name):
                with self.assertRaises(InvalidAmountError):
                    self.acc.deposit(value)

    def test_invalid_deposit_does_not_change_balance(self):
        self.acc.deposit(100)
        for name, value in BAD_AMOUNTS:
            with self.subTest(case=name):
                with self.assertRaises(InvalidAmountError):
                    self.acc.deposit(value)
        self.assertEqual(self.acc.get_balance(), 100)


class TestWithdraw(unittest.TestCase):
    """Снятие средств."""

    def setUp(self):
        self.acc = BankAccount("Иван", "ACC-001")
        self.acc.deposit(1000)

    def test_withdraw_decreases_balance(self):
        self.acc.withdraw(300)
        self.assertEqual(self.acc.get_balance(), 700)

    def test_withdraw_returns_new_balance(self):
        self.assertEqual(self.acc.withdraw(400), 600)

    def test_withdraw_entire_balance_allowed(self):
        self.acc.withdraw(1000)
        self.assertEqual(self.acc.get_balance(), 0)

    def test_withdraw_more_than_balance_rejected(self):
        with self.assertRaises(InsufficientFundsError):
            self.acc.withdraw(1000.01)

    def test_withdraw_one_kopeck_over_balance_rejected(self):
        with self.assertRaises(InsufficientFundsError):
            self.acc.withdraw(Decimal("1000.01"))

    def test_failed_withdraw_does_not_change_balance(self):
        with self.assertRaises(InsufficientFundsError):
            self.acc.withdraw(5000)
        self.assertEqual(self.acc.get_balance(), 1000)

    def test_withdraw_from_empty_account_rejected(self):
        empty = BankAccount("Пётр", "ACC-002")
        with self.assertRaises(InsufficientFundsError):
            empty.withdraw(1)

    def test_invalid_withdraw_rejected(self):
        for name, value in BAD_AMOUNTS:
            with self.subTest(case=name):
                with self.assertRaises(InvalidAmountError):
                    self.acc.withdraw(value)

    def test_invalid_withdraw_does_not_change_balance(self):
        for name, value in BAD_AMOUNTS:
            with self.subTest(case=name):
                with self.assertRaises(InvalidAmountError):
                    self.acc.withdraw(value)
        self.assertEqual(self.acc.get_balance(), 1000)

    def test_withdraw_fractional(self):
        self.acc.withdraw(0.01)
        self.assertEqual(self.acc.get_balance(), Decimal("999.99"))

    def test_sequential_withdrawals(self):
        self.acc.withdraw(400)
        self.acc.withdraw(400)
        with self.assertRaises(InsufficientFundsError):
            self.acc.withdraw(400)
        self.assertEqual(self.acc.get_balance(), 200)


class TestTransfer(unittest.TestCase):
    """Перевод между счетами."""

    def setUp(self):
        self.sender = BankAccount("Отправитель", "ACC-001")
        self.receiver = BankAccount("Получатель", "ACC-002")
        self.sender.deposit(1000)
        self.receiver.deposit(500)

    def test_sender_balance_decreases(self):
        self.sender.transfer(self.receiver, 300)
        self.assertEqual(self.sender.get_balance(), 700)

    def test_receiver_balance_increases(self):
        self.sender.transfer(self.receiver, 300)
        self.assertEqual(self.receiver.get_balance(), 800)

    def test_change_is_equal_for_both_accounts(self):
        before_sender = self.sender.get_balance()
        before_receiver = self.receiver.get_balance()
        self.sender.transfer(self.receiver, 123.45)
        lost = before_sender - self.sender.get_balance()
        gained = self.receiver.get_balance() - before_receiver
        self.assertEqual(lost, gained)
        self.assertEqual(lost, Decimal("123.45"))

    def test_total_money_is_preserved(self):
        total_before = self.sender.get_balance() + self.receiver.get_balance()
        self.sender.transfer(self.receiver, 777.77)
        total_after = self.sender.get_balance() + self.receiver.get_balance()
        self.assertEqual(total_before, total_after)

    def test_transfer_entire_balance(self):
        self.sender.transfer(self.receiver, 1000)
        self.assertEqual(self.sender.get_balance(), 0)
        self.assertTrue(self.sender.is_empty())
        self.assertEqual(self.receiver.get_balance(), 1500)

    def test_transfer_to_empty_account(self):
        empty = BankAccount("Новый", "ACC-003")
        self.sender.transfer(empty, 100)
        self.assertEqual(empty.get_balance(), 100)
        self.assertFalse(empty.is_empty())

    def test_transfer_does_not_affect_third_account(self):
        third = BankAccount("Третий", "ACC-003")
        third.deposit(50)
        self.sender.transfer(self.receiver, 100)
        self.assertEqual(third.get_balance(), 50)

    def test_insufficient_funds_leaves_both_accounts_unchanged(self):
        with self.assertRaises(InsufficientFundsError):
            self.sender.transfer(self.receiver, 1000.01)
        self.assertEqual(self.sender.get_balance(), 1000)
        self.assertEqual(self.receiver.get_balance(), 500)

    def test_invalid_amount_leaves_both_accounts_unchanged(self):
        for name, value in BAD_AMOUNTS:
            with self.subTest(case=name):
                with self.assertRaises(InvalidAmountError):
                    self.sender.transfer(self.receiver, value)
                self.assertEqual(self.sender.get_balance(), 1000)
                self.assertEqual(self.receiver.get_balance(), 500)

    def test_transfer_to_same_account_rejected(self):
        with self.assertRaises(InvalidTransferError):
            self.sender.transfer(self.sender, 100)
        self.assertEqual(self.sender.get_balance(), 1000)

    def test_transfer_to_account_with_same_number_rejected(self):
        twin = BankAccount("Двойник", "ACC-001")
        with self.assertRaises(InvalidTransferError):
            self.sender.transfer(twin, 100)
        self.assertEqual(self.sender.get_balance(), 1000)
        self.assertEqual(twin.get_balance(), 0)

    def test_transfer_to_non_account_rejected(self):
        for target in (None, "ACC-002", 123, object()):
            with self.subTest(target=target):
                with self.assertRaises(InvalidTransferError):
                    self.sender.transfer(target, 100)
                self.assertEqual(self.sender.get_balance(), 1000)

    def test_transfer_from_empty_account_rejected(self):
        empty = BankAccount("Пустой", "ACC-009")
        with self.assertRaises(InsufficientFundsError):
            empty.transfer(self.receiver, 1)
        self.assertEqual(empty.get_balance(), 0)
        self.assertEqual(self.receiver.get_balance(), 500)

    def test_transfer_back_and_forth(self):
        self.sender.transfer(self.receiver, 200)
        self.receiver.transfer(self.sender, 200)
        self.assertEqual(self.sender.get_balance(), 1000)
        self.assertEqual(self.receiver.get_balance(), 500)


class TestGetBalance(unittest.TestCase):
    """Получение баланса."""

    def test_balance_after_series_of_operations(self):
        acc = BankAccount("Иван", "ACC-001")
        other = BankAccount("Пётр", "ACC-002")
        acc.deposit(1000)       # 1000
        acc.withdraw(250.50)    # 749.50
        acc.deposit(100)        # 849.50
        acc.transfer(other, 49.50)  # 800.00
        self.assertEqual(acc.get_balance(), Decimal("800.00"))
        self.assertEqual(other.get_balance(), Decimal("49.50"))

    def test_get_balance_does_not_change_balance(self):
        acc = BankAccount("Иван", "ACC-001")
        acc.deposit(100)
        acc.get_balance()
        acc.get_balance()
        self.assertEqual(acc.get_balance(), 100)

    def test_balance_never_negative(self):
        acc = BankAccount("Иван", "ACC-001")
        acc.deposit(100)
        for amount in (60, 60, 40, 1):
            try:
                acc.withdraw(amount)
            except InsufficientFundsError:
                pass
            self.assertGreaterEqual(acc.get_balance(), 0)


class TestIsEmpty(unittest.TestCase):
    """Проверка пустого счёта."""

    def test_new_account_is_empty(self):
        self.assertTrue(BankAccount("Иван", "ACC-001").is_empty())

    def test_account_with_money_is_not_empty(self):
        acc = BankAccount("Иван", "ACC-001")
        acc.deposit(100)
        self.assertFalse(acc.is_empty())

    def test_account_with_minimal_balance_is_not_empty(self):
        acc = BankAccount("Иван", "ACC-001")
        acc.deposit(0.01)
        self.assertFalse(acc.is_empty())

    def test_account_becomes_empty_after_full_withdrawal(self):
        acc = BankAccount("Иван", "ACC-001")
        acc.deposit(100)
        acc.withdraw(100)
        self.assertTrue(acc.is_empty())

    def test_account_becomes_empty_after_full_transfer(self):
        a = BankAccount("А", "1")
        b = BankAccount("Б", "2")
        a.deposit(100)
        a.transfer(b, 100)
        self.assertTrue(a.is_empty())
        self.assertFalse(b.is_empty())

    def test_failed_withdraw_keeps_account_not_empty(self):
        acc = BankAccount("Иван", "ACC-001")
        acc.deposit(50)
        with self.assertRaises(InsufficientFundsError):
            acc.withdraw(100)
        self.assertFalse(acc.is_empty())

    def test_is_empty_returns_bool(self):
        self.assertIsInstance(BankAccount("Иван", "1").is_empty(), bool)


if __name__ == "__main__":
    unittest.main(verbosity=2)
