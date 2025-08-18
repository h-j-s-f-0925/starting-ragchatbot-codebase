# Level 4: API Testing Examples 🌐

このディレクトリには、FastAPIアプリケーションのAPIエンドポイントテストの実践例が含まれています。

## 📁 ファイル構成

### test_fastapi_basic.py
**初心者向け基本APIテスト**

- ✅ TestClientの基本的な使い方
- ✅ シンプルなGET/POSTエンドポイントテスト  
- ✅ レスポンス検証の基礎
- ✅ エラーハンドリングテスト
- ✅ パラメータ化テストの例

**学習ポイント:**
- FastAPI TestClientの基本操作
- HTTPステータスコードの検証
- JSONレスポンスの構造検証
- Pydanticモデルとの連携

### test_fastapi_advanced.py
**上級者向け高度なAPIテスト**

- ✅ 複雑なモック戦略とRAGシステム模擬
- ✅ セッション管理のテスト
- ✅ 並行処理・パフォーマンステスト
- ✅ エラー回復ワークフローテスト
- ✅ 完全なユーザージャーニーテスト

**学習ポイント:**
- リアルなシステム動作の模擬
- 状態管理とセッション追跡
- エラーシナリオの包括的テスト
- パフォーマンステストの実装

## 🚀 実行方法

### 基本テストの実行
```bash
# 基本APIテストのみ実行
pytest docs/pytest_learning/examples/level4_api_testing/test_fastapi_basic.py -v

# 詳細出力で実行
pytest docs/pytest_learning/examples/level4_api_testing/test_fastapi_basic.py -vv -s

# 特定のテストクラスのみ実行
pytest docs/pytest_learning/examples/level4_api_testing/test_fastapi_basic.py::TestBasicAPIEndpoints -v
```

### 上級テストの実行
```bash
# 上級APIテストの実行
pytest docs/pytest_learning/examples/level4_api_testing/test_fastapi_advanced.py -v

# 遅いテスト（パフォーマンステスト）も含めて実行
pytest docs/pytest_learning/examples/level4_api_testing/test_fastapi_advanced.py -v -m ""

# 特定のテストクラスのみ
pytest docs/pytest_learning/examples/level4_api_testing/test_fastapi_advanced.py::TestAdvancedSessionManagement -v
```

### 全APIテスト例の実行
```bash
# ディレクトリ内の全テスト実行
pytest docs/pytest_learning/examples/level4_api_testing/ -v

# 実行時間測定付き
pytest docs/pytest_learning/examples/level4_api_testing/ -v --durations=5

# パフォーマンステストを除外
pytest docs/pytest_learning/examples/level4_api_testing/ -v -m "not slow"
```

## 📚 学習の進め方

### 1. 基本から始める（test_fastapi_basic.py）
1. `TestBasicAPIEndpoints` - 基本的なAPIテスト
2. `TestAPIErrorHandling` - エラーハンドリング
3. `TestAPIResponseValidation` - レスポンス検証
4. `TestHTTPBasics` - HTTP基礎知識

### 2. 上級テクニックを学ぶ（test_fastapi_advanced.py）
1. `TestAdvancedSessionManagement` - セッション管理
2. `TestAdvancedErrorHandling` - 複雑なエラーシナリオ
3. `TestAPIPerformance` - パフォーマンステスト
4. `TestComplexWorkflows` - ワークフローテスト

### 3. 実際のプロジェクトに応用
- 自分のFastAPIプロジェクトでテストを実装
- エラーケースの追加
- パフォーマンス要件の検証
- セキュリティテストの追加

## 🔧 必要な依存関係

これらの例を実行するには、以下のパッケージが必要です：

```bash
# 基本的な依存関係
pip install fastapi
pip install pytest
pip install httpx  # FastAPI TestClient用

# 上級機能用
pip install pytest-asyncio  # 非同期テスト用
pip install pytest-xdist    # 並列実行用
```

## 💡 実践のヒント

### テストの分類
```bash
# 基本的なAPIテストのみ
pytest -m "not slow" docs/pytest_learning/examples/level4_api_testing/

# パフォーマンステスト含む
pytest docs/pytest_learning/examples/level4_api_testing/

# エラーハンドリングのみ
pytest -k "error" docs/pytest_learning/examples/level4_api_testing/
```

### デバッグ時のコマンド
```bash
# print文を表示
pytest -s docs/pytest_learning/examples/level4_api_testing/test_fastapi_basic.py

# 詳細なトレースバック
pytest --tb=long docs/pytest_learning/examples/level4_api_testing/

# 特定のテストをデバッグ
pytest --pdb docs/pytest_learning/examples/level4_api_testing/test_fastapi_basic.py::TestBasicAPIEndpoints::test_health_check
```

## 🎯 学習目標

これらの例を完了すると、以下のスキルが身につきます：

**基礎レベル:**
- [ ] FastAPI TestClientの基本操作
- [ ] HTTPステータスコードの検証
- [ ] JSONレスポンスの構造確認
- [ ] 基本的なエラーハンドリング

**応用レベル:**
- [ ] 複雑なモック戦略の実装
- [ ] セッション管理のテスト
- [ ] パフォーマンステストの作成
- [ ] ユーザージャーニーテストの設計

**実践レベル:**
- [ ] 自分のAPIプロジェクトでのテスト実装
- [ ] CI/CDパイプラインでのAPIテスト実行
- [ ] セキュリティテストの追加
- [ ] 本番環境でのモニタリング

## 🔗 関連リソース

- [FastAPI Testing Documentation](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)

Happy API Testing! 🚀