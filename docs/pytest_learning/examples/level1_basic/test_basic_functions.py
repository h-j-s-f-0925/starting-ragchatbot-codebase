"""
Level 1: Basic - 最初のpytestテスト

このファイルは pytest を初めて学ぶ人向けの基本的なテスト例です。
- 関数のテスト方法
- アサーションの使い方
- 基本的なテスト構造

実行方法:
pytest examples/level1_basic/test_basic_functions.py -v
"""

# テスト対象の関数たち（通常は別ファイルに定義されます）
def add(a, b):
    """二つの数を足し算する関数"""
    return a + b

def multiply(a, b):
    """二つの数を掛け算する関数"""
    return a * b

def greet(name):
    """挨拶を返す関数"""
    return f"Hello, {name}!"

def is_even(number):
    """数が偶数かどうかを判定する関数"""
    return number % 2 == 0


# ここからテストコード
def test_add_positive_numbers():
    """正の数の足し算テスト"""
    result = add(2, 3)
    assert result == 5

def test_add_negative_numbers():
    """負の数の足し算テスト"""
    result = add(-1, -2)
    assert result == -3

def test_add_zero():
    """0との足し算テスト"""
    result = add(5, 0)
    assert result == 5

def test_multiply_positive_numbers():
    """正の数の掛け算テスト"""
    result = multiply(3, 4)
    assert result == 12

def test_multiply_by_zero():
    """0との掛け算テスト"""
    result = multiply(5, 0)
    assert result == 0

def test_greet_simple_name():
    """シンプルな名前での挨拶テスト"""
    result = greet("Alice")
    assert result == "Hello, Alice!"

def test_greet_empty_name():
    """空の名前での挨拶テスト"""
    result = greet("")
    assert result == "Hello, !"

def test_is_even_with_even_number():
    """偶数の判定テスト"""
    assert is_even(4) == True
    assert is_even(0) == True
    assert is_even(-2) == True

def test_is_even_with_odd_number():
    """奇数の判定テスト"""
    assert is_even(3) == False
    assert is_even(1) == False
    assert is_even(-1) == False

# 複数のアサーションを含むテスト
def test_multiple_operations():
    """複数の操作をテストする例"""
    # 複数のアサーションを一つのテストに含められます
    assert add(1, 1) == 2
    assert multiply(2, 3) == 6
    assert greet("Bob") == "Hello, Bob!"
    
# 異なるアサーション方法の例
def test_different_assertion_styles():
    """異なるアサーション方法の例"""
    result = add(10, 5)
    
    # 等価性チェック
    assert result == 15
    
    # 不等価性チェック
    assert result != 10
    
    # 大小比較
    assert result > 10
    assert result >= 15
    assert result < 20
    assert result <= 15
    
    # 型チェック
    assert isinstance(result, int)
    
    # 真偽値チェック
    assert result  # result が真であることを確認
    assert bool(result)  # 明示的な真偽値変換

# 文字列のテスト例
def test_string_operations():
    """文字列操作のテスト例"""
    greeting = greet("Python")
    
    # 文字列の内容チェック
    assert "Python" in greeting
    assert greeting.startswith("Hello")
    assert greeting.endswith("!")
    
    # 文字列の長さチェック
    assert len(greeting) == 14