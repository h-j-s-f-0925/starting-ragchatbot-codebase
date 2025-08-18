"""
Level 2: Intermediate - fixtureの基本と活用

このファイルでは pytest の重要な機能である fixture について学びます。
- fixture の基本的な使い方
- setup/teardown パターン
- fixture のスコープ
- データ準備と後片付け

実行方法:
pytest examples/level2_intermediate/test_fixtures.py -v
"""

import pytest
import tempfile
import os
from pathlib import Path


# テスト対象のクラス
class TodoList:
    """シンプルなTODOリストクラス"""
    
    def __init__(self):
        self.items = []
    
    def add_item(self, item):
        if not item.strip():
            raise ValueError("空のアイテムは追加できません")
        self.items.append({"text": item, "completed": False})
    
    def complete_item(self, index):
        if 0 <= index < len(self.items):
            self.items[index]["completed"] = True
        else:
            raise IndexError("無効なインデックスです")
    
    def get_items(self):
        return self.items.copy()
    
    def get_pending_count(self):
        return len([item for item in self.items if not item["completed"]])


class FileManager:
    """ファイル管理クラス"""
    
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    def create_file(self, filename, content=""):
        file_path = self.base_path / filename
        file_path.write_text(content, encoding='utf-8')
        return file_path
    
    def read_file(self, filename):
        file_path = self.base_path / filename
        if not file_path.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {filename}")
        return file_path.read_text(encoding='utf-8')
    
    def list_files(self):
        return [f.name for f in self.base_path.iterdir() if f.is_file()]


# ここからテストコード

# 基本的な fixture
@pytest.fixture
def empty_todo_list():
    """空のTODOリストを提供するfixture"""
    return TodoList()


@pytest.fixture
def sample_todo_list():
    """サンプルデータ入りのTODOリストを提供するfixture"""
    todo_list = TodoList()
    todo_list.add_item("買い物に行く")
    todo_list.add_item("レポートを書く")
    todo_list.add_item("映画を見る")
    return todo_list


# setup/teardown パターンの fixture
@pytest.fixture
def temp_directory():
    """一時ディレクトリを作成し、テスト後に削除するfixture"""
    # Setup: 一時ディレクトリを作成
    with tempfile.TemporaryDirectory() as tmp_dir:
        print(f"\n一時ディレクトリを作成しました: {tmp_dir}")
        yield tmp_dir
        # Teardown: with文を抜ける時に自動的に削除される
        print(f"\n一時ディレクトリを削除しました: {tmp_dir}")


@pytest.fixture
def file_manager(temp_directory):
    """FileManagerインスタンスを提供するfixture（temp_directoryに依存）"""
    manager = FileManager(temp_directory)
    yield manager
    # このfixtureはcleanupが必要ないが、必要に応じてここに記述


# スコープを指定したfixture
@pytest.fixture(scope="class")
def shared_todo_list():
    """クラス内で共有されるTODOリスト（class scope）"""
    print("\nクラススコープのTODOリストを作成")
    todo_list = TodoList()
    todo_list.add_item("共有アイテム1")
    todo_list.add_item("共有アイテム2")
    yield todo_list
    print("\nクラススコープのTODOリストを破棄")


# パラメータ化されたfixture
@pytest.fixture(params=["短いタスク", "これは少し長めのタスクの説明文です", "📝 絵文字付きタスク"])
def task_samples(request):
    """様々なタスクサンプルを提供するparametrized fixture"""
    return request.param


# ここからテストクラス

class TestTodoListBasicFixtures:
    """基本的なfixtureを使ったテスト"""
    
    def test_empty_list_creation(self, empty_todo_list):
        """空のリスト作成テスト"""
        assert len(empty_todo_list.get_items()) == 0
        assert empty_todo_list.get_pending_count() == 0
    
    def test_add_item_to_empty_list(self, empty_todo_list):
        """空のリストへのアイテム追加テスト"""
        empty_todo_list.add_item("新しいタスク")
        items = empty_todo_list.get_items()
        
        assert len(items) == 1
        assert items[0]["text"] == "新しいタスク"
        assert items[0]["completed"] == False
    
    def test_sample_list_contents(self, sample_todo_list):
        """サンプルリストの内容確認テスト"""
        items = sample_todo_list.get_items()
        
        assert len(items) == 3
        assert items[0]["text"] == "買い物に行く"
        assert items[1]["text"] == "レポートを書く"
        assert items[2]["text"] == "映画を見る"
        
        # 全て未完了であることを確認
        for item in items:
            assert item["completed"] == False
    
    def test_complete_item_in_sample_list(self, sample_todo_list):
        """サンプルリスト内のアイテム完了テスト"""
        # 最初のアイテムを完了
        sample_todo_list.complete_item(0)
        
        items = sample_todo_list.get_items()
        assert items[0]["completed"] == True
        assert items[1]["completed"] == False
        assert items[2]["completed"] == False
        
        # 未完了アイテム数を確認
        assert sample_todo_list.get_pending_count() == 2


class TestFileManagerWithFixtures:
    """fixtureを使ったファイル管理テスト"""
    
    def test_create_and_read_file(self, file_manager):
        """ファイル作成と読み取りテスト"""
        content = "これはテストファイルです。"
        filename = "test.txt"
        
        # ファイル作成
        created_path = file_manager.create_file(filename, content)
        assert created_path.exists()
        
        # ファイル読み取り
        read_content = file_manager.read_file(filename)
        assert read_content == content
    
    def test_list_files(self, file_manager):
        """ファイル一覧取得テスト"""
        # 複数のファイルを作成
        file_manager.create_file("file1.txt", "内容1")
        file_manager.create_file("file2.txt", "内容2")
        file_manager.create_file("file3.md", "# マークダウン")
        
        files = file_manager.list_files()
        assert len(files) == 3
        assert "file1.txt" in files
        assert "file2.txt" in files
        assert "file3.md" in files
    
    def test_read_nonexistent_file(self, file_manager):
        """存在しないファイルの読み取りテスト（エラーケース）"""
        with pytest.raises(FileNotFoundError) as exc_info:
            file_manager.read_file("存在しないファイル.txt")
        
        assert "ファイルが見つかりません" in str(exc_info.value)
    
    def test_file_isolation_between_tests(self, file_manager):
        """テスト間でのファイル分離確認"""
        # このテストで作成したファイルは他のテストに影響しない
        file_manager.create_file("isolated.txt", "分離されたファイル")
        
        files = file_manager.list_files()
        assert "isolated.txt" in files


class TestScopedFixtures:
    """スコープ指定fixtureのテスト"""
    
    def test_shared_list_first_test(self, shared_todo_list):
        """共有リストの最初のテスト"""
        items = shared_todo_list.get_items()
        assert len(items) == 2
        
        # アイテムを追加（他のテストにも影響する）
        shared_todo_list.add_item("テスト1で追加")
    
    def test_shared_list_second_test(self, shared_todo_list):
        """共有リストの二番目のテスト"""
        items = shared_todo_list.get_items()
        # 前のテストで追加したアイテムが残っている
        assert len(items) == 3
        assert any(item["text"] == "テスト1で追加" for item in items)
        
        # さらにアイテムを追加
        shared_todo_list.add_item("テスト2で追加")


class TestParametrizedFixtures:
    """パラメータ化fixtureのテスト"""
    
    def test_various_task_samples(self, empty_todo_list, task_samples):
        """様々なタスクサンプルのテスト"""
        # このテストは task_samples の各パラメータで実行される
        empty_todo_list.add_item(task_samples)
        
        items = empty_todo_list.get_items()
        assert len(items) == 1
        assert items[0]["text"] == task_samples
        assert len(task_samples) > 0  # 空でないことを確認


# fixtureを組み合わせたテスト
class TestFixtureCombination:
    """複数のfixtureを組み合わせたテスト"""
    
    def test_todo_list_and_file_manager(self, sample_todo_list, file_manager):
        """TODOリストとファイル管理の組み合わせテスト"""
        # TODOリストの内容をファイルに保存
        items = sample_todo_list.get_items()
        content = "\n".join([f"- {item['text']}" for item in items])
        
        file_manager.create_file("todo_list.md", content)
        
        # ファイルから読み取って確認
        saved_content = file_manager.read_file("todo_list.md")
        assert "買い物に行く" in saved_content
        assert "レポートを書く" in saved_content
        assert "映画を見る" in saved_content


# autouse fixture の例
@pytest.fixture(autouse=True)
def test_setup_and_teardown():
    """全てのテストで自動的に実行されるfixture"""
    print("\n=== テスト開始前の準備 ===")
    yield
    print("\n=== テスト終了後の片付け ===")


# fixture の依存関係の例
@pytest.fixture
def base_config():
    """基本設定fixture"""
    return {"debug": True, "timeout": 30}


@pytest.fixture
def extended_config(base_config):
    """拡張設定fixture（base_configに依存）"""
    config = base_config.copy()
    config.update({"max_items": 100, "auto_save": True})
    return config


def test_config_dependency(extended_config):
    """fixture依存関係のテスト"""
    assert extended_config["debug"] == True
    assert extended_config["timeout"] == 30
    assert extended_config["max_items"] == 100
    assert extended_config["auto_save"] == True