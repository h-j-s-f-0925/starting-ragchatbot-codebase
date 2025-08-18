# pytest ベストプラクティス集 ⭐

## 📋 このドキュメントについて

実際のRAGシステム開発プロジェクトで学んだ、pytestを使った効果的なテスト設計・実装のベストプラクティスをまとめました。チーム開発で即活用できる実践的なガイドラインです。

---

## 🏗️ テスト構造設計のベストプラクティス

### 1. ディレクトリ構造の設計原則

**✅ 推奨構造:**
```
project/
├── src/                    # アプリケーションコード
│   ├── __init__.py
│   ├── ai_generator.py
│   ├── vector_store.py
│   └── rag_system.py
├── tests/                  # テストコード
│   ├── conftest.py        # 共通fixture
│   ├── __init__.py
│   ├── unit/              # 単体テスト
│   │   ├── __init__.py
│   │   ├── test_ai_generator_basic.py
│   │   ├── test_ai_generator_tools.py
│   │   └── test_vector_store.py
│   ├── integration/       # 統合テスト
│   │   ├── __init__.py
│   │   ├── test_rag_system.py
│   │   └── test_api_integration.py
│   └── e2e/              # E2Eテスト
│       ├── __init__.py
│       └── test_live_system.py
├── pytest.ini            # pytest設定
└── requirements.txt
```

**原則:**
- **明確な分離**: unit/integration/e2eで明確に分ける
- **ミラー構造**: srcディレクトリ構造をtestsでミラーリング
- **機能別分割**: 大きなテストファイルは機能別に分割（例: test_ai_generator_basic.py, test_ai_generator_tools.py）

### 2. ファイル命名規則

**✅ 良い命名例:**
```python
# テストファイル
test_ai_generator_basic.py      # 基本機能
test_ai_generator_tools.py      # ツール機能
test_ai_generator_sequential.py # 順次実行機能

# テストクラス
class TestAIGeneratorBasic:     # クラス名は Test + 対象クラス名
class TestVectorStoreSearch:    # 機能が明確

# テストメソッド
def test_generate_response_without_tools(self):          # 何をテストするか明確
def test_vector_search_with_empty_query_returns_error(self): # 条件と期待結果が明確
```

**❌ 避けるべき命名:**
```python
# 不明確な命名
test_stuff.py
test_test.py
test_main.py

class TestCase1:
class Test1:

def test_1(self):
def test_something(self):
def test_it_works(self):
```

### 3. テストサイズの管理

**テストファイルサイズの目安:**
- **Unit Tests**: 200-400行/ファイル
- **Integration Tests**: 150-300行/ファイル  
- **E2E Tests**: 100-200行/ファイル

**分割の実例（570行 → 3ファイル）:**
```python
# 分割前（570行）
test_ai_generator.py

# 分割後
test_ai_generator_basic.py     # 220行 - 基本機能
test_ai_generator_tools.py     # 178行 - ツール実行
test_ai_generator_sequential.py # 172行 - 順次呼び出し
```

---

## 🎯 テストコード品質のベストプラクティス

### 4. テストメソッドの構造（AAA原則）

**✅ 推奨パターン:**
```python
def test_user_creation_with_valid_data(self):
    """有効なデータでユーザー作成が成功することを確認"""
    # Arrange（準備）
    user_data = {
        "name": "田中太郎",
        "email": "tanaka@example.com",
        "age": 25
    }
    expected_user_id = 123
    
    # Act（実行）
    result = create_user(user_data)
    
    # Assert（検証）
    assert result.id == expected_user_id
    assert result.name == user_data["name"]
    assert result.email == user_data["email"]
    assert result.created_at is not None
```

**AAA原則の詳細:**
- **Arrange**: テストデータとモックの準備
- **Act**: テスト対象の実行（1回のみ）
- **Assert**: 結果の検証

### 5. アサーションのベストプラクティス

**✅ 明確なアサーション:**
```python
# 具体的な値の検証
assert response.status_code == 200
assert user.name == "田中太郎"
assert len(results) == 3

# カスタムエラーメッセージ
assert result.is_valid, f"検証が失敗しました: {result.error_message}"
assert response.data is not None, "レスポンスデータが空です"

# 例外の検証
with pytest.raises(ValueError, match="無効なメールアドレス"):
    create_user({"email": "invalid-email"})

# 部分一致の検証
assert "エラー" in response.message
assert response.data["user_id"] in [1, 2, 3]
```

**❌ 避けるべきアサーション:**
```python
# 曖昧なアサーション
assert response        # 何をチェックしているか不明
assert not error       # どんなエラーを期待しているか不明
assert user            # ユーザーの何を確認しているか不明

# 複雑すぎるアサーション
assert len([x for x in data if x.status == "active" and x.created_at > datetime.now() - timedelta(days=7)]) > 0
```

### 6. テストの独立性

**✅ 独立したテスト:**
```python
class TestUserManagement:
    
    @pytest.fixture
    def clean_database(self):
        """各テスト前にデータベースをクリーンアップ"""
        clear_database()
        yield
        clear_database()
    
    def test_user_creation(self, clean_database):
        """ユーザー作成テスト"""
        user = create_user({"name": "田中"})
        assert user.id is not None
    
    def test_user_deletion(self, clean_database):
        """ユーザー削除テスト"""
        user = create_user({"name": "佐藤"})
        delete_user(user.id)
        assert get_user(user.id) is None
```

**❌ 依存関係のあるテスト:**
```python
class TestUserBad:
    def test_1_create_user(self):
        """テスト実行順序に依存"""
        self.user = create_user({"name": "田中"})
        
    def test_2_update_user(self):
        """前のテストに依存している"""
        self.user.update_name("佐藤")  # self.userが存在することを前提
```

---

## 🔧 fixtureのベストプラクティス

### 7. fixture設計原則

**スコープの適切な使い分け:**
```python
# セッション全体で1回だけ作成（重い処理）
@pytest.fixture(scope="session")
def database_connection():
    """データベース接続（セッション全体で共有）"""
    conn = create_connection()
    yield conn
    conn.close()

# モジュール内で1回だけ作成
@pytest.fixture(scope="module")
def large_dataset():
    """大きなテストデータセット（モジュール内で共有）"""
    return load_large_dataset()

# クラス内で1回だけ作成
@pytest.fixture(scope="class")
def api_client():
    """APIクライアント（クラス内で共有）"""
    return APIClient()

# 各テスト関数で新しく作成（デフォルト）
@pytest.fixture
def user_data():
    """ユーザーデータ（各テストで新しく作成）"""
    return {"name": "テストユーザー", "email": "test@example.com"}
```

### 8. 階層的fixture設計

**✅ 階層的な設計:**
```python
# conftest.py
@pytest.fixture
def base_config():
    """基本設定"""
    return {"debug": True, "timeout": 30}

@pytest.fixture  
def test_config(base_config):
    """テスト用設定"""
    base_config.update({"database_url": "sqlite:///:memory:"})
    return base_config

@pytest.fixture
def ai_client(test_config):
    """AIクライアント"""
    return AIClient(test_config["api_key"])

@pytest.fixture
def rag_system(ai_client, test_config):
    """RAGシステム（複数のfixtureを組み合わせ）"""
    return RAGSystem(ai_client, test_config)
```

### 9. fixtureの命名とドキュメント

**✅ 明確な命名:**
```python
@pytest.fixture
def mock_anthropic_client():
    """モック化されたAnthropicクライアント
    
    Returns:
        Mock: APIレスポンスを制御可能なモッククライアント
    """
    client = Mock()
    return client

@pytest.fixture
def sample_course_data():
    """テスト用コースデータ
    
    Returns:
        dict: 4つのレッスンを持つサンプルコースデータ
    """
    return {
        "title": "Python基礎",
        "instructor": "田中先生", 
        "lessons": [
            {"number": 1, "title": "変数と型"},
            {"number": 2, "title": "制御構造"},
            {"number": 3, "title": "関数"},
            {"number": 4, "title": "クラス"},
        ]
    }
```

---

## 🎭 モッキングのベストプラクティス

### 10. 適切なモック対象の選択

**✅ モックすべきもの:**
```python
# 外部API呼び出し
@patch('requests.get')
def test_api_call(mock_get):
    mock_get.return_value.json.return_value = {"status": "success"}

# ファイルシステム操作
@patch('builtins.open', mock_open(read_data="test data"))
def test_file_reading():
    pass

# 時間に依存する処理
@patch('datetime.datetime')
def test_time_dependent_logic(mock_datetime):
    mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)

# 重い計算処理
@patch('complex_calculation.heavy_compute')
def test_business_logic(mock_compute):
    mock_compute.return_value = 42
```

**❌ モックしない方が良いもの:**
```python
# 標準ライブラリの基本機能
# len(), str(), int() など

# 自分のアプリケーションのビジネスロジック
# （統合テストでない限り）

# 軽量な計算処理
# 簡単な数値計算、文字列操作など
```

### 11. モックの設定と検証

**✅ 適切なモック設定:**
```python
def test_user_notification_service(self):
    """ユーザー通知サービステスト"""
    with patch('email_service.send_email') as mock_send:
        # モックの戻り値設定
        mock_send.return_value = {"status": "sent", "id": "12345"}
        
        # テスト実行
        result = notify_user("user@example.com", "テストメッセージ")
        
        # モック呼び出しの検証
        mock_send.assert_called_once_with(
            to="user@example.com",
            subject="通知",
            body="テストメッセージ"
        )
        
        # 戻り値の検証
        assert result["notification_id"] == "12345"
```

### 12. fixtureでのモック管理

**✅ 再利用可能なモック:**
```python
# conftest.py
@pytest.fixture
def mock_api_client():
    """API クライアントのモック"""
    with patch('api_client.APIClient') as mock:
        # デフォルトの振る舞いを設定
        mock.return_value.get.return_value = {"status": "success"}
        mock.return_value.post.return_value = {"id": 123}
        yield mock.return_value

# テストファイル
def test_data_retrieval(mock_api_client):
    """データ取得テスト"""
    # 特定のレスポンスを設定
    mock_api_client.get.return_value = {"data": [1, 2, 3]}
    
    result = fetch_data()
    assert len(result) == 3
```

---

## 🏷️ マーカーとテスト分類

### 13. 効果的なマーカー活用

**✅ プロジェクトに適したマーカー:**
```python
# pytest.ini
[tool:pytest]
markers =
    unit: Unit tests for individual components
    integration: Integration tests across multiple components  
    e2e: End-to-end tests with real components
    slow: Tests that take longer than 5 seconds
    api: Tests that require external API access
    database: Tests that require database access
    auth: Tests that require authentication
    critical: Tests for critical business logic
```

**使用例:**
```python
@pytest.mark.unit
@pytest.mark.critical
def test_payment_calculation():
    """重要な支払い計算ロジック"""
    pass

@pytest.mark.integration
@pytest.mark.database
@pytest.mark.slow
def test_large_data_processing():
    """大量データ処理の統合テスト"""
    pass

@pytest.mark.e2e
@pytest.mark.api
@pytest.mark.slow
def test_complete_user_workflow():
    """完全なユーザーワークフロー"""
    pass
```

### 14. 条件付き実行

**✅ 環境に応じた実行制御:**
```python
import os
import pytest

# 環境変数による制御
@pytest.mark.skipif(
    not os.getenv("API_KEY"), 
    reason="API_KEY環境変数が設定されていません"
)
def test_api_integration():
    pass

# プラットフォーム依存
@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Unix系OSでのみ実行"
)
def test_unix_specific_feature():
    pass

# カスタム条件
def has_gpu():
    return torch.cuda.is_available()

@pytest.mark.skipif(not has_gpu(), reason="GPU未搭載")
def test_gpu_computation():
    pass
```

---

## 📊 テスト実行とCI/CDのベストプラクティス

### 15. 段階的テスト実行戦略

**開発段階別の実行パターン:**
```bash
# 開発中（高速フィードバック）
pytest -m "unit and not slow" -x --tb=short

# 機能完成時（関連テスト）
pytest tests/unit/test_new_feature.py tests/integration/test_new_feature.py -v

# プルリクエスト前（包括的チェック）
pytest -m "unit or integration" --cov=src --cov-fail-under=80

# リリース前（全テスト）
pytest --tb=short --html=report.html --cov=src --cov-report=html
```

### 16. CI/CD設定例

**GitHub Actions設定:**
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
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest pytest-cov pytest-xdist
        pip install -r requirements.txt
    
    - name: Run unit tests
      run: pytest tests/unit/ -v --cov=src --cov-report=xml -n auto
    
    - name: Run integration tests
      run: pytest tests/integration/ -v
      env:
        DATABASE_URL: ${{ secrets.TEST_DATABASE_URL }}
        API_KEY: ${{ secrets.TEST_API_KEY }}
    
    - name: Run E2E tests
      run: pytest tests/e2e/ -v --tb=short
      if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

---

## 🧪 テストデータ管理のベストプラクティス

### 17. テストデータの分離

**✅ データ分離の手法:**
```python
# 1. ファクトリー関数
def create_test_user(**kwargs):
    """テストユーザー作成ファクトリー"""
    defaults = {
        "name": "テストユーザー",
        "email": "test@example.com",
        "age": 25,
        "role": "user"
    }
    defaults.update(kwargs)
    return User(**defaults)

# 2. データクラスの活用
@dataclass
class TestData:
    valid_user: dict
    invalid_user: dict
    admin_user: dict
    
    @classmethod
    def create(cls):
        return cls(
            valid_user={"name": "田中", "email": "tanaka@example.com"},
            invalid_user={"name": "", "email": "invalid"},
            admin_user={"name": "管理者", "email": "admin@example.com", "role": "admin"}
        )

# 3. JSONファイルでの管理
@pytest.fixture
def test_data():
    """外部ファイルからテストデータを読み込み"""
    with open("tests/data/sample_data.json") as f:
        return json.load(f)
```

### 18. テストデータベースの管理

**✅ データベーステストの手法:**
```python
@pytest.fixture(scope="session")
def test_database():
    """テスト用データベースセットアップ"""
    # テスト用DBの作成
    db_url = "sqlite:///:memory:"
    engine = create_engine(db_url)
    create_all_tables(engine)
    
    yield engine
    
    # クリーンアップ
    engine.dispose()

@pytest.fixture(autouse=True)
def clean_database(test_database):
    """各テスト後にDBをクリーンアップ"""
    yield
    for table in reversed(metadata.sorted_tables):
        test_database.execute(table.delete())
```

---

## 🔍 デバッグとトラブルシューティング

### 19. 効果的なデバッグ手法

**デバッグ用のテスト実行:**
```bash
# 特定テストのデバッグ
pytest tests/test_example.py::test_specific -vv -s --tb=long --pdb

# ログ出力を含む実行
pytest tests/test_example.py -v -s --log-level=DEBUG

# 失敗したテストのみ再実行
pytest --lf -vv -s
```

**テストコード内でのデバッグ:**
```python
def test_complex_logic(self):
    """複雑なロジックのテスト"""
    # デバッグ用print（-s オプションで表示）
    print(f"デバッグ: input_data = {input_data}")
    
    # ブレークポイント設定
    import pdb; pdb.set_trace()
    
    # アサーション失敗時の詳細情報
    result = complex_function(input_data)
    assert result.status == "success", f"実際の結果: {result.__dict__}"
```

### 20. 一般的な問題と解決策

**よくある問題:**

**1. テストが見つからない**
```python
# 解決策: ファイル・関数命名規則の確認
# ❌ my_test.py
# ✅ test_my_module.py

# ❌ def check_something():
# ✅ def test_something():
```

**2. インポートエラー**
```python
# 解決策: conftest.py でパス設定
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

**3. fixture が見つからない**
```python
# 解決策: conftest.py の配置確認
tests/
├── conftest.py          # 全テストで利用可能
├── unit/
│   ├── conftest.py      # unitディレクトリ内でのみ利用可能
│   └── test_*.py
└── integration/
    └── test_*.py
```

---

## 📈 テスト品質向上のメトリクス

### 21. 測定すべき指標

**コードカバレッジ:**
```bash
# カバレッジ測定
pytest --cov=src --cov-report=html --cov-report=term-missing

# 閾値設定
pytest --cov=src --cov-fail-under=80

# ブランチカバレッジ
pytest --cov=src --cov-branch --cov-report=html
```

**テスト実行時間:**
```bash
# 遅いテストの特定
pytest --durations=10

# 並列実行での改善
pytest -n auto

# マーカーでの分類実行
pytest -m "not slow"
```

### 22. 品質指標の目安

**推奨される指標:**
- **コードカバレッジ**: 80%以上（クリティカル部分は95%以上）
- **テスト実行時間**: 単体テストは5分以内、統合テストは15分以内
- **テスト失敗率**: 継続的に1%以下
- **テストファイルサイズ**: 400行以下/ファイル

---

## 🤝 チーム開発でのベストプラクティス

### 23. コードレビューの観点

**テストレビューチェックリスト:**
- [ ] テスト名が動作を明確に表している
- [ ] AAA原則に従って構造化されている
- [ ] 適切なマーカーが付与されている
- [ ] fixtureが適切に活用されている
- [ ] モックが必要最小限に抑えられている
- [ ] エラーケースがカバーされている
- [ ] アサーションが具体的で明確

### 24. テスト文化の醸成

**チーム規約例:**
```markdown
## テスト作成規約

### 必須事項
1. 新機能にはテストを必ず追加
2. バグ修正時は再発防止テストを追加
3. プルリクエストはテスト成功が条件

### 推奨事項
1. TDD（テストファースト）の実践
2. ペアプログラミングでのテスト作成
3. 定期的なテストコードレビュー

### 品質基準
1. コードカバレッジ80%以上維持
2. テスト実行時間10分以内
3. テスト失敗は即座に修正
```

---

## 🎯 まとめ

このベストプラクティス集で紹介した手法を活用することで、保守性が高く効果的なテストスイートを構築できます。

**重要なポイント:**

1. **構造設計**: 明確な分離と一貫した命名
2. **テスト品質**: AAA原則と独立性の確保
3. **fixture活用**: 再利用性と階層設計
4. **モック戦略**: 適切な対象選択と管理
5. **実行戦略**: 段階的実行とCI/CD統合
6. **チーム運用**: レビュー文化と継続改善

**継続的改善:**
- 定期的なテスト見直し
- チーム内での知識共有
- 新しい手法の積極的な導入
- メトリクスに基づく改善

効果的なテストは一朝一夕では完成しません。このベストプラクティスを参考に、チームの状況に合わせて継続的に改善していきましょう。

Happy Testing! 🚀