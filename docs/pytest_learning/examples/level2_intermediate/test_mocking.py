"""
Level 2: Intermediate - モッキングの基本と実践

このファイルでは unittest.mock を使ったモッキングについて学びます。
- Mock と MagicMock の使い方
- patch デコレータの活用
- 外部依存のモッキング
- アサーションによる呼び出し確認

実行方法:
pytest examples/level2_intermediate/test_mocking.py -v
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
import requests
import json
from datetime import datetime


# テスト対象のクラス（外部依存を含む）
class WeatherService:
    """天気情報サービス"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.weather.com"
    
    def get_weather(self, city):
        """指定した都市の天気情報を取得"""
        url = f"{self.base_url}/weather"
        params = {
            "city": city,
            "key": self.api_key
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return {
            "city": data["city"],
            "temperature": data["temperature"],
            "condition": data["condition"],
            "timestamp": datetime.now().isoformat()
        }


class EmailNotifier:
    """メール通知サービス"""
    
    def __init__(self, smtp_server, username, password):
        self.smtp_server = smtp_server
        self.username = username
        self.password = password
    
    def send_email(self, to_address, subject, body):
        """メールを送信"""
        # 実際の実装では smtplib を使用
        print(f"Sending email to {to_address}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        return {"status": "sent", "message_id": "12345"}


class ReportGenerator:
    """レポート生成クラス"""
    
    def __init__(self, weather_service, email_notifier):
        self.weather_service = weather_service
        self.email_notifier = email_notifier
    
    def generate_weather_report(self, cities, send_email=False):
        """天気レポートを生成"""
        report = {"generated_at": datetime.now().isoformat(), "cities": []}
        
        for city in cities:
            try:
                weather = self.weather_service.get_weather(city)
                report["cities"].append(weather)
            except Exception as e:
                report["cities"].append({
                    "city": city,
                    "error": str(e)
                })
        
        if send_email:
            self._send_report_email(report)
        
        return report
    
    def _send_report_email(self, report):
        """レポートをメールで送信"""
        subject = f"天気レポート - {len(report['cities'])}都市"
        body = self._format_report(report)
        
        return self.email_notifier.send_email(
            "admin@example.com",
            subject,
            body
        )
    
    def _format_report(self, report):
        """レポートをフォーマット"""
        lines = [f"生成日時: {report['generated_at']}", ""]
        
        for city_data in report["cities"]:
            if "error" in city_data:
                lines.append(f"❌ {city_data['city']}: {city_data['error']}")
            else:
                lines.append(f"✅ {city_data['city']}: {city_data['temperature']}°C, {city_data['condition']}")
        
        return "\n".join(lines)


class FileLogger:
    """ファイルログ出力クラス"""
    
    def __init__(self, log_file):
        self.log_file = log_file
    
    def log(self, level, message):
        """ログを出力"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    
    def log_info(self, message):
        self.log("INFO", message)
    
    def log_error(self, message):
        self.log("ERROR", message)


# ここからテストコード

class TestBasicMocking:
    """基本的なモッキングのテスト"""
    
    def test_simple_mock_creation(self):
        """シンプルなMockオブジェクトの作成"""
        # Mockオブジェクトを作成
        mock_service = Mock()
        
        # 戻り値を設定
        mock_service.get_data.return_value = {"result": "success"}
        
        # モックを呼び出し
        result = mock_service.get_data()
        
        # 戻り値の確認
        assert result == {"result": "success"}
        
        # 呼び出されたことを確認
        mock_service.get_data.assert_called_once()
    
    def test_mock_with_side_effect(self):
        """side_effectを使ったMock"""
        mock_service = Mock()
        
        # 例外を発生させる設定
        mock_service.risky_operation.side_effect = ConnectionError("接続エラー")
        
        # 例外が発生することを確認
        with pytest.raises(ConnectionError) as exc_info:
            mock_service.risky_operation()
        
        assert "接続エラー" in str(exc_info.value)
        mock_service.risky_operation.assert_called_once()
    
    def test_mock_call_arguments(self):
        """Mockの呼び出し引数確認"""
        mock_service = Mock()
        mock_service.process_data.return_value = "processed"
        
        # 引数付きで呼び出し
        result = mock_service.process_data("input", format="json")
        
        # 戻り値確認
        assert result == "processed"
        
        # 呼び出し引数確認
        mock_service.process_data.assert_called_once_with("input", format="json")


class TestWeatherServiceMocking:
    """WeatherServiceのモッキングテスト"""
    
    @patch('requests.get')
    def test_get_weather_success(self, mock_get):
        """正常な天気情報取得のテスト"""
        # requests.get のモックレスポンスを設定
        mock_response = Mock()
        mock_response.json.return_value = {
            "city": "東京",
            "temperature": 25,
            "condition": "晴れ"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # テスト実行
        service = WeatherService("test-api-key")
        result = service.get_weather("東京")
        
        # 結果確認
        assert result["city"] == "東京"
        assert result["temperature"] == 25
        assert result["condition"] == "晴れ"
        assert "timestamp" in result
        
        # API呼び出し確認
        mock_get.assert_called_once_with(
            "https://api.weather.com/weather",
            params={"city": "東京", "key": "test-api-key"}
        )
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()
    
    @patch('requests.get')
    def test_get_weather_api_error(self, mock_get):
        """API エラーのテスト"""
        # requests.get でエラーが発生する設定
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        service = WeatherService("test-api-key")
        
        # エラーが発生することを確認
        with pytest.raises(requests.exceptions.HTTPError):
            service.get_weather("存在しない都市")
        
        # API が呼び出されたことを確認
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


class TestReportGeneratorMocking:
    """ReportGeneratorのモッキングテスト"""
    
    def test_generate_weather_report_success(self):
        """正常なレポート生成のテスト"""
        # 依存サービスをモック化
        mock_weather_service = Mock()
        mock_email_notifier = Mock()
        
        # weather_service のモック設定
        mock_weather_service.get_weather.side_effect = [
            {"city": "東京", "temperature": 25, "condition": "晴れ"},
            {"city": "大阪", "temperature": 28, "condition": "曇り"}
        ]
        
        # ReportGenerator のテスト
        generator = ReportGenerator(mock_weather_service, mock_email_notifier)
        result = generator.generate_weather_report(["東京", "大阪"])
        
        # 結果確認
        assert len(result["cities"]) == 2
        assert result["cities"][0]["city"] == "東京"
        assert result["cities"][1]["city"] == "大阪"
        assert "generated_at" in result
        
        # サービス呼び出し確認
        assert mock_weather_service.get_weather.call_count == 2
        mock_weather_service.get_weather.assert_any_call("東京")
        mock_weather_service.get_weather.assert_any_call("大阪")
        
        # メール送信は呼び出されていないことを確認
        mock_email_notifier.send_email.assert_not_called()
    
    def test_generate_weather_report_with_error(self):
        """エラーを含むレポート生成のテスト"""
        mock_weather_service = Mock()
        mock_email_notifier = Mock()
        
        # 一部の都市でエラーが発生する設定
        def weather_side_effect(city):
            if city == "東京":
                return {"city": "東京", "temperature": 25, "condition": "晴れ"}
            else:
                raise Exception("API接続エラー")
        
        mock_weather_service.get_weather.side_effect = weather_side_effect
        
        generator = ReportGenerator(mock_weather_service, mock_email_notifier)
        result = generator.generate_weather_report(["東京", "無効な都市"])
        
        # 結果確認
        assert len(result["cities"]) == 2
        assert result["cities"][0]["city"] == "東京"
        assert result["cities"][1]["city"] == "無効な都市"
        assert "error" in result["cities"][1]
        assert "API接続エラー" in result["cities"][1]["error"]
    
    @patch('examples.level2_intermediate.test_mocking.datetime')
    def test_generate_weather_report_with_email(self, mock_datetime):
        """メール送信ありのレポート生成テスト"""
        # datetime のモック設定
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-15T10:00:00"
        
        mock_weather_service = Mock()
        mock_email_notifier = Mock()
        
        mock_weather_service.get_weather.return_value = {
            "city": "東京",
            "temperature": 25,
            "condition": "晴れ"
        }
        
        mock_email_notifier.send_email.return_value = {
            "status": "sent",
            "message_id": "test123"
        }
        
        generator = ReportGenerator(mock_weather_service, mock_email_notifier)
        result = generator.generate_weather_report(["東京"], send_email=True)
        
        # レポート確認
        assert len(result["cities"]) == 1
        assert result["generated_at"] == "2024-01-15T10:00:00"
        
        # メール送信確認
        mock_email_notifier.send_email.assert_called_once()
        call_args = mock_email_notifier.send_email.call_args
        
        assert call_args[0][0] == "admin@example.com"  # to_address
        assert "天気レポート - 1都市" in call_args[0][1]  # subject
        assert "東京" in call_args[0][2]  # body


class TestFileLoggerMocking:
    """ファイル操作のモッキングテスト"""
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('examples.level2_intermediate.test_mocking.datetime')
    def test_log_info(self, mock_datetime, mock_file):
        """ログ出力のテスト"""
        # datetime のモック設定
        mock_datetime.now.return_value.strftime.return_value = "2024-01-15 10:00:00"
        
        logger = FileLogger("test.log")
        logger.log_info("テストメッセージ")
        
        # ファイルが正しく開かれたことを確認
        mock_file.assert_called_once_with("test.log", "a", encoding="utf-8")
        
        # 正しい内容が書き込まれたことを確認
        handle = mock_file()
        handle.write.assert_called_once_with("[2024-01-15 10:00:00] INFO: テストメッセージ\n")
    
    @patch('builtins.open', new_callable=mock_open)
    def test_log_error(self, mock_file):
        """エラーログ出力のテスト"""
        logger = FileLogger("error.log")
        logger.log_error("エラーが発生しました")
        
        # ファイル操作確認
        mock_file.assert_called_once_with("error.log", "a", encoding="utf-8")
        
        # 書き込み内容にERRORレベルが含まれていることを確認
        handle = mock_file()
        written_content = handle.write.call_args[0][0]
        assert "ERROR: エラーが発生しました" in written_content


class TestMockAssertions:
    """Mockのアサーション機能のテスト"""
    
    def test_call_count_assertions(self):
        """呼び出し回数のアサーション"""
        mock_service = Mock()
        
        # 複数回呼び出し
        mock_service.method("arg1")
        mock_service.method("arg2")
        mock_service.method("arg3")
        
        # 呼び出し回数確認
        assert mock_service.method.call_count == 3
        
        # 特定の引数での呼び出し確認
        mock_service.method.assert_any_call("arg1")
        mock_service.method.assert_any_call("arg2")
        mock_service.method.assert_any_call("arg3")
    
    def test_call_order_assertions(self):
        """呼び出し順序のアサーション"""
        mock_service = Mock()
        
        # 順序付きで呼び出し
        mock_service.step1()
        mock_service.step2()
        mock_service.step3()
        
        # 呼び出し順序確認
        expected_calls = [
            mock_service.step1(),
            mock_service.step2(),
            mock_service.step3()
        ]
        
        assert mock_service.mock_calls == expected_calls
    
    def test_not_called_assertion(self):
        """呼び出されていないことのアサーション"""
        mock_service = Mock()
        
        # 何も呼び出さない
        
        # 呼び出されていないことを確認
        mock_service.never_called_method.assert_not_called()


# fixture を使ったモックのテスト
@pytest.fixture
def mock_weather_service():
    """WeatherService のモックを提供するfixture"""
    mock = Mock()
    mock.get_weather.return_value = {
        "city": "テスト都市",
        "temperature": 22,
        "condition": "快晴"
    }
    return mock


@pytest.fixture
def mock_email_notifier():
    """EmailNotifier のモックを提供するfixture"""
    mock = Mock()
    mock.send_email.return_value = {"status": "sent", "message_id": "fixture123"}
    return mock


class TestWithMockFixtures:
    """fixture を使ったモックテスト"""
    
    def test_report_generator_with_fixtures(self, mock_weather_service, mock_email_notifier):
        """fixture を使ったReportGeneratorのテスト"""
        generator = ReportGenerator(mock_weather_service, mock_email_notifier)
        result = generator.generate_weather_report(["テスト都市"])
        
        assert len(result["cities"]) == 1
        assert result["cities"][0]["city"] == "テスト都市"
        assert result["cities"][0]["temperature"] == 22
        
        mock_weather_service.get_weather.assert_called_once_with("テスト都市")