# WebClass Scraper

名城大学のWebClassシステムに自動ログインし，履修している科目のコンテンツ一覧を抽出してJSONファイルとして保存するPythonスクリプトです．

✨✨[ktsgsgさん](https://github.com/ktsgsg)の，[webclass_kadai_getter](https://github.com/ktsgsg/webclass_kadai_getter)をフォークし参考にさせていただきました．素晴らしいアイデアをありがとうございます✨✨

機能としてはフォーク元より少ないですが，文字データを取得することに絞りリファクタリングをしたことで，今後の開発で課題取得をする際に使いやすいテンプレートとしました．

## 概要

このツールは，SSO（シングルサインオン）認証を通じて，WebClassのSAML認証を経てログインセッションを確立します．その後，ダッシュボードから履修科目一覧を取得し，各科目のページから，配布資料，課題，テストなどの情報を解析・抽出します．

抽出されたデータは，科目ごとに `{科目名}.json` という形式で `temp` フォルダに保存されます．

## 機能

* SSOおよびSAML認証の自動化
* セキュアな資格情報（ID/パスワード）の保存（`cryptography`による暗号化）
* 科目一覧の自動取得
* `ThreadPoolExecutor` を利用した並列処理による高速なコンテンツ抽出
* 科目ごとのコンテンツ情報をJSONファイルとして出力

## 使い方

まず，このスクリプトを起動したいディレクトリに移動します．その後，以下のコマンドでcloneをした後，ディレクトリを移動してください．

```bash
git clone https://github.com/hochu-shunsuke/webclass_kadai_getter
cd webclass_kadai_getter
```

## 必要なライブラリのインストール

以下のコマンドを実行し，仮想環境を作成してください．

```bash
python -m venv venv
```

その後，ご自身のOS/シェルに合わせて，以下のいずれかのコマンドで仮想環境をアクティベートしてください．

```bash
# macOS/Linux (Bash, Zshなど)
source venv/bin/activate

# Windows (PowerShell)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
.venv\Scripts\activate.ps1

# Windows (コマンドプロンプト)
.venv\Scripts\activate.bat
```

以下のコマンドを実行し，必要なPythonライブラリをインストールしてください．

```bash
pip install -r requirements.txt
```

## 実行方法

1. 上記ライブラリをインストールします．

2. ターミナルで `main.py` を実行します．

  ```bash
  python main.py
  # または
  python3 main.py
  ```

3. *初回実行時:*

* `userid`（学籍番号）と `password`（パスワード）の入力を求められます．
* 入力された資格情報は暗号化され，以下の2ファイルに保存されます．
  * `key.key`: 暗号化キー
  * `userdata.txt`: 暗号化された資格情報
* **次回以降**は，これらのファイルから資格情報が自動で読み込まれるため，再入力は不要です

4. **実行後:**

* `temp` フォルダが作成され，その中に科目ごとのJSONファイルが保存されます．

```txt
.
├── main.py
├── settings.py
├── webclass_client.py
├── parser.py
├── key.key           <-- 自動生成
├── userdata.txt      <-- 自動生成
└── temp/             <-- 自動生成
    ├── 〇〇学.json
    ├── △△論.json
    └── ...
```

## ファイル構成

* **`main.py`**

  * メインの実行スクリプト．
  * 並列処理（スレッドプール）を管理し，各科目の取得・解析プロセス全体を統括します．

* **`webclass_client.py`**

  * 認証クライアント．
  * SSOトークンの取得，SAML認証，`requests.Session` の管理など，WebClassへのログインと通信に関するすべてのロジックを担当します．

* **`settings.py`**

  * 資格情報モジュール．
  * `userid` と `password` の入力を受け付け，`cryptography` を使用して安全に暗号化・復号，ファイルへの保存・読み込みを行います．

* **`parser.py`**

  * HTML解析モジュール．
  * `BeautifulSoup` を使用し，各科目のコンテンツページのHTML構造を解析して，必要な情報を辞書型（dict）に変換します．

## 注意事項

* WebClassのHTML構造や認証フローが大学側で変更された場合，スクリプト（特に `parser.py` と `webclass_client.py`）が動作しなくなる可能性があります．
* `key.key` と `userdata.txt` には重要な情報が含まれています．これらのファイルを他人に共有しないでください．
* スクリプトの実行によって生じたいかなる問題についても，作成者は責任を負いません．自己責任で利用してください．
