"""
Level 4: Expert - カスタムプラグインとフック

このファイルでは pytest の最も高度な機能について学びます。
- カスタムプラグインの作成
- pytest フックの実装
- 動的テスト生成
- カスタムコレクション
- 高度なレポート生成

実行方法:
pytest examples/level4_expert/test_custom_plugins.py -v --tb=short
"""

import pytest
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import uuid


# テスト結果データ構造
@dataclass
class TestMetrics:
    """テスト実行メトリクス"""
    test_name: str
    start_time: float
    end_time: float
    duration: float
    status: str
    error_message: str = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SessionReport:
    """セッション全体のレポート"""
    session_id: str
    start_time: str
    end_time: str
    total_duration: float
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    test_metrics: List[TestMetrics]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# カスタムプラグインクラス
class TestMetricsPlugin:
    """テスト実行メトリクスを収集するプラグイン"""
    
    def __init__(self):
        self.test_metrics: List[TestMetrics] = []
        self.session_start_time = None
        self.session_id = str(uuid.uuid4())[:8]
        self.current_test_start = None
    
    def pytest_sessionstart(self, session):
        """セッション開始時のフック"""
        self.session_start_time = time.time()
        print(f"\n🚀 テストセッション開始 (ID: {self.session_id})")
    
    def pytest_sessionfinish(self, session, exitstatus):
        """セッション終了時のフック"""
        session_end_time = time.time()
        total_duration = session_end_time - self.session_start_time
        
        # 結果統計を計算
        passed = sum(1 for m in self.test_metrics if m.status == "PASSED")
        failed = sum(1 for m in self.test_metrics if m.status == "FAILED")
        skipped = sum(1 for m in self.test_metrics if m.status == "SKIPPED")
        
        # セッションレポートを作成
        report = SessionReport(
            session_id=self.session_id,
            start_time=datetime.fromtimestamp(self.session_start_time).isoformat(),
            end_time=datetime.fromtimestamp(session_end_time).isoformat(),
            total_duration=total_duration,
            total_tests=len(self.test_metrics),
            passed_tests=passed,
            failed_tests=failed,
            skipped_tests=skipped,
            test_metrics=self.test_metrics
        )
        
        # レポートをファイルに保存
        self._save_report(report)
        
        # サマリーを出力
        print(f"\n📊 テストセッション完了")
        print(f"   セッションID: {self.session_id}")
        print(f"   総実行時間: {total_duration:.2f}秒")
        print(f"   総テスト数: {len(self.test_metrics)}")
        print(f"   成功: {passed}, 失敗: {failed}, スキップ: {skipped}")
        
        if exitstatus == 0:
            print("   ✅ 全テスト正常終了")
        else:
            print("   ❌ テスト実行中にエラーが発生")
    
    def pytest_runtest_setup(self, item):
        """テスト実行前のフック"""
        self.current_test_start = time.time()
        print(f"\n⏳ テスト開始: {item.name}")
    
    def pytest_runtest_teardown(self, item, nextitem):
        """テスト実行後のフック"""
        if self.current_test_start:
            duration = time.time() - self.current_test_start
            print(f"⏱️  実行時間: {duration:.3f}秒")
    
    def pytest_runtest_logreport(self, report):
        """テスト結果レポートのフック"""
        if report.when == "call":  # テスト実行フェーズのみ処理
            end_time = time.time()
            duration = end_time - self.current_test_start if self.current_test_start else 0
            
            error_message = None
            if report.failed and report.longrepr:
                error_message = str(report.longrepr)
            
            metrics = TestMetrics(
                test_name=report.nodeid,
                start_time=self.current_test_start,
                end_time=end_time,
                duration=duration,
                status=report.outcome.upper(),
                error_message=error_message
            )
            
            self.test_metrics.append(metrics)
    
    def _save_report(self, report: SessionReport):
        """レポートをJSONファイルに保存"""
        report_dir = Path("test_reports")
        report_dir.mkdir(exist_ok=True)
        
        report_file = report_dir / f"test_report_{self.session_id}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 レポート保存: {report_file}")


class SlowTestPlugin:
    """遅いテストを検出・警告するプラグイン"""
    
    def __init__(self, threshold_seconds: float = 1.0):
        self.threshold = threshold_seconds
        self.slow_tests = []
    
    def pytest_runtest_logreport(self, report):
        """テスト結果を監視"""
        if report.when == "call" and report.duration > self.threshold:
            self.slow_tests.append({
                "test": report.nodeid,
                "duration": report.duration,
                "threshold": self.threshold
            })
    
    def pytest_sessionfinish(self, session, exitstatus):
        """セッション終了時に遅いテストを報告"""
        if self.slow_tests:
            print(f"\n🐌 遅いテスト検出 (>{self.threshold}秒):")
            for test in sorted(self.slow_tests, key=lambda x: x["duration"], reverse=True):
                print(f"   ⚠️  {test['test']}: {test['duration']:.2f}秒")


# カスタムマーカーとフィルター
class CustomMarkerPlugin:
    """カスタムマーカーを管理するプラグイン"""
    
    def pytest_configure(self, config):
        """設定フェーズでマーカーを登録"""
        config.addinivalue_line("markers", "performance: Performance-related tests")
        config.addinivalue_line("markers", "database: Database operation tests")
        config.addinivalue_line("markers", "api: API integration tests")
        config.addinivalue_line("markers", "critical: Business-critical functionality tests")
        config.addinivalue_line("markers", "experimental: Experimental feature tests")
    
    def pytest_collection_modifyitems(self, config, items):
        """テスト収集後にアイテムを修正"""
        # critical マーカーがついたテストを最初に実行
        critical_tests = [item for item in items if item.get_closest_marker("critical")]
        other_tests = [item for item in items if not item.get_closest_marker("critical")]
        
        # リストを再構成
        items[:] = critical_tests + other_tests
        
        # experimental マーカーがついたテストにxfailを自動追加
        for item in items:
            if item.get_closest_marker("experimental"):
                item.add_marker(pytest.mark.xfail(reason="実験的機能のため不安定"))


# 動的テスト生成
class DynamicTestPlugin:
    """動的にテストを生成するプラグイン"""
    
    def pytest_generate_tests(self, metafunc):
        """テスト関数にパラメータを動的に注入"""
        if "dynamic_data" in metafunc.fixturenames:
            # 実際のプロジェクトでは外部ファイルやAPIから取得
            test_data = [
                {"input": 1, "expected": 2},
                {"input": 5, "expected": 10},
                {"input": 10, "expected": 20},
            ]
            
            metafunc.parametrize("dynamic_data", test_data, ids=[
                f"input_{data['input']}" for data in test_data
            ])


# プラグインを登録
pytest_plugins = [
    TestMetricsPlugin(),
    SlowTestPlugin(threshold_seconds=0.1),  # 0.1秒以上を遅いとする
    CustomMarkerPlugin(),
    DynamicTestPlugin(),
]


# テスト対象のクラス
class ComplexCalculator:
    """複雑な計算を行う電卓クラス"""
    
    def fibonacci(self, n: int) -> int:
        """フィボナッチ数列の計算（再帰版）"""
        if n <= 1:
            return n
        return self.fibonacci(n - 1) + self.fibonacci(n - 2)
    
    def prime_factors(self, n: int) -> List[int]:
        """素因数分解"""
        factors = []
        d = 2
        while d * d <= n:
            while n % d == 0:
                factors.append(d)
                n //= d
            d += 1
        if n > 1:
            factors.append(n)
        return factors
    
    def matrix_multiply(self, a: List[List[int]], b: List[List[int]]) -> List[List[int]]:
        """行列の積（シンプル実装）"""
        rows_a, cols_a = len(a), len(a[0])
        rows_b, cols_b = len(b), len(b[0])
        
        if cols_a != rows_b:
            raise ValueError("行列の次元が合いません")
        
        result = [[0] * cols_b for _ in range(rows_a)]
        
        for i in range(rows_a):
            for j in range(cols_b):
                for k in range(cols_a):
                    result[i][j] += a[i][k] * b[k][j]
        
        return result


class DatabaseSimulator:
    """データベース操作のシミュレーター"""
    
    def __init__(self):
        self.data = {}
        self.connection_delay = 0.01  # 接続遅延をシミュレート
    
    def connect(self):
        """データベース接続をシミュレート"""
        time.sleep(self.connection_delay)
        return True
    
    def query(self, sql: str) -> List[Dict[str, Any]]:
        """クエリ実行をシミュレート"""
        self.connect()
        
        # シンプルなSQLパーサー（テスト用）
        if sql.lower().startswith("select"):
            return list(self.data.values())
        elif sql.lower().startswith("insert"):
            # INSERT INTO table (id, name) VALUES (1, 'test')
            # 超簡易パーサー
            return [{"status": "inserted"}]
        
        return []
    
    def insert(self, table: str, data: Dict[str, Any]):
        """データ挿入"""
        self.connect()
        key = f"{table}_{len(self.data)}"
        self.data[key] = data
        return key


# ここからテストコード

class TestBasicFunctionality:
    """基本機能のテスト"""
    
    @pytest.mark.critical
    def test_simple_addition(self):
        """重要な基本機能テスト（最初に実行される）"""
        calc = ComplexCalculator()
        # この例では実際には何もしないが、criticalマーカーのテスト
        assert 1 + 1 == 2
    
    @pytest.mark.performance
    def test_fibonacci_calculation(self):
        """フィボナッチ数列計算のテスト"""
        calc = ComplexCalculator()
        
        # 小さな値での計算
        assert calc.fibonacci(0) == 0
        assert calc.fibonacci(1) == 1
        assert calc.fibonacci(5) == 5
        assert calc.fibonacci(10) == 55
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_large_fibonacci(self):
        """大きなフィボナッチ数列（遅いテスト）"""
        calc = ComplexCalculator()
        
        # このテストは意図的に遅く、SlowTestPluginで検出される
        result = calc.fibonacci(25)
        assert result == 75025
    
    @pytest.mark.database
    def test_database_operations(self):
        """データベース操作のテスト"""
        db = DatabaseSimulator()
        
        # 接続テスト
        assert db.connect() == True
        
        # データ挿入
        key = db.insert("users", {"name": "テストユーザー", "age": 30})
        assert key is not None
        
        # クエリ実行
        results = db.query("SELECT * FROM users")
        assert len(results) > 0
    
    @pytest.mark.api
    @pytest.mark.experimental
    def test_experimental_feature(self):
        """実験的機能のテスト（xfailが自動追加される）"""
        # 実験的機能なので不安定
        calc = ComplexCalculator()
        
        # この機能はまだ完全ではないため、失敗する可能性がある
        # CustomMarkerPluginによってxfailが自動的に追加される
        result = calc.prime_factors(100)
        assert result == [2, 2, 5, 5]  # これは正しい結果


class TestDynamicGeneration:
    """動的生成テストのテスト"""
    
    def test_dynamic_calculation(self, dynamic_data):
        """動的に生成されたテストデータを使用"""
        # dynamic_data は DynamicTestPlugin によって注入される
        input_value = dynamic_data["input"]
        expected = dynamic_data["expected"]
        
        # 簡単な計算（入力を2倍する）
        result = input_value * 2
        assert result == expected


class TestMatrixOperations:
    """行列演算のテスト"""
    
    @pytest.mark.performance
    def test_matrix_multiplication(self):
        """行列の積のテスト"""
        calc = ComplexCalculator()
        
        # 2x2 行列の積
        a = [[1, 2], [3, 4]]
        b = [[5, 6], [7, 8]]
        
        result = calc.matrix_multiply(a, b)
        expected = [[19, 22], [43, 50]]
        
        assert result == expected
    
    @pytest.mark.performance
    def test_matrix_multiplication_invalid_dimensions(self):
        """行列の次元不整合エラーテスト"""
        calc = ComplexCalculator()
        
        a = [[1, 2]]  # 1x2
        b = [[1], [2], [3]]  # 3x1 (次元が合わない)
        
        with pytest.raises(ValueError) as exc_info:
            calc.matrix_multiply(a, b)
        
        assert "次元が合いません" in str(exc_info.value)


# カスタムフィクスチャでプラグインテスト
@pytest.fixture
def metrics_plugin():
    """メトリクスプラグインインスタンスを取得"""
    # 実際のプラグインインスタンスを取得
    for plugin in pytest_plugins:
        if isinstance(plugin, TestMetricsPlugin):
            return plugin
    return None


class TestPluginFunctionality:
    """プラグイン機能自体のテスト"""
    
    def test_metrics_collection(self, metrics_plugin):
        """メトリクス収集機能のテスト"""
        if metrics_plugin:
            # テスト開始前の状態を確認
            initial_count = len(metrics_plugin.test_metrics)
            
            # このテスト自体もメトリクスに追加されることを想定
            assert metrics_plugin.session_id is not None
            assert len(metrics_plugin.session_id) == 8  # UUID の最初の8文字
    
    def test_slow_test_simulation(self):
        """遅いテストのシミュレーション"""
        # 意図的に少し待つ（SlowTestPluginでキャッチされる）
        time.sleep(0.15)  # 0.15秒待つ（閾値0.1秒を超える）
        
        assert True  # テストは成功


class TestComplexScenarios:
    """複雑なシナリオのテスト"""
    
    @pytest.mark.critical
    @pytest.mark.database
    @pytest.mark.performance
    def test_complex_database_scenario(self):
        """複雑なデータベースシナリオ"""
        db = DatabaseSimulator()
        calc = ComplexCalculator()
        
        # 複数のデータを挿入
        users = [
            {"name": "ユーザー1", "age": 25},
            {"name": "ユーザー2", "age": 30},
            {"name": "ユーザー3", "age": 35},
        ]
        
        keys = []
        for user in users:
            key = db.insert("users", user)
            keys.append(key)
        
        # データが正しく挿入されたことを確認
        assert len(keys) == 3
        
        # クエリでデータを取得
        results = db.query("SELECT * FROM users")
        assert len(results) == 3
        
        # 各ユーザーの年齢の合計を計算
        total_age = sum(user["age"] for user in users)
        assert total_age == 90
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_comprehensive_calculation_suite(self):
        """包括的な計算スイート（時間のかかるテスト）"""
        calc = ComplexCalculator()
        
        # 複数の計算を組み合わせ
        fib_results = [calc.fibonacci(i) for i in range(15)]
        assert len(fib_results) == 15
        assert fib_results[-1] == 377  # fib(14) = 377
        
        # 素因数分解
        prime_factors = calc.prime_factors(60)
        assert prime_factors == [2, 2, 3, 5]
        
        # 行列計算
        matrix_a = [[1, 2, 3], [4, 5, 6]]
        matrix_b = [[7, 8], [9, 10], [11, 12]]
        result = calc.matrix_multiply(matrix_a, matrix_b)
        
        expected = [[58, 64], [139, 154]]
        assert result == expected


# エラーハンドリングテスト
class TestErrorHandling:
    """エラーハンドリングのテスト"""
    
    @pytest.mark.critical
    def test_fibonacci_negative_input(self):
        """フィボナッチ数列の負数入力テスト"""
        calc = ComplexCalculator()
        
        # 負数でも実行されるが、結果は定義により0または負数
        result = calc.fibonacci(-1)
        assert result == -1
    
    @pytest.mark.database
    def test_database_connection_failure_simulation(self):
        """データベース接続失敗のシミュレーション"""
        db = DatabaseSimulator()
        
        # 接続遅延を増やして問題をシミュレート
        db.connection_delay = 0.05
        
        # それでも接続は成功するはず
        assert db.connect() == True


# テスト完了後のクリーンアップ
def pytest_sessionfinish(session, exitstatus):
    """セッション終了後の追加処理"""
    print(f"\n🧹 カスタムクリーンアップ実行")
    print(f"   終了ステータス: {exitstatus}")
    
    # テストレポートディレクトリを確認
    report_dir = Path("test_reports")
    if report_dir.exists():
        report_files = list(report_dir.glob("*.json"))
        print(f"   生成されたレポート: {len(report_files)} 件")
        for report_file in report_files:
            print(f"     - {report_file}")


# このファイル用の設定
def pytest_configure(config):
    """このファイル専用の設定"""
    # テストレポートディレクトリを作成
    Path("test_reports").mkdir(exist_ok=True)
    
    print("🔧 カスタムプラグインテスト設定完了")