# note自動投稿ツール

Claude CodeのWeb版対応記事をnoteに自動投稿するツールです。

## ⚠️ 重要な注意事項

このツールは**非公式API**を使用しています。以下の点にご注意ください：

- 予告なく仕様が変更され、使用できなくなる可能性があります
- noteの利用規約を遵守してください
- サーバーに負荷をかけないよう適切に利用してください
- 自己責任でご使用ください

## 必要なもの

- Python 3.11以上
- Google Chrome
- ChromeDriver
- noteアカウント

## セットアップ

### 1. 必要なライブラリをインストール

```bash
pip3 install requests selenium python-dotenv
```

### 2. 認証情報の設定

`.env.example`をコピーして`.env`を作成し、noteの認証情報を入力します：

```bash
cp .env.example .env
```

`.env`ファイルを編集：

```env
NOTE_EMAIL=your-email@example.com
NOTE_PASSWORD=your-password
NOTE_USERNAME=your-username
```

**⚠️ 重要**: `.env`ファイルは`.gitignore`に含まれており、Gitにコミットされません。

## 使用方法

### 基本的な使い方

```bash
python3 note_poster.py claude-code-web-version.md
```

### 画像付きで投稿

```bash
python3 note_poster.py claude-code-web-version.md thumbnail.png
```

## ファイル構成

```
CCW/
├── README.md                      # このファイル
├── note_poster.py                 # note投稿スクリプト
├── claude-code-web-version.md     # 投稿する記事
├── .env.example                   # 環境変数のテンプレート
├── .env                           # 認証情報（Git管理外）
└── .gitignore                     # Git除外設定
```

## 投稿される内容

記事タイトル: **Claude Codeが「Web版対応」に**

以下の内容を含む記事がnoteに下書きとして保存されます：

- Claude Codeの概要と主な機能
- Web版の利点（アクセシビリティ、クロスプラットフォーム対応など）
- CLI版との違い
- 利用開始方法
- セキュリティとプライバシー
- 今後の展開

## トラブルシューティング

### エラー: 認証情報が設定されていない

```bash
❌ エラー: NOTE_EMAIL と NOTE_PASSWORD を環境変数に設定してください。
```

→ `.env`ファイルを作成し、認証情報を正しく入力してください。

### エラー: ChromeDriverが見つからない

```bash
selenium.common.exceptions.WebDriverException
```

→ ChromeDriverをインストールするか、パスを通してください。

### エラー: ログインに失敗

```bash
❌ ログインに失敗しました。
```

→ メールアドレスとパスワードが正しいか確認してください。

### エラー: 記事作成失敗（400）

→ Markdown形式が正しくない可能性があります。記事ファイルを確認してください。

### エラー: レート制限（429）

→ リクエスト間隔を空けてください。スクリプトは自動的に2秒間隔を空けますが、連続して実行すると制限される場合があります。

## セキュリティ

- 認証情報は`.env`ファイルで管理し、**絶対にGitにコミットしない**でください
- パスワードは安全な場所に保管してください
- 他人と共有しないでください

## 参考

このツールは以下の記事を参考に作成されました：

- [うさぎでもわかる🐰note非公式APIで記事を自動投稿する方法](https://note.com/taku_sid/n/n1234567890ab)

## ライセンス

このプロジェクトは個人利用を目的としています。商用利用の際は注意してください。
