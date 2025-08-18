"""
Level 3: Advanced - 高度なfixture活用

このファイルでは pytest fixture の高度な使い方について学びます。
- fixture のスコープ管理
- 依存関係のある fixture
- 動的 fixture の作成
- fixture factory パターン
- yield fixture での setup/teardown

実行方法:
pytest examples/level3_advanced/test_advanced_fixtures.py -v -s
"""

import pytest
import tempfile
import sqlite3
import json
from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass
from typing import List, Dict, Any
import logging


# テスト対象のクラス群
@dataclass
class User:
    """ユーザーモデル"""
    id: int
    name: str
    email: str
    role: str = "user"


@dataclass
class Task:
    """タスクモデル"""
    id: int
    title: str
    description: str
    user_id: int
    completed: bool = False


class Database:
    """シンプルなデータベースクラス"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self._setup_tables()
    
    def _setup_tables(self):
        """テーブルを作成"""
        cursor = self.connection.cursor()
        
        # Users テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                role TEXT DEFAULT 'user'
            )
        ''')
        
        # Tasks テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                user_id INTEGER,
                completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        self.connection.commit()
    
    def create_user(self, name: str, email: str, role: str = "user") -> int:
        """ユーザーを作成"""
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, role) VALUES (?, ?, ?)",
            (name, email, role)
        )
        self.connection.commit()
        return cursor.lastrowid
    
    def get_user(self, user_id: int) -> User:
        """ユーザーを取得"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return User(**dict(row))
        return None
    
    def create_task(self, title: str, description: str, user_id: int) -> int:
        """タスクを作成"""
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO tasks (title, description, user_id) VALUES (?, ?, ?)",
            (title, description, user_id)
        )
        self.connection.commit()
        return cursor.lastrowid
    
    def get_tasks_by_user(self, user_id: int) -> List[Task]:
        """ユーザーのタスクを取得"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM tasks WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        return [Task(**dict(row)) for row in rows]
    
    def close(self):
        """データベース接続を閉じる"""
        if self.connection:
            self.connection.close()


class ConfigManager:
    """設定管理クラス"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        config_file = Path(self.config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def get(self, key: str, default=None):
        """設定値を取得"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """設定値を設定"""
        self.config[key] = value
        self._save_config()
    
    def _save_config(self):
        """設定ファイルに保存"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)


class Application:
    """アプリケーションクラス"""
    
    def __init__(self, database: Database, config_manager: ConfigManager):
        self.database = database
        self.config_manager = config_manager
    
    def register_user(self, name: str, email: str, role: str = "user") -> int:
        """ユーザー登録"""
        user_id = self.database.create_user(name, email, role)
        
        # ログ設定
        if self.config_manager.get("enable_logging", False):
            print(f"ユーザー登録: {name} ({email})")
        
        return user_id
    
    def create_user_task(self, user_id: int, title: str, description: str) -> int:
        """ユーザーのタスクを作成"""
        return self.database.create_task(title, description, user_id)
    
    def get_user_summary(self, user_id: int) -> Dict[str, Any]:
        """ユーザーサマリーを取得"""
        user = self.database.get_user(user_id)
        if not user:
            return None
        
        tasks = self.database.get_tasks_by_user(user_id)
        completed_tasks = [t for t in tasks if t.completed]
        
        return {
            "user": user,
            "total_tasks": len(tasks),
            "completed_tasks": len(completed_tasks),
            "pending_tasks": len(tasks) - len(completed_tasks)
        }


# ここからテストコード

# 基本的なセッションスコープ fixture
@pytest.fixture(scope="session")
def temp_base_dir():
    """セッション全体で使用する一時ディレクトリ"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        print(f"\n=== セッション用一時ディレクトリ作成: {tmp_dir} ===")
        yield Path(tmp_dir)
        print(f"\n=== セッション用一時ディレクトリ削除: {tmp_dir} ===")


# モジュールスコープの fixture
@pytest.fixture(scope="module")
def config_file(temp_base_dir):
    """モジュール全体で使用する設定ファイル"""
    config_path = temp_base_dir / "config.json"
    
    # 初期設定を作成
    initial_config = {
        "enable_logging": True,
        "max_users": 100,
        "default_role": "user",
        "features": {
            "notifications": True,
            "analytics": False
        }
    }
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(initial_config, f, indent=2)
    
    print(f"\n=== 設定ファイル作成: {config_path} ===")
    yield config_path
    print(f"\n=== 設定ファイル削除: {config_path} ===")


# クラススコープの fixture
@pytest.fixture(scope="class")
def shared_database(temp_base_dir):
    """クラス内で共有するデータベース"""
    db_path = temp_base_dir / "shared_test.db"
    db = Database(str(db_path))
    
    print(f"\n=== 共有データベース作成: {db_path} ===")
    yield db
    
    db.close()
    print(f"\n=== 共有データベース削除: {db_path} ===")


# ファクトリーパターンの fixture
@pytest.fixture
def database_factory(temp_base_dir):
    """データベースを作成するファクトリー"""
    created_databases = []
    
    def _create_database(name: str = "test.db") -> Database:
        db_path = temp_base_dir / name
        db = Database(str(db_path))
        created_databases.append(db)
        return db
    
    yield _create_database
    
    # クリーンアップ
    for db in created_databases:
        db.close()
    print(f"\n=== ファクトリーで作成したデータベース {len(created_databases)} 個をクリーンアップ ===")


# 依存関係のある fixture チェーン
@pytest.fixture
def config_manager(config_file):
    """設定マネージャー（config_file に依存）"""
    return ConfigManager(str(config_file))


@pytest.fixture
def database(temp_base_dir):
    """テスト用データベース"""
    db_path = temp_base_dir / "test.db"
    db = Database(str(db_path))
    yield db
    db.close()


@pytest.fixture
def application(database, config_manager):
    """アプリケーション（database と config_manager に依存）"""
    return Application(database, config_manager)


# サンプルデータを提供する fixture
@pytest.fixture
def sample_users():
    """サンプルユーザーデータ"""
    return [
        {"name": "田中太郎", "email": "tanaka@example.com", "role": "admin"},
        {"name": "佐藤花子", "email": "sato@example.com", "role": "user"},
        {"name": "鈴木一郎", "email": "suzuki@example.com", "role": "user"},
    ]


@pytest.fixture
def sample_tasks():
    """サンプルタスクデータ"""
    return [
        {"title": "レポート作成", "description": "月次レポートを作成する"},
        {"title": "会議準備", "description": "来週の会議資料を準備する"},
        {"title": "システム更新", "description": "サーバーのOSを更新する"},
    ]


# parametrize との組み合わせ fixture
@pytest.fixture(params=["sqlite", "memory"])
def database_type(request, temp_base_dir):
    """異なるタイプのデータベースを提供"""
    if request.param == "sqlite":
        db_path = temp_base_dir / "param_test.db"
        db = Database(str(db_path))
    else:  # memory
        db = Database(":memory:")
    
    yield db
    db.close()


# autouse fixture の例
@pytest.fixture(autouse=True)
def test_isolation():
    """テスト分離のための autouse fixture"""
    print(f"\n--- テスト開始: {pytest.current_test_name if hasattr(pytest, 'current_test_name') else 'unknown'} ---")
    yield
    print(f"--- テスト終了 ---")


# ここからテストクラス

class TestBasicFixtureScopes:
    """基本的な fixture スコープのテスト"""
    
    def test_session_fixture_persistence(self, temp_base_dir):
        """セッション fixture の永続性テスト"""
        # セッション全体で同じディレクトリが使用される
        test_file = temp_base_dir / "session_test.txt"
        test_file.write_text("セッション用テストファイル")
        
        assert test_file.exists()
        assert test_file.read_text() == "セッション用テストファイル"
    
    def test_module_fixture_usage(self, config_file):
        """モジュール fixture の使用テスト"""
        # 設定ファイルが存在することを確認
        assert config_file.exists()
        
        # 設定内容を確認
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        assert config["enable_logging"] == True
        assert config["max_users"] == 100
        assert config["default_role"] == "user"


class TestDatabaseFixtures:
    """データベース fixture のテスト"""
    
    def test_shared_database_first(self, shared_database):
        """共有データベースの最初のテスト"""
        # ユーザーを作成
        user_id = shared_database.create_user("共有ユーザー1", "shared1@example.com")
        assert user_id is not None
        
        # ユーザーが作成されたことを確認
        user = shared_database.get_user(user_id)
        assert user.name == "共有ユーザー1"
        assert user.email == "shared1@example.com"
    
    def test_shared_database_second(self, shared_database):
        """共有データベースの二番目のテスト"""
        # 前のテストで作成したユーザーがまだ存在することを確認
        # （クラススコープなので共有される）
        user = shared_database.get_user(1)  # 最初に作成されたユーザー
        if user:  # 実行順序によっては存在しない場合もある
            assert user.name == "共有ユーザー1"
        
        # 新しいユーザーを追加
        user_id = shared_database.create_user("共有ユーザー2", "shared2@example.com")
        assert user_id is not None
    
    def test_isolated_database(self, database):
        """分離されたデータベースのテスト"""
        # このテストは独立したデータベースを使用
        user_id = database.create_user("分離ユーザー", "isolated@example.com")
        assert user_id == 1  # 新しいデータベースなので ID は 1 から
        
        user = database.get_user(user_id)
        assert user.name == "分離ユーザー"


class TestFactoryFixtures:
    """ファクトリー fixture のテスト"""
    
    def test_database_factory_single(self, database_factory):
        """データベースファクトリーの単一作成テスト"""
        db = database_factory("single_test.db")
        
        # データベースが正常に作成されることを確認
        user_id = db.create_user("ファクトリーユーザー", "factory@example.com")
        assert user_id is not None
        
        user = db.get_user(user_id)
        assert user.name == "ファクトリーユーザー"
    
    def test_database_factory_multiple(self, database_factory):
        """データベースファクトリーの複数作成テスト"""
        # 複数のデータベースを作成
        db1 = database_factory("multi_test1.db")
        db2 = database_factory("multi_test2.db")
        
        # それぞれに異なるデータを作成
        user_id1 = db1.create_user("ユーザー1", "user1@example.com")
        user_id2 = db2.create_user("ユーザー2", "user2@example.com")
        
        # データが分離されていることを確認
        user1 = db1.get_user(user_id1)
        user2 = db2.get_user(user_id2)
        
        assert user1.name == "ユーザー1"
        assert user2.name == "ユーザー2"
        
        # 相互に存在しないことを確認
        assert db1.get_user(user_id2) is None
        assert db2.get_user(user_id1) is None


class TestDependentFixtures:
    """依存関係のある fixture のテスト"""
    
    def test_application_functionality(self, application, sample_users):
        """アプリケーションの基本機能テスト"""
        # ユーザー登録
        user_data = sample_users[0]
        user_id = application.register_user(
            user_data["name"],
            user_data["email"],
            user_data["role"]
        )
        
        assert user_id is not None
        
        # タスクを作成
        task_id = application.create_user_task(
            user_id,
            "テストタスク",
            "これはテスト用のタスクです"
        )
        
        assert task_id is not None
        
        # ユーザーサマリーを取得
        summary = application.get_user_summary(user_id)
        
        assert summary["user"].name == user_data["name"]
        assert summary["total_tasks"] == 1
        assert summary["completed_tasks"] == 0
        assert summary["pending_tasks"] == 1
    
    def test_config_manager_functionality(self, config_manager):
        """設定マネージャーの機能テスト"""
        # 既存の設定を確認
        assert config_manager.get("enable_logging") == True
        assert config_manager.get("max_users") == 100
        
        # 新しい設定を追加
        config_manager.set("test_setting", "test_value")
        assert config_manager.get("test_setting") == "test_value"
        
        # デフォルト値の確認
        assert config_manager.get("nonexistent_key", "default") == "default"


class TestParametrizedFixtures:
    """パラメータ化された fixture のテスト"""
    
    def test_different_database_types(self, database_type, sample_users):
        """異なるタイプのデータベースでのテスト"""
        # データベースの種類に関係なく同じ操作ができることを確認
        user_data = sample_users[0]
        user_id = database_type.create_user(
            user_data["name"],
            user_data["email"],
            user_data["role"]
        )
        
        assert user_id is not None
        
        user = database_type.get_user(user_id)
        assert user.name == user_data["name"]
        assert user.email == user_data["email"]
        assert user.role == user_data["role"]


class TestComplexFixtureInteractions:
    """複雑な fixture 相互作用のテスト"""
    
    def test_full_application_workflow(self, application, sample_users, sample_tasks):
        """完全なアプリケーションワークフローのテスト"""
        # 複数のユーザーを登録
        user_ids = []
        for user_data in sample_users:
            user_id = application.register_user(
                user_data["name"],
                user_data["email"],
                user_data["role"]
            )
            user_ids.append(user_id)
        
        # 各ユーザーにタスクを作成
        for i, user_id in enumerate(user_ids):
            for j, task_data in enumerate(sample_tasks):
                task_title = f"{task_data['title']} (ユーザー{i+1})"
                application.create_user_task(
                    user_id,
                    task_title,
                    task_data["description"]
                )
        
        # 各ユーザーのサマリーを確認
        for i, user_id in enumerate(user_ids):
            summary = application.get_user_summary(user_id)
            
            assert summary["user"].name == sample_users[i]["name"]
            assert summary["total_tasks"] == len(sample_tasks)
            assert summary["completed_tasks"] == 0
            assert summary["pending_tasks"] == len(sample_tasks)


# カスタム fixture の例
@pytest.fixture
def logged_database(database, config_manager):
    """ログ機能付きデータベース wrapper"""
    
    class LoggedDatabase:
        def __init__(self, db, config):
            self.db = db
            self.config = config
            self.log_enabled = config.get("enable_logging", False)
        
        def create_user(self, name, email, role="user"):
            user_id = self.db.create_user(name, email, role)
            if self.log_enabled:
                print(f"ログ: ユーザー作成 ID={user_id}, Name={name}")
            return user_id
        
        def get_user(self, user_id):
            user = self.db.get_user(user_id)
            if self.log_enabled and user:
                print(f"ログ: ユーザー取得 ID={user_id}, Name={user.name}")
            return user
    
    return LoggedDatabase(database, config_manager)


class TestCustomFixtures:
    """カスタム fixture のテスト"""
    
    def test_logged_database_functionality(self, logged_database, sample_users):
        """ログ機能付きデータベースのテスト"""
        user_data = sample_users[0]
        
        # ユーザー作成（ログ出力されるはず）
        user_id = logged_database.create_user(
            user_data["name"],
            user_data["email"],
            user_data["role"]
        )
        
        assert user_id is not None
        
        # ユーザー取得（ログ出力されるはず）
        user = logged_database.get_user(user_id)
        assert user.name == user_data["name"]