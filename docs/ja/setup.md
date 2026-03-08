# Lifegence Business -- セットアップガイド

[Frappe](https://frappeframework.com/) / [ERPNext](https://erpnext.com/) 向けのビジネス管理モジュール集です。

**ライセンス**: MIT -- [LICENSE](../../LICENSE) を参照

---

## 前提条件

| 要件 | バージョン |
|---|---|
| Python | 3.10 以上 |
| Frappe Framework | v15 以上 |
| ERPNext | v15 以上 |
| MariaDB / MySQL | 10.6 以上 |
| Node.js | 18 以上 |

動作可能な Frappe Bench 環境が必要です。未構築の場合は [Frappe インストールガイド](https://frappeframework.com/docs/user/en/installation) を参照してください。

---

## インストール

### 1. アプリのダウンロード

```bash
bench get-app https://github.com/lifegence/lifegence-business.git
```

### 2. サイトへのインストール

```bash
bench --site your-site install-app lifegence_business
```

### 3. マイグレーション実行

```bash
bench --site your-site migrate
```

### 4. アセットのビルド

```bash
bench build --app lifegence_business
```

---

## `after_install` で作成されるリソース

アプリインストール時に `after_install` フックにより、7モジュールのうち6モジュールが自動セットアップされます（契約管理はインストール時のセットアップ不要）。

### コンプライアンス

- **ロール**: Compliance Manager, Compliance User（`insert` で作成。フィクスチャではない）
- **権限**: Committee Report, Classification Category, Report Chunk, Indexing Log, Compliance Settings への Custom DocPerm
- **分類カテゴリ**: 3レイヤー39カテゴリ（A: 不正類型, B: 組織メカニズム, C: 組織文化）

### 与信管理

- **ロール**: Credit Manager, Credit Approver
- **カスタムフィールド**（既存 ERPNext DocType への追加）:
  - **Customer（取引先）**: リスクグレード, 与信ステータス, 反社チェック結果（折りたたみ可能な「与信管理」セクション）
  - **Sales Order（受注）**: 与信チェック合格, 与信チェック備考（折りたたみ可能な「与信チェック」セクション）
- **デフォルト設定**: 与信期間365日, 超過時自動ブロック, アラート閾値80%, 審査サイクル12ヶ月, グレード閾値 A(80)/B(60)/C(40)/D(20)

### 予算管理

- **ロール**: Budget Manager
- **デフォルト設定**: 会計年度開始月4月, 通貨JPY, 千円丸め, 承認ワークフロー有効, 差異閾値10%（警告）, 予測有効（線形法）

### ヘルプデスク

- **ロール**: Support Manager, Support Agent
- **デフォルトカテゴリ**: IT, HR（人事・労務）, 経理, 顧客サポート
- **デフォルトSLAポリシー**（「標準SLA」）: Low 24h/72h, Medium 8h/24h, High 4h/8h, Urgent 1h/4h, 営業時間 09:00-18:00

### DMS（文書管理）

- **ロール**: DMS Manager, DMS User
- **デフォルト保存ポリシー**: 法定7年保存, 法定10年保存, 永久保存, 3年保存

### 内部監査

- **ロール**: Audit Manager, Auditor, Risk Manager
- **デフォルト設定**: リスクマトリクス5x5, 審査サイクル90日, 自動リマインダー7日前, 日次期限超過チェック

---

## `after_migrate` で実行される処理

`bench migrate` 実行時に以下の冪等処理が実行されます:

- コンプライアンスロールと権限の確認・作成
- 39分類カテゴリのシード（既存はスキップ）
- `Report Chunk.content` への FULLTEXT インデックス作成（未作成時のみ）
- コンプライアンスサイドバー項目の設定
- 監査ロールの確認・作成

---

## ロール一覧

| ロール | モジュール | 作成元 |
|---|---|---|
| Compliance Manager | コンプライアンス | `after_install` / `after_migrate` |
| Compliance User | コンプライアンス | `after_install` / `after_migrate` |
| Credit Manager | 与信管理 | フィクスチャ |
| Credit Approver | 与信管理 | フィクスチャ |
| Budget Manager | 予算管理 | フィクスチャ |
| Support Manager | ヘルプデスク | フィクスチャ |
| Support Agent | ヘルプデスク | フィクスチャ |
| DMS Manager | 文書管理 | フィクスチャ |
| DMS User | 文書管理 | フィクスチャ |
| Audit Manager | 内部監査 | フィクスチャ + `after_migrate` |
| Auditor | 内部監査 | フィクスチャ + `after_migrate` |
| Risk Manager | 内部監査 | フィクスチャ + `after_migrate` |

---

## インストール後の設定

インストール後、各モジュールの設定を行います。以下の順序を推奨します。

### 1. 与信管理

**Credit Settings** 画面で以下を確認:

- デフォルト与信期間とアラート閾値
- グレード別スコア閾値
- 自動ブロック動作
- TDB/TSR API 認証情報（外部信用データ連携を使用する場合）

### 2. 予算管理

**Budget Settings** 画面で以下を確認:

- 会計年度開始月（デフォルト: 4月）
- 通貨・端数処理設定
- 承認ワークフロー設定
- 差異閾値とアクション
- 予測手法とスケジュール

### 3. ヘルプデスク

プリインストールされたカテゴリとSLAポリシーを確認:

- **HD Category** リスト: 必要に応じてカテゴリを追加・変更
- **HD SLA Policy**: 応答時間・解決時間をサービスレベルに合わせて調整

### 4. DMS（文書管理）

**DMS Settings** 画面で以下を設定:

- バージョン管理・アクセスログのオン/オフ
- 電子帳簿保存法対応設定
- デフォルト保存期間・最大ファイルサイズ

### 5. コンプライアンス（任意）

コンプライアンスモジュールの RAG 検索機能を使用する場合、**Compliance Settings** で以下を設定:

- Gemini API キーとモデル
- Qdrant 接続URLとコレクション名
- チャンキングパラメータ（チャンクサイズ、オーバーラップ）
- 検索重みデフォルト（ベクトル検索 vs 全文検索）

### 6. 契約管理（任意）

電子署名連携を使用する場合:

- **E-Signature Provider Settings** で CloudSign または DocuSign の認証情報を登録
- **Contract Approval Rule** で自動承認ルーティングルールを設定

### 7. 内部監査

**Audit Settings** 画面で以下を確認:

- J-SOX 有効化（必要な場合）
- リスクマトリクスサイズと審査サイクル
- リマインダー・期限超過チェック設定

---

## オプションの外部依存サービス

基本機能には不要ですが、以下のサービスで追加機能が利用可能になります。

| サービス | モジュール | 用途 | 設定場所 |
|---|---|---|---|
| Qdrant | コンプライアンス | RAG検索用ベクトルDB | Compliance Settings |
| Google Gemini API | コンプライアンス | テキスト埋め込み・AI分類 | Compliance Settings |
| CloudSign | 契約管理 | 日本向け電子署名サービス | E-Signature Provider Settings |
| DocuSign | 契約管理 | 国際電子署名サービス | E-Signature Provider Settings |
| TDB API | 与信管理 | 帝国データバンク信用情報 | Credit Settings |
| TSR API | 与信管理 | 東京商工リサーチ信用情報 | Credit Settings |

---

## アップデート

### 標準アップデート

```bash
cd /path/to/frappe-bench
bench update --pull --apps lifegence_business
bench --site your-site migrate
bench build --app lifegence_business
```

### アプリのみのアップデート（Frappe/ERPNext は更新しない場合）

```bash
cd /path/to/frappe-bench/apps/lifegence_business
git pull
cd /path/to/frappe-bench
bench --site your-site migrate
bench build --app lifegence_business
```

---

## アンインストール

```bash
bench --site your-site uninstall-app lifegence_business
bench remove-app lifegence_business
```

注意: 与信管理モジュールが Customer および Sales Order に追加したカスタムフィールドは、アンインストール時に自動削除されません。不要な場合は **フォームのカスタマイズ** から手動で削除してください。

---

## 関連ドキュメント

- [モジュールリファレンス](modules.md) -- 全7モジュールの詳細ドキュメント
- [設定リファレンス](configuration.md) -- 設定、ロール、外部サービス
- [トラブルシューティング](troubleshooting.md) -- よくある問題と解決策
