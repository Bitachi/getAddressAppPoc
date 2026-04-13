# 現在地住所表示アプリ - セットアップ手順

## 構成

```
スマホブラウザ
    ↓ index.html を取得
  S3（静的ウェブホスティング）
    ↓ POST /geocode（緯度経度）
  API Gateway
    ↓
  Lambda（lambda_function.py）
    ↓
  Google Maps Geocoding API
    ↓ 日本語住所
  スマホ画面に表示
```

---

## 1. Lambda のセットアップ

### 1-1. 関数作成
- ランタイム: `Python 3.12`
- アーキテクチャ: `x86_64`
- 実行ロール: 新しいロールを作成（基本的なLambdaアクセス権限）

### 1-2. コードのデプロイ
`lambda_function.py` をそのままコピー＆ペースト or zipでアップロード

### 1-3. 環境変数の設定（重要）
「設定」→「環境変数」から以下を追加：

| キー | 値 |
|---|---|
| `GOOGLE_MAPS_API_KEY` | GCPで発行したGeocoding APIキー |

> ⚠️ APIキーはコードに直書きしないこと。環境変数で管理する。

### 1-4. タイムアウト設定
「設定」→「一般設定」→ タイムアウトを `15秒` に変更（デフォルト3秒だとGeocoding APIが間に合わない場合あり）

---

## 2. API Gateway のセットアップ

### 2-1. APIの作成
- タイプ: **HTTP API**（REST APIより設定がシンプル）
- 名前: `geocode-api`（任意）

### 2-2. ルートの設定
| メソッド | パス |
|---|---|
| POST | /geocode |

> ⚠️ OPTIONSルートは**作成しない**。HTTP APIはCORS設定が有効であればOPTIONSを自動処理するため、OPTIONSルートにLambdaをアタッチすると競合して400エラーになる。

### 2-3. インテグレーションの設定
- インテグレーションタイプ: `Lambda`
- Lambda関数: 作成した関数を選択

### 2-4. CORSの設定
「CORS」から以下を設定：

| 項目 | 値 |
|---|---|
| Access-Control-Allow-Origin | `*`（本番はS3のURLに絞る） |
| Access-Control-Allow-Headers | `content-type` |
| Access-Control-Allow-Methods | `POST` |
| Access-Control-Max-Age | `300` |

> OPTIONSはAPI Gatewayが自動処理するため、Allow-Methodsに含める必要はない。

### 2-5. デプロイ
- 「自動デプロイを有効にする」を選択するとステージ名は **`$default`** になる
- デプロイ後に表示されるエンドポイントURLをメモ

例: `https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com`

---

## 3. index.html の修正

`index.html` の以下の行を書き換える：

```javascript
// 変更前
const API_ENDPOINT = 'https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod/geocode';

// 変更後（自動デプロイ・$defaultステージの場合）
const API_ENDPOINT = 'https://実際のID.execute-api.ap-northeast-1.amazonaws.com/geocode';
//                                                                               ↑ ステージ名なし
```

> ⚠️ 自動デプロイ（$defaultステージ）の場合、URLにステージ名は含まれない。手動デプロイで `prod` ステージを作った場合のみ `/prod/geocode` になる。

---

## 4. S3 のセットアップ

### 4-1. バケット作成
- バケット名: 任意（例: `keibikai-location-app`）
- リージョン: `ap-northeast-1`（東京）
- **「パブリックアクセスをすべてブロック」→ チェックを外す**

### 4-2. 静的ウェブホスティングの有効化
「プロパティ」→「静的ウェブサイトホスティング」→「有効にする」
- インデックスドキュメント: `index.html`

### 4-3. バケットポリシーの設定
「アクセス許可」→「バケットポリシー」に以下を設定（バケット名を変更）：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::バケット名/*"
    }
  ]
}
```

### 4-4. ファイルのアップロード
`index.html` をS3にアップロード

### 4-5. URLの確認
「プロパティ」→「静的ウェブサイトホスティング」→ バケットウェブサイトエンドポイントのURLをスマホで開く

---

## 5. Google Maps APIキーの設定

GCPコンソールで以下を有効化：
- **Geocoding API**

APIキーの制限（推奨）：
- 「APIの制限」→ `Geocoding API` のみに絞る
- 「アプリケーションの制限」→ IPアドレス制限 or 制限なし（LambdaはIPが変動するため）

---

## 動作確認

1. S3のエンドポイントURLをスマホで開く
2. 「現在地の住所を取得」ボタンを押す
3. ブラウザのGPS許可を「許可」する
4. 住所が表示されれば完了

---

## トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| GPS取得が拒否される | ブラウザのGPS許可がオフ | ブラウザ設定から位置情報を許可 |
| 通信エラーになる | API GatewayのURLが間違い | `API_ENDPOINT` の値を確認 |
| CORSエラー・400になる | OPTIONSルートにLambdaをアタッチしている | OPTIONSルートを削除する |
| CORSエラーになる | API GatewayのCORS設定漏れ | 手順2-4を再確認 |
| 住所が英語になる | `language=ja` が効いていない | Lambda環境変数とコードを確認 |
| Lambdaがタイムアウト | タイムアウト設定が短い | 手順1-4でタイムアウトを15秒に変更 |