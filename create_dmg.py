import os
import dmgbuild

# アプリケーション名
app_name = "PageSpeed Insights Analyzer"

# .appファイルのパス
app_path = f"/Applications/{app_name}.app"

# DMGの出力先
dmg_path = f"/Users/shoheishimizu/Python/pagespeed-insight-analyzer/dist/{app_name}.dmg"

# アイコンファイルのパス（.icnsファイル）
icon_path = "/Users/shoheishimizu/Python/pagespeed-insight-analyzer/pagespeed-insight-analyzer-app.icns"

# DMGの設定
dmg_settings = {
    'volume_name': app_name,
    'format': 'UDBZ',
    'size': '150M',
    'files': [app_path],
    'icon': icon_path,
    'icon_size': 80,
    'window_rect': ((100, 100), (500, 400)),
    'background': 'builtin-arrow',
    'icon_locations': {
        app_name: (250, 200),
    }
}

# DMGのビルド
dmgbuild.build_dmg(dmg_path, app_name, settings=dmg_settings)

print(f"DMGファイルが作成されました: {dmg_path}")