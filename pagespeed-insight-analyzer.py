import sys
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTextEdit,
                             QLineEdit, QLabel, QFileDialog, QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QMessageBox, QHeaderView, QSizePolicy)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QColor, QPalette
import requests
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os

class PageSpeedWorker(QThread):
    finished = pyqtSignal(str)
    progress = pyqtSignal(str)
    result = pyqtSignal(list)

    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        try:
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.config['credentials_path'], scope)
            client = gspread.authorize(creds)

            sheet = client.open_by_url(self.config['spreadsheet_url']).worksheet(self.config['worksheet_name'])

            get_url = 'https://www.googleapis.com/pagespeedonline/v5/runPagespeed'
            api_key = self.config['api_key']

            current_date = datetime.now().strftime("%Y-%m-%d")
            next_row = len(sheet.col_values(1)) + 1
            sheet.update_cell(next_row, 1, current_date)

            results = []

            for site in self.config['urls']:
                for strategy in ['mobile', 'desktop']:
                    start_time = time.time()
                    self.progress.emit(f"{site['name']} ({strategy})の分析を開始します...")
                    try:
                        payload = {'url': site['url'], 'strategy': strategy, 'key': api_key}
                        response = requests.get(get_url, params=payload)
                        response.raise_for_status()
                        result = response.json()

                        score = result['lighthouseResult']['categories']['performance']['score'] * 100

                        column = site['spColumn'] if strategy == 'mobile' else site['pcColumn']
                        sheet.update_cell(next_row, gspread.utils.a1_to_rowcol(column + '1')[1], score)

                        strategy_display = "モバイル" if strategy == "mobile" else "デスクトップ"
                        elapsed_time = time.time() - start_time
                        self.progress.emit(f"{site['name']} - {strategy_display}: スコア {score:.2f}, 所要時間 {elapsed_time:.2f}秒")
                        results.append([site['name'], strategy_display, score])
                        time.sleep(2)

                    except Exception as e:
                        elapsed_time = time.time() - start_time
                        self.progress.emit(f"{site['name']} ({strategy_display})のエラー: {str(e)}, 所要時間 {elapsed_time:.2f}秒")
                        results.append([site['name'], strategy_display, "エラー"])

            self.result.emit(results)
            self.finished.emit("データ収集と更新が完了しました。")

        except Exception as e:
            self.finished.emit(f"エラーが発生しました: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PageSpeed Insights Analyzer")
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QLabel {
                font-size: 14px;
                color: #333;
            }
            QLineEdit, QTextEdit, QTableWidget {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                font-size: 14px;
            }
            QLineEdit::placeholder {
                color: #aaa;
            }
            QPushButton {
                background-color: #0080F2;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                cursor: pointer;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #003d80;
            }
        """)

        self.config_file = os.path.join(os.path.expanduser("~"), ".pagespeed_analyzer_config.json")
        self.load_config()

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # タイトル
        title_label = QLabel("PageSpeed Insights Analyzer")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # 入力フィールド
        self.create_input_field(layout, "APIキー:", self.config['api_key'], "api_key_input", "APIキーを入力してください")
        self.create_file_input_field(layout, "認証情報ファイル:", self.config['credentials_path'], "cred_input", "認証情報ファイルのパスを入力または参照してください")
        self.create_input_field(layout, "スプレッドシートURL:", self.config['spreadsheet_url'], "sheet_input", "スプレッドシートのURLを入力してください（編集権限が必要です）")
        self.create_input_field(layout, "ワークシート名:", self.config['worksheet_name'], "worksheet_input", "ワークシート名を入力してください")

        # URL設定
        self.url_table = QTableWidget(0, 4)
        self.url_table.setHorizontalHeaderLabels(["サイト名", "URL", "モバイル列", "デスクトップ列"])
        self.url_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.url_table.setStyleSheet("QHeaderView::section { background-color: #f0f0f0; }")
        layout.addWidget(self.url_table)

        self.load_urls_to_table()

        url_buttons_layout = QHBoxLayout()
        self.add_url_button = self.create_button("URL追加", self.add_url_row)
        url_buttons_layout.addWidget(self.add_url_button)
        self.remove_url_button = self.create_button("URL削除", self.remove_url_row)
        url_buttons_layout.addWidget(self.remove_url_button)
        layout.addLayout(url_buttons_layout)

        # アクションボタン
        action_buttons_layout = QHBoxLayout()
        self.start_button = self.create_button("分析開始", self.start_analysis)
        action_buttons_layout.addWidget(self.start_button)
        self.save_config_button = self.create_button("設定を保存", self.save_config)
        action_buttons_layout.addWidget(self.save_config_button)
        layout.addLayout(action_buttons_layout)

        # ログエリア
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background-color: #f8f8f8; border: 1px solid #ddd;")
        layout.addWidget(self.log_area)

        # 結果テーブル
        self.results_table = QTableWidget(0, 3)
        self.results_table.setHorizontalHeaderLabels(["サイト", "デバイス", "スコア"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setStyleSheet("QHeaderView::section { background-color: #f0f0f0; }")
        layout.addWidget(self.results_table)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def create_input_field(self, layout, label_text, default_value, object_name, placeholder_text):
        input_layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        input_layout.addWidget(label)
        input_field = QLineEdit(default_value)
        input_field.setPlaceholderText(placeholder_text)
        setattr(self, object_name, input_field)
        input_layout.addWidget(input_field)
        layout.addLayout(input_layout)

    def create_file_input_field(self, layout, label_text, default_value, object_name, placeholder_text):
        input_layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        input_layout.addWidget(label)
        input_field = QLineEdit(default_value)
        input_field.setPlaceholderText(placeholder_text)
        setattr(self, object_name, input_field)
        input_layout.addWidget(input_field)
        browse_button = self.create_button("参照", self.browse_credentials)
        input_layout.addWidget(browse_button)
        layout.addLayout(input_layout)

    def create_button(self, text, callback):
        button = QPushButton(text)
        button.clicked.connect(callback)
        button.setCursor(Qt.PointingHandCursor)
        return button

    def browse_credentials(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "認証情報ファイルを選択", "", "JSONファイル (*.json)")
        if file_name:
            self.cred_input.setText(file_name)

    def add_url_row(self):
        row_position = self.url_table.rowCount()
        self.url_table.insertRow(row_position)

    def remove_url_row(self):
        current_row = self.url_table.currentRow()
        if current_row > -1:
            self.url_table.removeRow(current_row)

    def start_analysis(self):
        self.update_config_from_ui()

        self.start_button.setEnabled(False)
        self.log_area.clear()
        self.results_table.setRowCount(0)

        self.worker = PageSpeedWorker(self.config)
        self.worker.progress.connect(self.update_log)
        self.worker.finished.connect(self.analysis_finished)
        self.worker.result.connect(self.update_results)
        self.worker.start()

    def update_log(self, message):
        self.log_area.append(message)

    def analysis_finished(self, message):
        self.log_area.append(message)
        self.start_button.setEnabled(True)

    def update_results(self, results):
        self.results_table.setRowCount(len(results))
        for i, result in enumerate(results):
            self.results_table.setItem(i, 0, QTableWidgetItem(result[0]))
            self.results_table.setItem(i, 1, QTableWidgetItem(result[1]))
            self.results_table.setItem(i, 2, QTableWidgetItem(str(result[2])))

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = {
                    'api_key': '',
                    'credentials_path': '',
                    'spreadsheet_url': '',
                    'worksheet_name': 'Sheet1',
                    'urls': []
                }
        except Exception as e:
            QMessageBox.warning(self, "設定読み込みエラー", f"設定の読み込み中にエラーが発生しました: {str(e)}")
            self.config = {
                'api_key': '',
                'credentials_path': '',
                'spreadsheet_url': '',
                'worksheet_name': 'Sheet1',
                'urls': []
            }

    def save_config(self):
        try:
            self.update_config_from_ui()
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f)
            QMessageBox.information(self, "設定保存", "設定が正常に保存されました。")
        except Exception as e:
            QMessageBox.critical(self, "設定保存エラー", f"設定の保存中にエラーが発生しました: {str(e)}")

    def update_config_from_ui(self):
        self.config['api_key'] = self.api_key_input.text()
        self.config['credentials_path'] = self.cred_input.text()
        self.config['spreadsheet_url'] = self.sheet_input.text()
        self.config['worksheet_name'] = self.worksheet_input.text()

        self.config['urls'] = []
        for row in range(self.url_table.rowCount()):
            self.config['urls'].append({
                'name': self.url_table.item(row, 0).text() if self.url_table.item(row, 0) else '',
                'url': self.url_table.item(row, 1).text() if self.url_table.item(row, 1) else '',
                'spColumn': self.url_table.item(row, 2).text() if self.url_table.item(row, 2) else '',
                'pcColumn': self.url_table.item(row, 3).text() if self.url_table.item(row, 3) else ''
            })

    def load_urls_to_table(self):
            self.url_table.setRowCount(len(self.config['urls']))
            for i, url_info in enumerate(self.config['urls']):
                self.url_table.setItem(i, 0, QTableWidgetItem(url_info['name']))
                self.url_table.setItem(i, 1, QTableWidgetItem(url_info['url']))
                self.url_table.setItem(i, 2, QTableWidgetItem(url_info['spColumn']))
                self.url_table.setItem(i, 3, QTableWidgetItem(url_info['pcColumn']))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # より現代的な外観のためにFusionスタイルを使用
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())