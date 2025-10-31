#!/usr/bin/env python3
"""
note自動投稿スクリプト
⚠️ 非公式APIを使用しています。予告なく動作しなくなる可能性があります。
"""

import os
import re
import sys
import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()


def markdown_to_html(markdown_text):
    """簡易的なMarkdown→HTML変換"""
    html = markdown_text

    # 見出し（### -> h3, ## -> h2, # -> h1の順番で処理）
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # リスト
    html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)

    # 強調
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

    # コードブロック（```で囲まれた部分）
    html = re.sub(r'```(.+?)```', r'<pre><code>\1</code></pre>', html, flags=re.DOTALL)
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)

    # 段落（空行で区切られた部分）
    paragraphs = html.split('\n\n')
    html = '\n'.join([f'<p>{p}</p>' if not p.startswith('<') else p for p in paragraphs])

    return html


def get_note_cookies(email, password):
    """noteにログインしてCookieを取得"""
    print("🔐 noteにログイン中...")

    # Chromeオプションの設定（ヘッドレスモード）
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')

    # webdriver-managerを使用して自動的にChromeDriverを取得
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # ログインページにアクセス
        driver.get('https://note.com/login')

        # メールアドレスとパスワードを入力
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        email_input.send_keys(email)

        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(password)

        # ログインボタンをクリック
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()

        # ログイン完了を待つ
        time.sleep(5)

        # Cookieを取得
        cookies = driver.get_cookies()

        # Cookie辞書に変換
        cookie_dict = {}
        for cookie in cookies:
            cookie_dict[cookie['name']] = cookie['value']

        print("✅ ログイン成功！")
        return cookie_dict

    except Exception as e:
        print(f"❌ ログインエラー: {e}")
        return None
    finally:
        driver.quit()


def create_article(cookies, title, markdown_content):
    """新しい記事を作成"""
    print("📝 記事を作成中...")

    # MarkdownをHTMLに変換
    html_content = markdown_to_html(markdown_content)

    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    data = {
        'body': html_content,
        'name': title,
        'template_key': None,
    }

    try:
        response = requests.post(
            'https://note.com/api/v1/text_notes',
            cookies=cookies,
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            article_id = result['data']['id']
            article_key = result['data']['key']
            print(f"✅ 記事作成成功！ID: {article_id}")
            return article_id, article_key
        else:
            print(f"❌ 記事作成失敗: {response.status_code}")
            print(f"レスポンス: {response.text}")
            return None, None
    except Exception as e:
        print(f"❌ 記事作成エラー: {e}")
        return None, None


def upload_image(cookies, image_path):
    """画像をアップロード"""
    print(f"🖼️  画像をアップロード中: {image_path}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    try:
        with open(image_path, 'rb') as f:
            files = {'file': f}

            response = requests.post(
                'https://note.com/api/v1/upload_image',
                cookies=cookies,
                headers=headers,
                files=files,
                timeout=60
            )

        if response.status_code == 200:
            result = response.json()
            image_key = result['data']['key']
            image_url = result['data']['url']
            print(f"✅ 画像アップロード成功！")
            return image_key, image_url
        else:
            print(f"❌ 画像アップロード失敗: {response.status_code}")
            return None, None
    except FileNotFoundError:
        print(f"❌ 画像ファイルが見つかりません: {image_path}")
        return None, None
    except Exception as e:
        print(f"❌ 画像アップロードエラー: {e}")
        return None, None


def update_article_draft(cookies, article_id, title, markdown_content, image_key=None):
    """記事を更新して下書きとして保存"""
    print("💾 記事を下書き保存中...")

    html_content = markdown_to_html(markdown_content)

    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    data = {
        'body': html_content,
        'name': title,
        'status': 'draft',  # 下書きとして保存
    }

    # アイキャッチ画像がある場合は追加
    if image_key:
        data['eyecatch_image_key'] = image_key

    try:
        response = requests.put(
            f'https://note.com/api/v1/text_notes/{article_id}',
            cookies=cookies,
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            print("✅ 記事の下書き保存成功！")
            return True
        else:
            print(f"❌ 記事の更新失敗: {response.status_code}")
            print(f"レスポンス: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 記事更新エラー: {e}")
        return False


def post_to_note(email, password, title, markdown_content, image_path=None, username=None):
    """noteに記事を投稿する完全な関数"""
    print("\n" + "="*60)
    print("📮 note自動投稿を開始します")
    print("="*60 + "\n")

    # ログイン
    cookies = get_note_cookies(email, password)
    if not cookies:
        print("\n❌ ログインに失敗しました。")
        return False

    # レート制限を考慮
    time.sleep(2)

    # 記事作成
    article_id, article_key = create_article(cookies, title, markdown_content)
    if not article_id:
        print("\n❌ 記事の作成に失敗しました。")
        return False

    # レート制限を考慮
    time.sleep(2)

    # 画像アップロード（オプション）
    image_key = None
    if image_path and os.path.exists(image_path):
        image_key, image_url = upload_image(cookies, image_path)
        time.sleep(2)

    # 記事の下書き保存
    success = update_article_draft(
        cookies,
        article_id,
        title,
        markdown_content,
        image_key
    )

    if success:
        print("\n" + "="*60)
        print("✅ 投稿完了！")
        print("="*60)
        if username:
            print(f"\n📄 記事URL: https://note.com/{username}/n/{article_key}")
        else:
            print(f"\n📄 記事KEY: {article_key}")
            print("   ※ noteのダッシュボードから確認してください")
        print("\n")
    else:
        print("\n❌ 投稿に失敗しました。")

    return success


def main():
    """メイン関数"""
    # 環境変数から認証情報を取得
    email = os.getenv('NOTE_EMAIL')
    password = os.getenv('NOTE_PASSWORD')
    username = os.getenv('NOTE_USERNAME')

    # コマンドライン引数から記事ファイルを取得
    if len(sys.argv) < 2:
        print("使用方法: python3 note_poster.py <markdown_file> [image_file]")
        print("\n例:")
        print("  python3 note_poster.py article.md")
        print("  python3 note_poster.py article.md thumbnail.png")
        sys.exit(1)

    article_file = sys.argv[1]
    image_file = sys.argv[2] if len(sys.argv) > 2 else None

    # 認証情報のチェック
    if not email or not password:
        print("❌ エラー: NOTE_EMAIL と NOTE_PASSWORD を環境変数に設定してください。")
        print("\n.envファイルに以下のように記述してください:")
        print("NOTE_EMAIL=your-email@example.com")
        print("NOTE_PASSWORD=your-password")
        print("NOTE_USERNAME=your-username  # オプション")
        sys.exit(1)

    # 記事ファイルの読み込み
    try:
        with open(article_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # タイトルを抽出（最初の# 見出し）
        title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        if title_match:
            title = title_match.group(1)
        else:
            title = os.path.splitext(os.path.basename(article_file))[0]

        print(f"📄 記事タイトル: {title}")
        print(f"📝 記事ファイル: {article_file}")
        if image_file:
            print(f"🖼️  画像ファイル: {image_file}")

        # 投稿実行
        success = post_to_note(email, password, title, content, image_file, username)

        sys.exit(0 if success else 1)

    except FileNotFoundError:
        print(f"❌ エラー: ファイルが見つかりません: {article_file}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
