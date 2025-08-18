"""
Level 3: Advanced - パラメータ化とマーカーの活用

このファイルでは pytest の高度な機能について学びます。
- parametrize を使ったテストケースの生成
- カスタムマーカーの作成と活用
- 条件付きテストの実行
- テストの分類と整理

実行方法:
pytest examples/level3_advanced/test_parametrize_markers.py -v
pytest examples/level3_advanced/test_parametrize_markers.py -m "unit"
pytest examples/level3_advanced/test_parametrize_markers.py -m "slow"
"""

import pytest
import math
import sys
import platform
from datetime import datetime, timedelta


# テスト対象の関数とクラス
class Calculator:
    """高機能電卓クラス"""
    
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
    
    def multiply(self, a, b):
        return a * b
    
    def divide(self, a, b):
        if b == 0:
            raise ZeroDivisionError("0で割ることはできません")
        return a / b
    
    def power(self, base, exponent):
        return base ** exponent
    
    def sqrt(self, x):
        if x < 0:
            raise ValueError("負の数の平方根は計算できません")
        return math.sqrt(x)
    
    def factorial(self, n):
        if n < 0:
            raise ValueError("負の数の階乗は計算できません")
        if n == 0 or n == 1:
            return 1
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result


class TextProcessor:
    """テキスト処理クラス"""
    
    def reverse_string(self, text):
        return text[::-1]
    
    def count_words(self, text):
        if not text.strip():
            return 0
        return len(text.split())
    
    def to_uppercase(self, text):
        return text.upper()
    
    def to_lowercase(self, text):
        return text.lower()
    
    def remove_spaces(self, text):
        return text.replace(" ", "")
    
    def is_palindrome(self, text):
        cleaned = self.remove_spaces(text.lower())
        return cleaned == cleaned[::-1]


# カスタムマーカーの定義
pytest_plugins = []


def pytest_configure(config):
    """pytest の設定でカスタムマーカーを登録"""
    config.addinivalue_line("markers", "unit: Unit test for individual functions")
    config.addinivalue_line("markers", "integration: Integration test across components")
    config.addinivalue_line("markers", "slow: Tests that take longer to execute")
    config.addinivalue_line("markers", "math: Mathematical operation tests")
    config.addinivalue_line("markers", "text: Text processing tests")
    config.addinivalue_line("markers", "edge_case: Edge case and boundary tests")
    config.addinivalue_line("markers", "windows_only: Tests that run only on Windows")
    config.addinivalue_line("markers", "linux_only: Tests that run only on Linux")


# ここからテストコード

class TestBasicParametrize:
    """基本的なパラメータ化テスト"""
    
    @pytest.mark.unit
    @pytest.mark.math
    @pytest.mark.parametrize("a,b,expected", [
        (1, 2, 3),
        (0, 0, 0),
        (-1, 1, 0),
        (10, -5, 5),
        (100, 200, 300),
    ])
    def test_addition(self, a, b, expected):
        """足し算のパラメータ化テスト"""
        calc = Calculator()
        result = calc.add(a, b)
        assert result == expected
    
    @pytest.mark.unit
    @pytest.mark.math
    @pytest.mark.parametrize("a,b,expected", [
        (10, 2, 5.0),
        (15, 3, 5.0),
        (7, 2, 3.5),
        (-10, 2, -5.0),
        (0, 5, 0.0),
    ])
    def test_division(self, a, b, expected):
        """割り算のパラメータ化テスト"""
        calc = Calculator()
        result = calc.divide(a, b)
        assert result == expected
    
    @pytest.mark.unit
    @pytest.mark.math
    @pytest.mark.edge_case
    @pytest.mark.parametrize("dividend", [1, 10, -5, 100])
    def test_division_by_zero(self, dividend):
        """0除算エラーのパラメータ化テスト"""
        calc = Calculator()
        with pytest.raises(ZeroDivisionError) as exc_info:
            calc.divide(dividend, 0)
        assert "0で割ることはできません" in str(exc_info.value)


class TestTextProcessingParametrize:
    """テキスト処理のパラメータ化テスト"""
    
    @pytest.mark.unit
    @pytest.mark.text
    @pytest.mark.parametrize("input_text,expected", [
        ("hello", "olleh"),
        ("Python", "nohtyP"),
        ("", ""),
        ("a", "a"),
        ("12345", "54321"),
        ("hello world", "dlrow olleh"),
    ])
    def test_reverse_string(self, input_text, expected):
        """文字列反転のパラメータ化テスト"""
        processor = TextProcessor()
        result = processor.reverse_string(input_text)
        assert result == expected
    
    @pytest.mark.unit
    @pytest.mark.text
    @pytest.mark.parametrize("text,expected_count", [
        ("hello world", 2),
        ("one", 1),
        ("", 0),
        ("   ", 0),
        ("one two three four five", 5),
        ("word", 1),
        ("multiple   spaces   between", 3),
    ])
    def test_count_words(self, text, expected_count):
        """単語数カウントのパラメータ化テスト"""
        processor = TextProcessor()
        result = processor.count_words(text)
        assert result == expected_count
    
    @pytest.mark.unit
    @pytest.mark.text
    @pytest.mark.parametrize("text,expected", [
        ("racecar", True),
        ("hello", False),
        ("A man a plan a canal Panama", True),
        ("race a car", False),
        ("", True),
        ("a", True),
        ("Madam", True),
        ("hello world", False),
    ])
    def test_is_palindrome(self, text, expected):
        """回文判定のパラメータ化テスト"""
        processor = TextProcessor()
        result = processor.is_palindrome(text)
        assert result == expected


class TestComplexParametrize:
    """複雑なパラメータ化テスト"""
    
    @pytest.mark.unit
    @pytest.mark.math
    @pytest.mark.parametrize("base,exponent,expected", [
        (2, 3, 8),
        (5, 0, 1),
        (10, 2, 100),
        (-2, 3, -8),
        (3, -2, 1/9),
    ])
    def test_power_calculation(self, base, exponent, expected):
        """累乗計算のパラメータ化テスト"""
        calc = Calculator()
        result = calc.power(base, exponent)
        assert abs(result - expected) < 1e-10  # 浮動小数点の誤差を考慮
    
    @pytest.mark.unit
    @pytest.mark.math
    @pytest.mark.slow
    @pytest.mark.parametrize("n,expected", [
        (0, 1),
        (1, 1),
        (5, 120),
        (10, 3628800),
    ])
    def test_factorial(self, n, expected):
        """階乗計算のパラメータ化テスト"""
        calc = Calculator()
        result = calc.factorial(n)
        assert result == expected
    
    @pytest.mark.unit
    @pytest.mark.math
    @pytest.mark.edge_case
    @pytest.mark.parametrize("invalid_input", [-1, -5, -10])
    def test_factorial_negative_input(self, invalid_input):
        """階乗の負数入力エラーテスト"""
        calc = Calculator()
        with pytest.raises(ValueError) as exc_info:
            calc.factorial(invalid_input)
        assert "負の数の階乗は計算できません" in str(exc_info.value)


class TestParametrizeWithIds:
    """IDを指定したパラメータ化テスト"""
    
    @pytest.mark.unit
    @pytest.mark.math
    @pytest.mark.parametrize(
        "x,expected",
        [
            (4, 2.0),
            (9, 3.0),
            (16, 4.0),
            (25, 5.0),
            (0, 0.0),
        ],
        ids=["sqrt_4", "sqrt_9", "sqrt_16", "sqrt_25", "sqrt_0"]
    )
    def test_sqrt_with_ids(self, x, expected):
        """平方根計算のID付きパラメータ化テスト"""
        calc = Calculator()
        result = calc.sqrt(x)
        assert abs(result - expected) < 1e-10
    
    @pytest.mark.unit
    @pytest.mark.text
    @pytest.mark.parametrize(
        "operation,input_text,expected",
        [
            ("upper", "hello", "HELLO"),
            ("lower", "WORLD", "world"),
            ("upper", "MixedCase", "MIXEDCASE"),
            ("lower", "MixedCase", "mixedcase"),
        ],
        ids=["to_upper_simple", "to_lower_simple", "to_upper_mixed", "to_lower_mixed"]
    )
    def test_case_conversion_with_ids(self, operation, input_text, expected):
        """大文字小文字変換のID付きテスト"""
        processor = TextProcessor()
        
        if operation == "upper":
            result = processor.to_uppercase(input_text)
        elif operation == "lower":
            result = processor.to_lowercase(input_text)
        
        assert result == expected


class TestConditionalTests:
    """条件付きテスト実行"""
    
    @pytest.mark.unit
    @pytest.mark.skipif(sys.version_info < (3, 8), reason="Python 3.8以上が必要")
    def test_python_version_dependent(self):
        """Python バージョン依存テスト"""
        calc = Calculator()
        result = calc.add(1, 2)
        assert result == 3
    
    @pytest.mark.unit
    @pytest.mark.windows_only
    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows専用テスト")
    def test_windows_specific_feature(self):
        """Windows専用機能テスト"""
        # Windows専用の機能をテスト
        assert platform.system() == "Windows"
    
    @pytest.mark.unit
    @pytest.mark.linux_only
    @pytest.mark.skipif(platform.system() != "Linux", reason="Linux専用テスト")
    def test_linux_specific_feature(self):
        """Linux専用機能テスト"""
        # Linux専用の機能をテスト
        assert platform.system() == "Linux"
    
    @pytest.mark.unit
    @pytest.mark.skipif("CI" in os.environ, reason="CI環境ではスキップ")
    def test_local_environment_only(self):
        """ローカル環境専用テスト"""
        import os
        # ローカル環境でのみ実行するテスト
        assert "CI" not in os.environ


class TestSlowMarkers:
    """実行時間の長いテスト"""
    
    @pytest.mark.slow
    @pytest.mark.math
    def test_large_factorial_calculation(self):
        """大きな数の階乗計算（時間のかかるテスト）"""
        calc = Calculator()
        
        # 比較的大きな数の階乗を計算
        result = calc.factorial(15)
        expected = 1307674368000  # 15!
        
        assert result == expected
    
    @pytest.mark.slow
    @pytest.mark.text
    def test_large_text_processing(self):
        """大量テキスト処理（時間のかかるテスト）"""
        processor = TextProcessor()
        
        # 大きなテキストを生成
        large_text = "word " * 10000
        
        # 単語数をカウント
        word_count = processor.count_words(large_text)
        assert word_count == 10000
        
        # 大文字変換
        upper_text = processor.to_uppercase(large_text)
        assert upper_text == "WORD " * 10000


class TestParametrizeWithFixtures:
    """fixture とパラメータ化の組み合わせ"""
    
    @pytest.fixture
    def calculator(self):
        """Calculator インスタンスを提供"""
        return Calculator()
    
    @pytest.fixture
    def text_processor(self):
        """TextProcessor インスタンスを提供"""
        return TextProcessor()
    
    @pytest.mark.unit
    @pytest.mark.parametrize("operation,a,b,expected", [
        ("add", 1, 2, 3),
        ("subtract", 5, 3, 2),
        ("multiply", 4, 3, 12),
        ("divide", 10, 2, 5.0),
    ])
    def test_calculator_operations_with_fixture(self, calculator, operation, a, b, expected):
        """fixture を使った計算操作のパラメータ化テスト"""
        if operation == "add":
            result = calculator.add(a, b)
        elif operation == "subtract":
            result = calculator.subtract(a, b)
        elif operation == "multiply":
            result = calculator.multiply(a, b)
        elif operation == "divide":
            result = calculator.divide(a, b)
        
        assert result == expected


class TestCustomMarkerCombinations:
    """カスタムマーカーの組み合わせテスト"""
    
    @pytest.mark.unit
    @pytest.mark.math
    @pytest.mark.edge_case
    def test_sqrt_negative_number(self):
        """平方根の負数入力エラーテスト"""
        calc = Calculator()
        with pytest.raises(ValueError) as exc_info:
            calc.sqrt(-1)
        assert "負の数の平方根は計算できません" in str(exc_info.value)
    
    @pytest.mark.integration
    @pytest.mark.math
    @pytest.mark.text
    def test_calculator_and_text_processor_integration(self):
        """Calculator と TextProcessor の統合テスト"""
        calc = Calculator()
        processor = TextProcessor()
        
        # 計算結果を文字列として処理
        result = calc.add(123, 456)
        result_str = str(result)
        
        # 文字列を反転
        reversed_str = processor.reverse_string(result_str)
        assert reversed_str == "975"
        
        # 単語数をカウント
        word_count = processor.count_words(result_str)
        assert word_count == 1


# pytest.mark.xfail を使った期待される失敗のテスト
class TestExpectedFailures:
    """期待される失敗のテスト"""
    
    @pytest.mark.xfail(reason="この機能はまだ実装されていません")
    def test_unimplemented_feature(self):
        """未実装機能のテスト"""
        calc = Calculator()
        # まだ実装されていない機能
        result = calc.logarithm(10)  # このメソッドは存在しない
        assert result == 1
    
    @pytest.mark.xfail(condition=sys.platform == "win32", reason="Windowsでは既知の問題")
    def test_known_windows_issue(self):
        """Windows での既知の問題"""
        # Windows で失敗することが分かっているテスト
        assert False, "Windows では失敗します"


# まとめ用のマーカー確認テスト
class TestMarkerExamples:
    """マーカーの使用例確認"""
    
    def test_check_all_markers_work(self):
        """全てのマーカーが正常に動作することを確認"""
        # このテストは実際には何もマーカーが付いていない
        assert True
    
    @pytest.mark.unit
    def test_unit_marker(self):
        """unitマーカーのテスト"""
        assert True
    
    @pytest.mark.integration
    def test_integration_marker(self):
        """integrationマーカーのテスト"""
        assert True
    
    @pytest.mark.slow
    def test_slow_marker(self):
        """slowマーカーのテスト"""
        assert True
    
    @pytest.mark.unit
    @pytest.mark.math
    def test_multiple_markers(self):
        """複数マーカーのテスト"""
        assert True