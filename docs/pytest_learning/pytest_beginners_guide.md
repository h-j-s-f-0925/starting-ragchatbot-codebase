# pytest完全初心者ガイド 🚀

## 📋 このガイドについて

このガイドは、Pythonのテストフレームワーク「pytest」を全く触ったことがない方でも、実際のプロジェクトでテストを書けるようになることを目標としています。

実際のRAGシステム開発プロジェクトでの経験を基に、理論だけでなく実践的なスキルを段階的に学習できる構成になっています。

## 🎯 学習目標

このガイドを完了すると、以下のことができるようになります：

- ✅ pytestの基本概念と使い方を理解する
- ✅ 実際のプロジェクトでテストコードを書ける
- ✅ fixture、モック、パラメータ化テストを活用できる
- ✅ チーム開発で通用するテスト構造を設計できる
- ✅ CI/CDでテストを自動実行できる

## 📖 学習の進め方

### 推奨学習時間
- **レベル1**: 2-3時間（基礎理解）
- **レベル2**: 4-5時間（実践基礎）
- **レベル3**: 6-8時間（プロジェクト実践）
- **レベル4**: 3-4時間（上級技法）

### 必要な前提知識
- Python基礎文法（関数、クラス、インポート）
- 基本的なコマンドライン操作
- 簡単なプログラミング経験

---

# レベル1: pytest基礎編 🌱

## 1.1 pytestとは何か？

### なぜテストが必要なのか？

想像してください。あなたが作った計算機アプリがあります：

```python
def calculate_total(price, tax_rate):
    """価格と税率から合計金額を計算"""
    return price + (price * tax_rate)
```

この関数、本当に正しく動きますか？

```python
# 手動でチェック
print(calculate_total(100, 0.1))  # 110.0が期待される
print(calculate_total(0, 0.1))    # 0.0が期待される
print(calculate_total(100, 0))    # 100.0が期待される
```

でも、毎回手動チェックは面倒ですよね。そこで**自動テスト**の出番です！

### pytestの特徴

```python
# test_calculator.py
def test_calculate_total():
    """calculate_total関数のテスト"""
    assert calculate_total(100, 0.1) == 110.0
    assert calculate_total(0, 0.1) == 0.0
    assert calculate_total(100, 0) == 100.0
```

```bash
# テスト実行
pytest test_calculator.py
```

**pytestの魅力：**
- 🎯 **シンプル**: `assert`文だけでテストが書ける
- 🚀 **高機能**: 豊富な機能と拡張性
- 🔍 **詳細な情報**: 失敗時に原因が分かりやすい
- 🌍 **人気**: Pythonで最も使われているテストフレームワーク

## 1.2 環境セットアップ

### インストール

```bash
# pip使用の場合
pip install pytest

# uvを使用の場合（推奨）
uv add pytest

# conda使用の場合
conda install pytest
```

### 最初のテスト作成

**ステップ1: テスト対象の関数を作成**

```python
# calculator.py
def add(a, b):
    """二つの数を足す"""
    return a + b

def subtract(a, b):
    """二つの数を引く"""
    return a - b

def multiply(a, b):
    """二つの数を掛ける"""
    return a * b

def divide(a, b):
    """二つの数を割る"""
    if b == 0:
        raise ValueError("ゼロで割ることはできません")
    return a / b
```

**ステップ2: テストファイルを作成**

```python
# test_calculator.py
from calculator import add, subtract, multiply, divide
import pytest

def test_add():
    """足し算のテスト"""
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

def test_subtract():
    """引き算のテスト"""
    assert subtract(5, 3) == 2
    assert subtract(0, 0) == 0
    assert subtract(-1, -1) == 0

def test_multiply():
    """掛け算のテスト"""
    assert multiply(3, 4) == 12
    assert multiply(0, 5) == 0
    assert multiply(-2, 3) == -6

def test_divide():
    """割り算のテスト"""
    assert divide(6, 2) == 3
    assert divide(5, 2) == 2.5
    
def test_divide_by_zero():
    """ゼロ除算エラーのテスト"""
    with pytest.raises(ValueError):
        divide(5, 0)
```

**ステップ3: テスト実行**

```bash
# 基本実行
pytest test_calculator.py

# 詳細出力
pytest test_calculator.py -v

# さらに詳細
pytest test_calculator.py -vv
```

### 実行結果の読み方

```
=================== test session starts ===================
platform linux -- Python 3.11.0, pytest-7.4.0, pluggy-1.3.0
cachedir: .pytest_cache
rootdir: /path/to/project
collected 5 items

test_calculator.py::test_add PASSED                   [ 20%]
test_calculator.py::test_subtract PASSED              [ 40%]
test_calculator.py::test_multiply PASSED              [ 60%]
test_calculator.py::test_divide PASSED                [ 80%]
test_calculator.py::test_divide_by_zero PASSED        [100%]

=================== 5 passed in 0.02s ===================
```

**読み方：**
- `collected 5 items`: 5個のテストが見つかった
- `PASSED`: テストが成功
- `[ 20%]`: 進捗状況
- `5 passed in 0.02s`: 5個成功、0.02秒で完了

## 1.3 基本コマンドマスター

### よく使うコマンド

```bash
# 1. 全テスト実行
pytest

# 2. 特定ファイル実行
pytest test_calculator.py

# 3. 詳細出力
pytest -v

# 4. 失敗時に詳細情報表示
pytest -v --tb=short

# 5. 最初の失敗で停止
pytest -x

# 6. print文を表示
pytest -s
```

### エラー時の対処法

**失敗例を見てみましょう：**

```python
def test_add_wrong():
    """わざと失敗させる例"""
    assert add(2, 3) == 6  # 実際は5だが6を期待
```

**実行結果：**
```
FAILED test_calculator.py::test_add_wrong - assert 5 == 6
```

**詳細表示（`-v`オプション）：**
```
def test_add_wrong():
>       assert add(2, 3) == 6
E       assert 5 == 6
E        +  where 5 = add(2, 3)

test_calculator.py:XX: AssertionError
```

**対処法：**
1. `assert`文を確認
2. 期待値が正しいかチェック
3. 関数の実装を確認

## 1.4 基本的なテスト設定

### pytest.ini ファイル

```ini
[tool:pytest]
# テストファイルのパス指定
testpaths = tests

# テストファイルの命名規則
python_files = test_*.py

# テストクラスの命名規則
python_classes = Test*

# テスト関数の命名規則
python_functions = test_*

# 常に使用するオプション
addopts = 
    -v
    --tb=short
    --strict-markers

# 警告フィルター
filterwarnings =
    ignore::DeprecationWarning
```

### ディレクトリ構造

```
my_project/
├── src/
│   ├── calculator.py
│   └── __init__.py
├── tests/
│   ├── test_calculator.py
│   └── __init__.py
├── pytest.ini
└── README.md
```

---

# レベル2: 実践基礎編 🛠️

## 2.1 fixtureの魔法

### fixtureとは？

テストで同じデータを何度も使いたい時、毎回作るのは面倒ですよね？

```python
# 面倒なパターン
def test_user_creation():
    user_data = {"name": "田中", "age": 25, "email": "tanaka@example.com"}
    user = create_user(user_data)
    assert user.name == "田中"

def test_user_update():
    user_data = {"name": "田中", "age": 25, "email": "tanaka@example.com"}
    user = create_user(user_data)
    user.update_age(26)
    assert user.age == 26
```

fixtureを使うと：

```python
# fixture使用パターン
import pytest

@pytest.fixture
def user_data():
    """テスト用ユーザーデータ"""
    return {"name": "田中", "age": 25, "email": "tanaka@example.com"}

@pytest.fixture
def sample_user(user_data):
    """テスト用ユーザーオブジェクト"""
    return create_user(user_data)

def test_user_creation(sample_user):
    assert sample_user.name == "田中"

def test_user_update(sample_user):
    sample_user.update_age(26)
    assert sample_user.age == 26
```

### conftest.py - 共通fixture

複数のテストファイルで同じfixtureを使いたい場合：

```python
# tests/conftest.py
import pytest
from datetime import datetime

@pytest.fixture
def current_time():
    """現在時刻のfixture"""
    return datetime.now()

@pytest.fixture
def test_config():
    """テスト用設定"""
    return {
        "database_url": "sqlite:///:memory:",
        "debug": True,
        "test_mode": True
    }

@pytest.fixture
def sample_users():
    """テスト用ユーザーリスト"""
    return [
        {"name": "田中", "age": 25},
        {"name": "佐藤", "age": 30},
        {"name": "鈴木", "age": 28},
    ]
```

```python
# tests/test_users.py
def test_user_count(sample_users):
    """ユーザー数のテスト"""
    assert len(sample_users) == 3

def test_config_loading(test_config):
    """設定読み込みのテスト"""
    assert test_config["test_mode"] is True
```

### fixtureのスコープ

```python
@pytest.fixture(scope="function")  # デフォルト: 各テスト関数で新しく作成
def function_scope():
    print("関数ごとに実行")
    return "function_data"

@pytest.fixture(scope="class")     # クラス内で1回だけ作成
def class_scope():
    print("クラスごとに実行")
    return "class_data"

@pytest.fixture(scope="module")    # モジュール内で1回だけ作成
def module_scope():
    print("モジュールごとに実行")
    return "module_data"

@pytest.fixture(scope="session")   # セッション全体で1回だけ作成
def session_scope():
    print("セッションごとに実行")
    return "session_data"
```

## 2.2 モッキング入門

### なぜモックが必要？

実際の開発では、外部サービスに依存するコードがよくあります：

```python
import requests

class WeatherService:
    def get_temperature(self, city):
        """都市の気温を取得"""
        response = requests.get(f"https://api.weather.com/{city}")
        return response.json()["temperature"]

def should_wear_coat(city):
    """コートを着るべきかを判定"""
    weather = WeatherService()
    temp = weather.get_temperature(city)
    return temp < 15
```

このコードをテストするとき：
- 🚫 実際のAPIを呼ぶと遅い
- 🚫 ネットワークエラーでテストが失敗する
- 🚫 APIの制限に引っかかる

### モックを使った解決

```python
# test_weather.py
import pytest
from unittest.mock import Mock, patch
from weather import WeatherService, should_wear_coat

def test_should_wear_coat_cold():
    """寒い時はコートを着るべき"""
    # WeatherServiceをモック化
    with patch('weather.WeatherService') as mock_service:
        # モックの戻り値を設定
        mock_instance = mock_service.return_value
        mock_instance.get_temperature.return_value = 10
        
        # テスト実行
        result = should_wear_coat("東京")
        
        # 検証
        assert result is True
        mock_instance.get_temperature.assert_called_once_with("東京")

def test_should_wear_coat_warm():
    """暖かい時はコートは不要"""
    with patch('weather.WeatherService') as mock_service:
        mock_instance = mock_service.return_value
        mock_instance.get_temperature.return_value = 20
        
        result = should_wear_coat("沖縄")
        
        assert result is False
        mock_instance.get_temperature.assert_called_once_with("沖縄")
```

### より簡単なfixtureでのモック

```python
# conftest.py
@pytest.fixture
def mock_weather_service():
    """天気サービスのモック"""
    with patch('weather.WeatherService') as mock:
        yield mock.return_value

# test_weather.py
def test_with_fixture(mock_weather_service):
    """fixtureを使ったモックテスト"""
    mock_weather_service.get_temperature.return_value = 5
    
    result = should_wear_coat("札幌")
    assert result is True
```

## 2.3 パラメータ化テスト

### 同じテストロジックで複数のケース

```python
@pytest.mark.parametrize("a, b, expected", [
    (2, 3, 5),
    (0, 0, 0),
    (-1, 1, 0),
    (10, -5, 5),
])
def test_add_multiple_cases(a, b, expected):
    """複数ケースの足し算テスト"""
    assert add(a, b) == expected
```

### 複雑なケース

```python
@pytest.mark.parametrize("city, temp, expected_coat", [
    ("東京", 10, True),   # 寒い -> コート必要
    ("大阪", 20, False),  # 暖かい -> コート不要
    ("札幌", 5, True),    # 非常に寒い -> コート必要
    ("沖縄", 25, False),  # 暑い -> コート不要
])
def test_coat_decision(city, temp, expected_coat, mock_weather_service):
    """都市別コート判定テスト"""
    mock_weather_service.get_temperature.return_value = temp
    
    result = should_wear_coat(city)
    assert result == expected_coat
```

### IDを使った読みやすいテスト

```python
@pytest.mark.parametrize("input_data, expected", [
    ({"name": "田中", "age": 25}, True),
    ({"name": "", "age": 25}, False),
    ({"name": "佐藤", "age": -1}, False),
], ids=["valid_user", "empty_name", "invalid_age"])
def test_user_validation(input_data, expected):
    """ユーザーデータ検証テスト"""
    result = validate_user(input_data)
    assert result == expected
```

---

# レベル3: プロジェクト実践編 🏗️

## 3.1 テスト構造の設計

### 実際のプロジェクト構造例

```
rag_project/
├── src/
│   ├── ai_generator.py      # AI応答生成
│   ├── vector_store.py      # ベクター検索
│   ├── rag_system.py        # RAGシステム統合
│   └── config.py            # 設定
├── tests/
│   ├── conftest.py          # 共通fixture
│   ├── unit/                # 単体テスト
│   │   ├── test_ai_generator_basic.py
│   │   ├── test_ai_generator_tools.py
│   │   ├── test_vector_store.py
│   │   └── test_config.py
│   ├── integration/         # 統合テスト
│   │   ├── test_rag_system.py
│   │   └── test_api_integration.py
│   └── e2e/                 # E2Eテスト
│       └── test_live_system.py
├── pytest.ini
└── requirements.txt
```

### テストタイプの使い分け

**Unit Tests（単体テスト）**
```python
# tests/unit/test_ai_generator_basic.py
@pytest.mark.unit
class TestAIGeneratorBasic:
    """AIジェネレーターの基本機能テスト"""
    
    def test_response_generation(self, mock_anthropic_client):
        """応答生成の基本テスト"""
        # 単一のクラス・メソッドをテスト
        # 外部依存は全てモック化
        pass
```

**Integration Tests（統合テスト）**
```python
# tests/integration/test_rag_system.py
@pytest.mark.integration
class TestRAGSystem:
    """RAGシステム統合テスト"""
    
    def test_end_to_end_query(self, rag_system):
        """複数コンポーネント連携テスト"""
        # 複数のクラスの協調動作をテスト
        # 一部の外部依存は実際のものを使用
        pass
```

**E2E Tests（エンドツーエンドテスト）**
```python
# tests/e2e/test_live_system.py
@pytest.mark.e2e
@pytest.mark.slow
class TestLiveSystem:
    """実システムでのE2Eテスト"""
    
    def test_real_api_integration(self):
        """実際のAPIとの統合テスト"""
        # 可能な限り実際の依存関係を使用
        # 実際のユーザーシナリオをテスト
        pass
```

## 3.2 マーカーシステム

### カスタムマーカーの定義

```ini
# pytest.ini
[tool:pytest]
markers =
    unit: Unit tests for individual components
    integration: Integration tests across multiple components
    e2e: End-to-end tests with real components
    slow: Tests that take longer to run
    api: Tests that require API access
    database: Tests that require database access
```

### マーカーの使用例

```python
@pytest.mark.unit
def test_fast_unit_test():
    """高速な単体テスト"""
    pass

@pytest.mark.integration
@pytest.mark.slow
def test_complex_integration():
    """時間のかかる統合テスト"""
    pass

@pytest.mark.e2e
@pytest.mark.api
@pytest.mark.slow
def test_live_api():
    """実際のAPI使用テスト"""
    pass
```

### 実行時の活用

```bash
# 高速テストのみ実行（開発中）
pytest -m "not slow"

# 単体テストのみ実行
pytest -m unit

# API以外のテストを実行（オフライン環境）
pytest -m "not api"

# 統合テストとE2Eテストを実行（リリース前）
pytest -m "integration or e2e"
```

## 3.3 実際のプロジェクトから学ぶ

### 実例: AIジェネレーターのテスト

**テスト対象コード（簡略版）:**
```python
# ai_generator.py
import anthropic

class AIGenerator:
    def __init__(self, api_key, model):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
    
    def generate_response(self, query, tools=None):
        """AI応答を生成"""
        response = self.client.messages.create(
            model=self.model,
            messages=[{"role": "user", "content": query}],
            tools=tools
        )
        return response.content[0].text
```

**段階別テスト実装:**

**レベル1: 基本テスト**
```python
# tests/unit/test_ai_generator_basic.py
import pytest
from unittest.mock import Mock, patch

@pytest.mark.unit
class TestAIGeneratorBasic:
    
    @pytest.fixture
    def ai_generator(self):
        """テスト用AIジェネレーター"""
        with patch('ai_generator.anthropic.Anthropic'):
            from ai_generator import AIGenerator
            return AIGenerator("test-key", "test-model")
    
    def test_initialization(self, ai_generator):
        """初期化テスト"""
        assert ai_generator.model == "test-model"
    
    def test_generate_response_basic(self, ai_generator):
        """基本的な応答生成テスト"""
        # モック設定
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "テスト応答"
        
        ai_generator.client.messages.create.return_value = mock_response
        
        # テスト実行
        result = ai_generator.generate_response("テストクエリ")
        
        # 検証
        assert result == "テスト応答"
        ai_generator.client.messages.create.assert_called_once()
```

**レベル2: 詳細テスト**
```python
def test_api_parameters(self, ai_generator):
    """API呼び出しパラメーターテスト"""
    mock_response = Mock()
    mock_response.content = [Mock()]
    mock_response.content[0].text = "応答"
    
    ai_generator.client.messages.create.return_value = mock_response
    
    ai_generator.generate_response("クエリ")
    
    # 呼び出しパラメーターの詳細検証
    call_args = ai_generator.client.messages.create.call_args[1]
    assert call_args["model"] == "test-model"
    assert call_args["messages"] == [{"role": "user", "content": "クエリ"}]
    assert "tools" not in call_args
```

**レベル3: エラーハンドリング**
```python
def test_api_error_handling(self, ai_generator):
    """APIエラーハンドリングテスト"""
    # APIエラーをシミュレート
    ai_generator.client.messages.create.side_effect = Exception("API Error")
    
    with pytest.raises(Exception, match="API Error"):
        ai_generator.generate_response("クエリ")
```

---

# レベル4: API・Web アプリケーションテスト編 🌐

## 4.1 FastAPI アプリケーションのテスト

### APIテストの重要性

Webアプリケーション開発では、APIエンドポイントが正しく動作することを確認するテストが重要です。RAGシステムのようなWeb API では、以下の点をテストする必要があります：

- エンドポイントが正しいレスポンスを返すか
- リクエストの検証が適切に行われるか  
- エラー処理が適切に動作するか
- セッション管理が正しく機能するか

### TestClient を使ったAPIテスト

**基本的なAPIテストの書き方：**

```python
# test_api_basic.py
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import pytest

# テスト用のアプリを作成（静的ファイルマウントを回避）
def create_test_app():
    """テスト用FastAPIアプリを作成"""
    from fastapi import FastAPI, HTTPException
    from app import QueryRequest, QueryResponse, Source, CourseStats
    
    app = FastAPI()
    
    # テスト用エンドポイント定義
    @app.post("/api/query", response_model=QueryResponse)
    async def test_query(request: QueryRequest):
        # モック化されたRAGシステムを使用
        return QueryResponse(
            answer="テスト応答",
            sources=[Source(text="テストソース", url=None)],
            session_id="test_session_123"
        )
    
    return app

@pytest.fixture
def client():
    """テストクライアント"""
    app = create_test_app()
    return TestClient(app)

def test_query_endpoint_basic(client):
    """クエリエンドポイントの基本テスト"""
    # APIリクエスト送信
    response = client.post(
        "/api/query",
        json={"query": "Python とは何ですか？"}
    )
    
    # レスポンス検証
    assert response.status_code == 200
    data = response.json()
    
    assert "answer" in data
    assert "sources" in data 
    assert "session_id" in data
    assert data["answer"] == "テスト応答"
```

### より実践的なAPIテスト

**実際のRAGシステムを模擬したテスト：**

```python
# test_api_advanced.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

@pytest.fixture
def mock_rag_system():
    """RAGシステムのモック"""
    with patch('app.rag_system') as mock:
        # リアルな応答を設定
        mock.query.return_value = (
            "Pythonは高レベルのプログラミング言語です。",
            [
                {"text": "Python入門", "url": "https://example.com/lesson1"},
                {"text": "プログラミング基礎", "url": None}
            ]
        )
        mock.session_manager.create_session.return_value = "session_456"
        mock.get_course_analytics.return_value = {
            "total_courses": 3,
            "course_titles": ["Python基礎", "Web開発", "データ分析"]
        }
        yield mock

@pytest.fixture 
def client(mock_rag_system):
    """実際のアプリを使ったテストクライアント"""
    from app import app
    # 静的ファイルマウントを一時的に無効化
    with patch('app.StaticFiles'):
        return TestClient(app)

def test_conversation_flow(client):
    """会話フローのテスト"""
    # 最初のクエリ（新しいセッション）
    response1 = client.post(
        "/api/query",
        json={"query": "Pythonとは？"}
    )
    assert response1.status_code == 200
    session_id = response1.json()["session_id"]
    
    # フォローアップクエリ（既存セッション）
    response2 = client.post(
        "/api/query",
        json={
            "query": "変数の使い方は？",
            "session_id": session_id
        }
    )
    assert response2.status_code == 200
    assert response2.json()["session_id"] == session_id

def test_course_stats_endpoint(client):
    """コース統計エンドポイントのテスト"""
    response = client.get("/api/courses")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_courses"] == 3
    assert len(data["course_titles"]) == 3
    assert "Python基礎" in data["course_titles"]

def test_error_handling(client):
    """エラーハンドリングのテスト"""
    # 無効なリクエスト
    response = client.post(
        "/api/query",
        json={"invalid_field": "test"}
    )
    assert response.status_code == 422  # バリデーションエラー
    
    # RAGシステムエラーのシミュレーション
    with patch('app.rag_system') as mock_rag:
        mock_rag.query.side_effect = Exception("データベース接続エラー")
        
        response = client.post(
            "/api/query", 
            json={"query": "test"}
        )
        assert response.status_code == 500
```

## 4.2 テストfixtureの高度な活用

### APIテスト用fixture設計

**階層的なfixture構成：**

```python
# conftest.py（APIテスト用の追加）
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

@pytest.fixture
def api_test_data():
    """APIテスト用データ"""
    return {
        "valid_queries": [
            "Pythonとは何ですか？",
            "変数の使い方を教えて",
            "関数の定義方法は？"
        ],
        "invalid_queries": [
            "",  # 空文字
            "a" * 10000,  # 長すぎる文字列
        ],
        "expected_responses": {
            "python_info": {
                "answer": "Pythonは高レベルプログラミング言語です",
                "sources": [
                    {"text": "Python入門", "url": "https://example.com"}
                ]
            }
        }
    }

@pytest.fixture
def mock_ai_responses():
    """AI応答のモック設定"""
    return {
        "python_query": "Pythonは汎用プログラミング言語です。",
        "error_query": Exception("AI API エラー"),
        "empty_query": "申し訳ございませんが、質問を明確にしてください。"
    }

@pytest.fixture
def api_client(mock_ai_responses):
    """設定済みAPIクライアント"""
    with patch('app.rag_system') as mock_rag:
        # デフォルトの動作を設定
        mock_rag.query.return_value = (
            mock_ai_responses["python_query"],
            [{"text": "参考資料", "url": None}]
        )
        mock_rag.session_manager.create_session.return_value = "test_session"
        
        with patch('app.StaticFiles'):
            from app import app
            yield TestClient(app)
```

### パラメータ化されたAPIテスト

**複数のシナリオを効率的にテスト：**

```python
@pytest.mark.parametrize("query, expected_status, expected_answer", [
    ("Pythonとは？", 200, "Pythonは高レベルプログラミング言語です"),
    ("", 422, None),  # バリデーションエラー
    ("有効なクエリ", 200, "適切な応答"),
])
def test_query_various_inputs(api_client, query, expected_status, expected_answer):
    """様々な入力でのクエリテスト"""
    if expected_status == 200:
        response = api_client.post(
            "/api/query",
            json={"query": query}
        )
    else:
        response = api_client.post(
            "/api/query", 
            json={"invalid": "data"} if expected_status == 422 else {"query": query}
        )
    
    assert response.status_code == expected_status
    
    if expected_status == 200:
        data = response.json()
        assert expected_answer in data["answer"]

@pytest.mark.parametrize("course_count, expected_titles", [
    (0, []),
    (1, ["Python基礎"]),
    (3, ["Python基礎", "Web開発", "データ分析"]),
])
def test_course_analytics_scenarios(api_client, course_count, expected_titles):
    """コース分析の様々なシナリオ"""
    with patch('app.rag_system') as mock_rag:
        mock_rag.get_course_analytics.return_value = {
            "total_courses": course_count,
            "course_titles": expected_titles
        }
        
        response = api_client.get("/api/courses")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_courses"] == course_count
        assert data["course_titles"] == expected_titles
```

## 4.3 マーカーを使ったAPIテスト分類

### APIテスト専用マーカー

```python
# pytest.ini
[tool:pytest]
markers =
    unit: Unit tests for individual components
    integration: Integration tests across multiple components
    e2e: End-to-end tests with real components
    slow: Tests that take longer to run
    api: API endpoint tests
    database: Tests that require database access

# テストファイル内でのマーカー使用
@pytest.mark.api
class TestAPIEndpoints:
    """API エンドポイントテスト"""
    
    @pytest.mark.api
    def test_query_endpoint(self, api_client):
        """クエリエンドポイントテスト"""
        pass
    
    @pytest.mark.api
    @pytest.mark.slow
    def test_large_query_processing(self, api_client):
        """大きなクエリの処理テスト"""
        pass

@pytest.mark.api
@pytest.mark.integration
def test_full_api_workflow(api_client):
    """完全なAPIワークフローテスト"""
    # 複数のエンドポイントを連携させたテスト
    pass
```

### 実行コマンドの活用

```bash
# API テストのみ実行
pytest -m api

# APIテスト以外を実行（高速）
pytest -m "not api"

# 統合レベルのAPIテスト
pytest -m "api and integration"

# 開発中の高速フィードバック
pytest -m "api and not slow" -v
```

# レベル5: 上級実践編 🚀

## 5.1 テストコードの保守性向上

### DRY原則の適用

**❌ 重複の多いテスト:**
```python
def test_user_creation_with_name():
    user_data = {"name": "田中", "email": "tanaka@example.com"}
    db = setup_database()
    user = create_user(user_data)
    db.save(user)
    assert user.name == "田中"
    cleanup_database(db)

def test_user_creation_with_email():
    user_data = {"name": "佐藤", "email": "sato@example.com"}
    db = setup_database()
    user = create_user(user_data)
    db.save(user)
    assert user.email == "sato@example.com"
    cleanup_database(db)
```

**✅ DRY原則適用後:**
```python
class TestUserCreation:
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """データベースセットアップ（自動実行）"""
        self.db = setup_database()
        yield
        cleanup_database(self.db)
    
    @pytest.fixture
    def user_data(self):
        """基本ユーザーデータ"""
        return {"name": "田中", "email": "tanaka@example.com"}
    
    def test_user_name_creation(self, user_data):
        """ユーザー名の保存テスト"""
        user = create_user(user_data)
        self.db.save(user)
        assert user.name == user_data["name"]
    
    def test_user_email_creation(self, user_data):
        """メールアドレスの保存テスト"""
        user = create_user(user_data)
        self.db.save(user)
        assert user.email == user_data["email"]
```

### ヘルパー関数の活用

```python
# tests/helpers.py
def create_test_user(**kwargs):
    """テストユーザー作成ヘルパー"""
    default_data = {
        "name": "テストユーザー",
        "email": "test@example.com",
        "age": 25
    }
    default_data.update(kwargs)
    return create_user(default_data)

def assert_user_equals(actual, expected):
    """ユーザー比較アサートヘルパー"""
    assert actual.name == expected.name
    assert actual.email == expected.email
    assert actual.age == expected.age

# tests/test_users.py
from tests.helpers import create_test_user, assert_user_equals

def test_user_update():
    """ユーザー更新テスト"""
    user = create_test_user(name="更新前")
    user.update_name("更新後")
    
    expected = create_test_user(name="更新後")
    assert_user_equals(user, expected)
```

## 5.2 高度なfixture活用

### 動的fixture

```python
@pytest.fixture(params=["sqlite", "postgresql", "mysql"])
def database_type(request):
    """複数のデータベースタイプでテスト"""
    return request.param

@pytest.fixture
def database_connection(database_type):
    """データベース接続"""
    if database_type == "sqlite":
        conn = create_sqlite_connection()
    elif database_type == "postgresql":
        conn = create_postgresql_connection()
    else:
        conn = create_mysql_connection()
    
    yield conn
    conn.close()

def test_user_creation(database_connection):
    """全データベースタイプでユーザー作成テスト"""
    # このテストは3回実行される（各DBタイプで1回ずつ）
    user = create_user({"name": "テスト"})
    database_connection.save(user)
    assert user.id is not None
```

### 条件付きskip/xfail

```python
import sys
import pytest

@pytest.mark.skipif(sys.platform == "win32", reason="Windows未対応")
def test_unix_specific_feature():
    """Unix専用機能のテスト"""
    pass

@pytest.mark.xfail(reason="既知のバグ #123")
def test_known_bug():
    """既知のバグのテスト"""
    # 失敗することが分かっているテスト
    assert False

@pytest.mark.skipif(not has_api_key(), reason="API_KEY未設定")
def test_api_integration():
    """API統合テスト"""
    pass
```

## 5.3 CI/CDでの活用

### GitHub Actions設定例

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest pytest-cov
        pip install -r requirements.txt
    
    - name: Run unit tests
      run: pytest tests/unit/ -v --cov=src
    
    - name: Run integration tests
      run: pytest tests/integration/ -v
      env:
        API_KEY: ${{ secrets.API_KEY }}
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
```

### テスト段階別実行

```bash
#!/bin/bash
# scripts/run_tests.sh

echo "🧪 単体テスト実行中..."
pytest tests/unit/ -v --tb=short
if [ $? -ne 0 ]; then
    echo "❌ 単体テストが失敗しました"
    exit 1
fi

echo "🔗 統合テスト実行中..."
pytest tests/integration/ -v --tb=short
if [ $? -ne 0 ]; then
    echo "❌ 統合テストが失敗しました"
    exit 1
fi

echo "🚀 E2Eテスト実行中..."
pytest tests/e2e/ -v --tb=short
if [ $? -ne 0 ]; then
    echo "❌ E2Eテストが失敗しました"
    exit 1
fi

echo "✅ 全てのテストが成功しました！"
```

## 5.4 チーム開発でのベストプラクティス

### テストレビューの観点

**✅ 良いテストの特徴:**
```python
def test_user_password_validation_with_weak_password():
    """弱いパスワードは拒否されることを確認"""
    # Arrange: テストデータの準備
    weak_password = "123"
    user_data = {"name": "田中", "password": weak_password}
    
    # Act: テスト対象の実行
    result = validate_user_password(user_data)
    
    # Assert: 結果の検証
    assert result.is_valid is False
    assert "パスワードが短すぎます" in result.error_message
```

**❌ 改善が必要なテスト:**
```python
def test_user():  # テスト名が不明確
    user = create_user({"name": "田中"})  # 何をテストしているか不明
    assert user  # 何を確認しているか不明確
```

### テスト文化の醸成

**1. テストファースト開発:**
```python
# 1. まずテストを書く（失敗する）
def test_calculate_discount():
    assert calculate_discount(100, 0.1) == 90

# 2. 最小限の実装で通す
def calculate_discount(price, discount_rate):
    return price * (1 - discount_rate)

# 3. リファクタリング
def calculate_discount(price, discount_rate):
    if price < 0 or discount_rate < 0 or discount_rate > 1:
        raise ValueError("無効な値です")
    return price * (1 - discount_rate)
```

**2. 継続的改善:**
```bash
# カバレッジ測定
pytest --cov=src --cov-report=html

# 遅いテストの特定
pytest --durations=10

# 定期的なテスト実行
# crontab設定例: 毎日午前3時にテスト実行
0 3 * * * cd /path/to/project && pytest tests/
```

---

# 🎯 まとめと次のステップ

## 学習した内容

### レベル1で習得したスキル
- ✅ pytestの基本的な使い方
- ✅ テストファイルの作成と実行
- ✅ assert文を使った検証
- ✅ 基本的なコマンドの使い方

### レベル2で習得したスキル
- ✅ fixtureによるテストデータ管理
- ✅ モッキングによる外部依存の分離
- ✅ パラメータ化テストでの効率化
- ✅ conftest.pyでの共通化

### レベル3で習得したスキル
- ✅ プロジェクト規模でのテスト構造設計
- ✅ unit/integration/e2eテストの使い分け
- ✅ マーカーシステムでの実行制御
- ✅ 実際のプロジェクトでの応用

### レベル4で習得したスキル
- ✅ テストコードの保守性向上
- ✅ 高度なfixture活用
- ✅ CI/CDでの自動化
- ✅ チーム開発でのベストプラクティス

## 実践的なスキルチェック

以下の項目ができるようになっていれば、実務で通用するpytestスキルが身についています：

**基礎スキル**
- [ ] 新しい機能に対してテストを書ける
- [ ] 既存のテストを読んで理解できる
- [ ] テストが失敗した時に原因を特定できる

**実践スキル**
- [ ] 適切なfixture設計ができる
- [ ] 外部依存をモック化できる
- [ ] テストの実行速度を考慮した設計ができる

**プロジェクトスキル**
- [ ] チーム開発に適したテスト構造を設計できる
- [ ] CI/CDでテストを自動実行できる
- [ ] テストカバレッジを適切に管理できる

## 次のステップ

### 1. より深い学習
- **pytest公式ドキュメント**: https://docs.pytest.org/
- **Advanced pytest features**: プラグイン開発、カスタムマーカー
- **Property-based testing**: Hypothesis との組み合わせ

### 2. 関連ツールの習得
```bash
# テストカバレッジ
pip install pytest-cov

# 並列実行
pip install pytest-xdist

# レポート生成
pip install pytest-html

# ベンチマークテスト
pip install pytest-benchmark
```

### 3. 実践プロジェクト
- 自分のプロジェクトにテストを追加
- オープンソースプロジェクトへの貢献
- チームでのテスト文化構築

## よくある質問 FAQ

**Q: どの程度のテストカバレッジを目指すべきですか？**
A: 一般的に80%以上が推奨されますが、重要なのは数字よりも質です。クリティカルな部分は100%、UI層は50%程度でも問題ありません。

**Q: テストの実行時間が長くて困っています**
A: マーカーを使った段階実行、並列実行（pytest-xdist）、モックの活用で改善できます。開発中は高速テストのみ実行し、CI/CDで全テストを実行する戦略が効果的です。

**Q: 既存プロジェクトにテストを追加するコツは？**
A: 新機能から始めて、バグ修正時にテストを追加、重要度の高い機能から順次カバー、という段階的アプローチがおすすめです。

**Q: チームメンバーにテストを書いてもらうには？**
A: テンプレートの提供、ペアプログラミング、レビューでの教育、テストの価値を実感できる成功体験の共有が効果的です。

---

**🎉 おめでとうございます！**

あなたはpytestの基礎から実践まで、幅広いスキルを身につけました。これらの知識を活用して、品質の高いPythonアプリケーションを開発してください。

テストは一朝一夕で完璧になるものではありません。継続的な改善と学習を通じて、より良いテストを書けるようになります。

Happy Testing! 🚀