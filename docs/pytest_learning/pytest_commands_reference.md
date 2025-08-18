# pytest コマンドリファレンス 📖

## 📋 このリファレンスについて

実際のRAGシステムプロジェクトで使用したpytestコマンドを基に、よく使うコマンドから高度な使い方まで体系的にまとめました。FastAPIのAPIエンドポイントテストコマンドも含む、開発現場ですぐに活用できる実践的なリファレンスです。

**新機能**: APIテスト専用のコマンドパターンとマーカー使用例を追加

---

## 🚀 基本実行コマンド

### 1. 基本テスト実行

```bash
# 全テスト実行
pytest

# カレントディレクトリの全テスト実行
pytest .

# 特定ディレクトリのテスト実行
pytest tests/

# uvを使用した実行（推奨）
uv run pytest
```

**用途**: 開発完了時の最終確認、CI/CDでの全テスト実行

### 2. 詳細出力コマンド

```bash
# 詳細出力（テスト名表示）
pytest -v
pytest --verbose

# 非常に詳細な出力
pytest -vv

# 簡潔な出力（結果のみ）
pytest -q
pytest --quiet

# print文やログを表示
pytest -s
pytest --capture=no
```

**実行例とその効果:**
```bash
# 基本実行の場合
$ pytest
================= test session starts =================
collected 92 items

........................................ [ 42%]
........................................................ [ 87%]
...........                                          [100%]

================= 92 passed in 1.45s =================

# 詳細出力の場合
$ pytest -v
================= test session starts =================
collected 92 items

tests/unit/test_ai_generator_basic.py::TestAIGeneratorBasic::test_generate_response_without_tools PASSED [ 1%]
tests/unit/test_ai_generator_basic.py::TestAIGeneratorBasic::test_conversation_history PASSED [ 2%]
tests/unit/test_ai_generator_tools.py::TestAIGeneratorTools::test_tool_execution PASSED [ 3%]
...
```

---

## 🎯 特定テスト実行コマンド

### 3. ファイル・ディレクトリ指定

```bash
# 特定ファイル実行
pytest tests/unit/test_ai_generator_basic.py

# 複数ファイル実行
pytest tests/unit/test_ai_generator_basic.py tests/unit/test_vector_store.py

# 特定ディレクトリ実行
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

**用途**: 開発中の該当機能のテストのみ実行、デバッグ時の問題箇所特定

### 4. クラス・メソッド指定

```bash
# 特定テストクラス実行
pytest tests/unit/test_ai_generator_basic.py::TestAIGeneratorBasic

# 特定テストメソッド実行
pytest tests/unit/test_ai_generator_basic.py::TestAIGeneratorBasic::test_generate_response_without_tools

# パターンマッチング
pytest -k "test_generate_response"
pytest -k "ai_generator and basic"
pytest -k "not slow"
```

**実行例:**
```bash
# 特定メソッドのみ実行
$ pytest tests/unit/test_ai_generator_basic.py::TestAIGeneratorBasic::test_generate_response_without_tools -v
================= test session starts =================
collected 1 item

tests/unit/test_ai_generator_basic.py::TestAIGeneratorBasic::test_generate_response_without_tools PASSED [100%]

================= 1 passed in 0.02s =================
```

---

## 🏷️ マーカー使用コマンド

### 5. マーカー指定実行

```bash
# 単体テストのみ実行
pytest -m unit

# 統合テストのみ実行
pytest -m integration

# E2Eテストのみ実行
pytest -m e2e

# 遅いテストを除外
pytest -m "not slow"

# APIテストを除外（オフライン環境）
pytest -m "not api"
```

### 6. 複合マーカー条件

```bash
# AND条件: 単体テストかつ遅くないもの
pytest -m "unit and not slow"

# OR条件: 統合テストまたはE2Eテスト
pytest -m "integration or e2e"

# 複雑な条件: 単体テストまたは（統合テストかつ遅くないもの）
pytest -m "unit or (integration and not slow)"

# 利用可能なマーカー一覧表示
pytest --markers
```

**実際のプロジェクトでの使用例:**
```bash
# 開発中（高速テストのみ）
pytest -m "not slow" -q

# プルリクエスト前（単体+統合）
pytest -m "unit or integration" -v

# リリース前（全テスト）
pytest -m "unit or integration or e2e" --tb=short
```

---

## 🌐 APIテスト専用コマンド

### 17. FastAPI エンドポイントテスト

```bash
# API テストのみ実行
pytest tests/api/ -v

# 特定のAPIエンドポイントテスト
pytest tests/api/test_app.py::TestQueryEndpoint -v

# APIテストマーカー使用
pytest -m api -v --tb=short

# API統合テスト
pytest -m "api and integration" -v

# API テスト高速実行（遅いテスト除外）
pytest -m "api and not slow" -q

# APIエラーハンドリングのみテスト
pytest tests/api/ -k "error" -v
```

### 18. APIテストのデバッグ

```bash
# API テストでprint文表示
pytest tests/api/test_app.py -s -v

# 特定のAPIテストをデバッグモードで実行
pytest tests/api/test_app.py::test_query_endpoint -vv -s --pdb

# APIレスポンスの詳細を確認
pytest tests/api/ -vv --tb=long

# APIテスト実行時間測定
pytest tests/api/ --durations=5
```

### 19. APIテスト環境別実行

```bash
# 開発環境でのAPIテスト（高速）
pytest -m "api and not slow" --tb=short -q

# テスト環境での包括的APIチェック
pytest tests/api/ -v --tb=line --maxfail=3

# CI/CD環境でのAPIテスト
pytest -m api --tb=short --junitxml=api-results.xml

# APIカバレッジ測定
pytest tests/api/ --cov=src --cov-report=html
```

### 20. APIテストのパフォーマンス測定

```bash
# API テストの実行時間分析
pytest tests/api/ --durations=10 -v

# 並列でのAPIテスト実行
pytest tests/api/ -n auto

# メモリ使用量を抑制したAPIテスト
pytest tests/api/ --forked

# APIテスト結果のHTML報告
pytest tests/api/ --html=api-report.html --self-contained-html
```

---

## 🛠️ エラー処理・デバッグコマンド

### 7. トレースバック制御

```bash
# 短縮トレースバック（デフォルト）
pytest --tb=short

# 1行でエラー表示
pytest --tb=line

# 詳細なトレースバック
pytest --tb=long

# トレースバック非表示
pytest --tb=no

# 最初と最後の行のみ表示
pytest --tb=auto
```

**トレースバック形式の比較:**
```bash
# --tb=line の場合
FAILED tests/unit/test_ai_generator.py::test_example - assert 5 == 6

# --tb=short の場合
def test_example():
>       assert add(2, 3) == 6
E       assert 5 == 6
E        +  where 5 = add(2, 3)

# --tb=long の場合
def test_example():
    def add(a, b):
        return a + b
    
>       assert add(2, 3) == 6
E       assert 5 == 6
E        +  where 5 = add(2, 3)

test_file.py:10: AssertionError
```

### 8. 失敗時停止制御

```bash
# 最初の失敗で停止
pytest -x
pytest --exitfirst

# N回失敗したら停止
pytest --maxfail=1
pytest --maxfail=3
pytest --maxfail=5

# 失敗したテストでpdbデバッガを起動
pytest --pdb

# pdbトレースオプション
pytest --pdb-trace
```

**開発段階別の使い分け:**
```bash
# 開発初期（すぐに問題を見つけたい）
pytest -x --tb=short

# 開発中期（複数の問題を一度に確認）
pytest --maxfail=3 --tb=line

# 完成間近（全体の状況を把握）
pytest --tb=no -q
```

---

## 📊 情報表示・収集コマンド

### 9. テスト収集・情報表示

```bash
# テスト収集のみ（実行しない）
pytest --collect-only
pytest --co

# 収集結果を簡潔に表示
pytest --co -q

# テスト数をカウント
pytest --co -q | wc -l

# 実行時間測定
pytest --durations=0          # 全テストの実行時間
pytest --durations=10         # 最も遅い10個のテスト
pytest --durations-min=1.0    # 1秒以上のテストのみ表示
```

**実行例:**
```bash
# テスト収集結果
$ pytest --co -q
tests/unit/test_ai_generator_basic.py::TestAIGeneratorBasic::test_generate_response_without_tools
tests/unit/test_ai_generator_basic.py::TestAIGeneratorBasic::test_conversation_history
tests/integration/test_rag_system.py::TestRAGSystem::test_query_processing
...

92 tests collected

# 実行時間表示
$ pytest --durations=5
================= slowest 5 durations =================
15.23s call     tests/integration/test_rag_system.py::test_end_to_end
12.45s call     tests/e2e/test_live_system.py::test_real_api
8.76s call      tests/integration/test_vector_search.py::test_large_dataset
3.21s call      tests/unit/test_ai_generator.py::test_complex_scenario
1.98s call      tests/integration/test_database.py::test_migration
```

### 10. 設定・環境情報

```bash
# pytest設定情報表示
pytest --help

# 利用可能なfixture一覧
pytest --fixtures

# 特定テストで使用可能なfixture
pytest --fixtures tests/unit/test_ai_generator.py

# プラグイン一覧
pytest --trace-config

# 設定ファイルの場所確認
pytest --collect-only --quiet | head -1
```

---

## 🔧 実行制御・最適化コマンド

### 11. 並列実行（pytest-xdist）

```bash
# 自動並列実行（CPUコア数に応じて）
pytest -n auto

# 指定プロセス数で並列実行
pytest -n 4

# 分散実行（複数マシン）
pytest -d --tx ssh=user@host1 --tx ssh=user@host2
```

### 12. キャッシュ・再実行制御

```bash
# 前回失敗したテストのみ実行
pytest --lf
pytest --last-failed

# 前回失敗したテストを最初に実行
pytest --ff
pytest --failed-first

# キャッシュクリア
pytest --cache-clear

# キャッシュ情報表示
pytest --cache-show
```

**効率的な開発ワークフロー:**
```bash
# 1. 開発中: 関連テストのみ高速実行
pytest tests/unit/test_new_feature.py -v

# 2. 失敗修正後: 失敗したテストを再実行
pytest --lf -v

# 3. 最終確認: 全テスト実行
pytest --tb=short
```

---

## 📈 カバレッジ・レポート生成

### 13. カバレッジ測定（pytest-cov）

```bash
# 基本カバレッジ測定
pytest --cov=src

# HTMLレポート生成
pytest --cov=src --cov-report=html

# ターミナルに詳細表示
pytest --cov=src --cov-report=term-missing

# 複数形式のレポート
pytest --cov=src --cov-report=html --cov-report=term --cov-report=xml

# カバレッジ閾値設定
pytest --cov=src --cov-fail-under=80
```

### 14. レポート出力（pytest-html）

```bash
# HTMLレポート生成
pytest --html=report.html

# 自己完結型HTMLレポート
pytest --html=report.html --self-contained-html

# JUnitXMLレポート（CI/CD用）
pytest --junitxml=test-results.xml
```

---

## 🎨 カスタム実行パターン

### 15. 環境別実行

```bash
# 開発環境での実行
pytest -m "not slow and not api" -v --tb=short

# テスト環境での実行
pytest -m "unit or integration" --tb=line --maxfail=5

# 本番環境検証
pytest -m e2e --tb=short --durations=10

# CI/CD環境での実行
pytest --tb=short --junitxml=results.xml --cov=src --cov-report=xml
```

### 16. 段階的実行スクリプト

```bash
#!/bin/bash
# scripts/test_pipeline.sh

echo "🧪 単体テスト実行..."
if ! pytest tests/unit/ -q --tb=line; then
    echo "❌ 単体テストが失敗しました"
    exit 1
fi

echo "🔗 統合テスト実行..."
if ! pytest tests/integration/ -q --tb=line --maxfail=3; then
    echo "❌ 統合テストが失敗しました"
    exit 1
fi

echo "🚀 E2Eテスト実行..."
if ! pytest tests/e2e/ -q --tb=line; then
    echo "❌ E2Eテストが失敗しました"
    exit 1
fi

echo "✅ 全テストが成功しました！"
```

---

## 💡 実践的なコマンド組み合わせ

### 開発段階別おすすめコマンド

**🔥 開発初期（TDD）**
```bash
# 高速フィードバック重視
pytest tests/unit/test_new_feature.py -v -x --tb=short
```

**🚀 開発中（機能追加）**
```bash
# 関連テスト実行
pytest -k "new_feature" -v --tb=line --maxfail=3
```

**🔍 デバッグ時**
```bash
# 詳細情報で特定テスト実行
pytest tests/unit/test_broken.py::test_specific -vv -s --tb=long --pdb
```

**✅ プルリクエスト前**
```bash
# 包括的チェック
pytest tests/unit/ tests/integration/ -v --tb=short --cov=src --cov-report=term-missing
```

**🚢 リリース前**
```bash
# 全テスト実行（レポート付き）
pytest --tb=short --html=test-report.html --cov=src --cov-report=html --durations=10
```

### よく使うエイリアス設定

```bash
# ~/.bashrc または ~/.zshrc に追加
alias pt="pytest"
alias ptu="pytest tests/unit/ -v"
alias pti="pytest tests/integration/ -v" 
alias pte="pytest tests/e2e/ -v"
alias pta="pytest tests/api/ -v"        # API テスト用
alias ptf="pytest --lf -v"
alias ptq="pytest -q --tb=line"
alias ptc="pytest --cov=src --cov-report=term-missing"
alias ptapi="pytest -m api -v"          # APIマーカー用
alias ptfast="pytest -m 'not slow' -q"  # 高速テスト用
```

---

## 🛡️ トラブルシューティング

### よくあるエラーと対処法

**1. テストが見つからない**
```bash
# 問題の確認
pytest --collect-only

# 原因と対処法
# - ファイル名がtest_*.pyでない → リネーム
# - 関数名がtest_*でない → リネーム  
# - __init__.pyがない → 作成
```

**2. インポートエラー**
```bash
# PYTHONPATH設定
PYTHONPATH=. pytest

# または conftest.py でパス追加
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

**3. 遅いテスト実行**
```bash
# 問題の特定
pytest --durations=0

# 対処法
pytest -n auto           # 並列実行
pytest -m "not slow"     # 遅いテストをスキップ
pytest --lf              # 失敗テストのみ再実行
```

**4. メモリ不足**
```bash
# メモリ使用量を抑制
pytest --forked          # 各テストを独立プロセスで実行
pytest -n 2              # 並列数を制限
```

---

## 📚 参考情報

### 設定ファイル例

**pytest.ini**
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
markers =
    unit: Unit tests for individual components
    integration: Integration tests across multiple components
    e2e: End-to-end tests with real components  
    slow: Tests that take longer to run
    api: API endpoint tests (FastAPI/Web)
    external_api: Tests that require external API access
```

### 必須プラグイン

```bash
# カバレッジ測定
pip install pytest-cov

# 並列実行
pip install pytest-xdist

# HTMLレポート
pip install pytest-html

# モック拡張
pip install pytest-mock

# ベンチマーク
pip install pytest-benchmark
```

---

## 🎯 まとめ

このリファレンスで紹介したコマンドを使い分けることで、効率的なテスト実行とデバッグが可能になります。

**覚えておくべき基本パターン:**
1. **開発中**: `pytest -m "not slow" -v`
2. **APIテスト**: `pytest -m api -v --tb=short`
3. **デバッグ**: `pytest path/to/test.py::test_name -vv -s --pdb`
4. **CI/CD**: `pytest --tb=short --junitxml=results.xml`
5. **カバレッジ**: `pytest --cov=src --cov-report=html`

継続的な使用を通じて、自分の開発スタイルに最適なコマンド組み合わせを見つけてください。

Happy Testing! 🚀