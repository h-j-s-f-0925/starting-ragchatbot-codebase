"""
Level 1: Basic - クラスを使ったテストの基本

このファイルではクラスを使ったテストの基本的な書き方を学びます。
- テストクラスの基本構造
- setUp/tearDownの概念
- クラス内でのテスト整理

実行方法:
pytest examples/level1_basic/test_classes.py -v
"""


# テスト対象のクラス（通常は別ファイルに定義されます）
class Calculator:
    """簡単な電卓クラス"""
    
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def subtract(self, a, b):
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result
    
    def get_history(self):
        return self.history.copy()
    
    def clear_history(self):
        self.history.clear()


class BankAccount:
    """銀行口座クラス"""
    
    def __init__(self, initial_balance=0):
        self.balance = initial_balance
        self.transactions = []
    
    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("入金額は正の数である必要があります")
        self.balance += amount
        self.transactions.append(f"入金: +{amount}")
    
    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("出金額は正の数である必要があります")
        if amount > self.balance:
            raise ValueError("残高不足です")
        self.balance -= amount
        self.transactions.append(f"出金: -{amount}")
    
    def get_balance(self):
        return self.balance


# ここからテストコード

class TestCalculator:
    """Calculator クラスのテスト"""
    
    def test_calculator_creation(self):
        """電卓の作成テスト"""
        calc = Calculator()
        assert calc.get_history() == []
    
    def test_add_operation(self):
        """足し算のテスト"""
        calc = Calculator()
        result = calc.add(5, 3)
        assert result == 8
        
        # 履歴も確認
        history = calc.get_history()
        assert len(history) == 1
        assert "5 + 3 = 8" in history
    
    def test_subtract_operation(self):
        """引き算のテスト"""
        calc = Calculator()
        result = calc.subtract(10, 4)
        assert result == 6
        
        # 履歴も確認
        history = calc.get_history()
        assert len(history) == 1
        assert "10 - 4 = 6" in history
    
    def test_multiple_operations(self):
        """複数の操作のテスト"""
        calc = Calculator()
        
        # 複数の操作を実行
        calc.add(1, 2)
        calc.subtract(5, 3)
        calc.add(10, 20)
        
        history = calc.get_history()
        assert len(history) == 3
        assert "1 + 2 = 3" in history
        assert "5 - 3 = 2" in history
        assert "10 + 20 = 30" in history
    
    def test_clear_history(self):
        """履歴クリアのテスト"""
        calc = Calculator()
        
        # 何回か操作をしてから履歴をクリア
        calc.add(1, 1)
        calc.add(2, 2)
        assert len(calc.get_history()) == 2
        
        calc.clear_history()
        assert len(calc.get_history()) == 0


class TestBankAccount:
    """BankAccount クラスのテスト"""
    
    def test_account_creation_default_balance(self):
        """デフォルト残高での口座作成テスト"""
        account = BankAccount()
        assert account.get_balance() == 0
        assert account.transactions == []
    
    def test_account_creation_with_initial_balance(self):
        """初期残高指定での口座作成テスト"""
        account = BankAccount(1000)
        assert account.get_balance() == 1000
        assert account.transactions == []
    
    def test_deposit_valid_amount(self):
        """有効な金額での入金テスト"""
        account = BankAccount()
        account.deposit(500)
        
        assert account.get_balance() == 500
        assert len(account.transactions) == 1
        assert "入金: +500" in account.transactions
    
    def test_deposit_multiple_times(self):
        """複数回入金のテスト"""
        account = BankAccount()
        
        account.deposit(100)
        account.deposit(200)
        account.deposit(50)
        
        assert account.get_balance() == 350
        assert len(account.transactions) == 3
    
    def test_withdraw_valid_amount(self):
        """有効な金額での出金テスト"""
        account = BankAccount(1000)
        account.withdraw(300)
        
        assert account.get_balance() == 700
        assert len(account.transactions) == 1
        assert "出金: -300" in account.transactions
    
    def test_deposit_invalid_amount(self):
        """無効な金額での入金テスト（エラーケース）"""
        account = BankAccount()
        
        # ゼロ以下の入金はエラーになるべき
        try:
            account.deposit(0)
            assert False, "エラーが発生するべきです"
        except ValueError as e:
            assert "正の数である必要があります" in str(e)
        
        try:
            account.deposit(-100)
            assert False, "エラーが発生するべきです"
        except ValueError as e:
            assert "正の数である必要があります" in str(e)
    
    def test_withdraw_insufficient_funds(self):
        """残高不足での出金テスト（エラーケース）"""
        account = BankAccount(100)
        
        try:
            account.withdraw(200)
            assert False, "残高不足エラーが発生するべきです"
        except ValueError as e:
            assert "残高不足です" in str(e)
        
        # 残高は変更されていないことを確認
        assert account.get_balance() == 100
    
    def test_complete_transaction_flow(self):
        """完全な取引フローのテスト"""
        account = BankAccount(500)  # 初期残高 500
        
        # 入金
        account.deposit(200)
        assert account.get_balance() == 700
        
        # 出金
        account.withdraw(100)
        assert account.get_balance() == 600
        
        # 再度入金
        account.deposit(50)
        assert account.get_balance() == 650
        
        # 取引履歴の確認
        assert len(account.transactions) == 3
        assert "入金: +200" in account.transactions
        assert "出金: -100" in account.transactions
        assert "入金: +50" in account.transactions