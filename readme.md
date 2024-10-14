# PageSpeed Insights Analyzer

PageSpeed Insights Analyzer は、複数のウェブサイトのパフォーマンスを自動的に分析し、結果を Google Spreadsheets に記録する MacOS 用デスクトップアプリケーションです。

## 特徴

-   複数のウェブサイトの PageSpeed Insights スコアを一括で取得
-   モバイルとデスクトップの両方のスコアを分析
-   結果を Google Spreadsheets に自動記録
-   ユーザーフレンドリーなグラフィカルインターフェース
-   設定の保存と読み込み機能

## インストール

1. 最新の`PageSpeedInsightsAnalyzer.dmg`ファイルをダウンロードします。

2. ダウンロードした DMG ファイルをダブルクリックして開きます。

3. アプリケーションアイコンを Applications フォルダにドラッグ＆ドロップしてインストールします。

4. インストール後、Launchpad または Applications フォルダから「PageSpeed Insights Analyzer」を起動できます。

## 使用準備

1. Google Cloud Platform で新しいプロジェクトを作成し、PageSpeed Insights API と Google Sheets API を有効にします。

2. サービスアカウントを作成し、JSON キーファイルをダウンロードします。

3. Google Sheets で API キーを取得します。

## 使用方法

1. アプリケーションを起動します。

2. 以下の情報を入力します：

    - PageSpeed Insights API キー
    - サービスアカウントの JSON キーファイルのパス
    - 結果を記録する Google Spreadsheet の URL
    - 使用するワークシート名

3. 分析したいウェブサイトの情報を追加します：

    - サイト名
    - URL
    - モバイルスコアを記録するスプレッドシートの列
    - デスクトップスコアを記録するスプレッドシートの列

4. 「分析開始」ボタンをクリックして分析を実行します。

5. 結果がアプリケーション内に表示され、指定した Google Spreadsheet に記録されます。

## 注意事項

-   Google Cloud Platform の API クォータに注意してください。
-   スプレッドシートへの書き込み権限があることを確認してください。
-   このアプリケーションは MacOS 用に設計されています。他の OS での動作は保証されません。
