# Lifegence Business -- 設定リファレンス

全設定項目、ロール、外部サービス設定の包括的なリファレンスです。

---

## 目次

1. [Credit Settings（与信設定）](#credit-settings与信設定)
2. [Budget Settings（予算設定）](#budget-settings予算設定)
3. [DMS Settings（文書管理設定）](#dms-settings文書管理設定)
4. [Compliance Settings（コンプライアンス設定）](#compliance-settingsコンプライアンス設定)
5. [Audit Settings（監査設定）](#audit-settings監査設定)
6. [E-Signature Provider Settings（電子署名プロバイダ設定）](#e-signature-provider-settings電子署名プロバイダ設定)
7. [ロール割り当て](#ロール割り当て)
8. [外部サービス設定](#外部サービス設定)

---

## Credit Settings（与信設定）

**ナビゲーション**: 与信管理 > Credit Settings

システム全体の与信管理動作を制御する Single DocType です。

### 一般設定

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| default_credit_period_days | Int | 365 | 新規与信枠のデフォルト有効期間（日） |
| auto_block_on_exceed | Check | 1 | 与信枠超過時に受注の提出をブロック |
| alert_threshold_pct | Int | 80 | アラートを発生させる与信枠使用率（%） |
| review_cycle_months | Int | 12 | 与信審査の必須サイクル（月） |
| send_review_reminder_days | Int | 30 | 審査期日の何日前にリマインダーを送信するか |

### グレードスコア閾値

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| grade_a_min_score | Int | 80 | グレードAの最低スコア |
| grade_b_min_score | Int | 60 | グレードBの最低スコア |
| grade_c_min_score | Int | 40 | グレードCの最低スコア |
| grade_d_min_score | Int | 20 | グレードDの最低スコア |

グレードDの閾値未満のスコアにはグレードEが割り当てられます。

### 外部API（オプション）

| フィールド | 型 | 説明 |
|---|---|---|
| tdb_api_url | Data | TDB（帝国データバンク）API エンドポイントURL |
| tdb_api_key | Password | TDB API 認証キー |
| tsr_api_url | Data | TSR（東京商工リサーチ）API エンドポイントURL |
| tsr_api_key | Password | TSR API 認証キー |

---

## Budget Settings（予算設定）

**ナビゲーション**: 予算管理 > Budget Settings

予算計画、承認、差異チェックを制御する Single DocType です。

### 会計年度設定

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| fiscal_year_start_month | Select | 4 | 会計年度の開始月（1-12） |
| budget_currency | Data | JPY | 予算金額のデフォルト通貨 |
| amount_rounding | Select | 千円 | 表示の丸め（千円、百万円） |

### 承認ワークフロー

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| approval_workflow_enabled | Check | 1 | 予算計画の承認ワークフローを有効化 |
| require_department_head_approval | Check | 1 | 部門長の承認を必須にする |
| require_cfo_approval | Check | 1 | CFOの承認を必須にする |
| revision_approval_required | Check | 1 | 予算修正の承認を必須にする |
| max_revision_count | Int | 3 | 予算計画あたりの最大修正回数 |

### 差異チェック

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| variance_threshold_pct | Int | 10 | アクションを発生させる予算差異のパーセンテージ |
| variance_action | Select | Warn | 閾値超過時のアクション: Warn（警告）, Stop（停止）, Ignore（無視） |
| check_budget_on_purchase_order | Check | 1 | 発注提出時に予算チェックを有効化 |

### 予測設定

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| forecast_enabled | Check | 1 | 予算予測機能を有効化 |
| forecast_method | Select | Linear | デフォルト手法: Linear（線形）, Average（平均）, Trend（トレンド）, Manual（手動） |
| forecast_update_day | Int | 5 | 自動予測更新の日（毎月何日か） |

---

## DMS Settings（文書管理設定）

**ナビゲーション**: 文書管理 > DMS Settings

文書管理の動作を制御する Single DocType です。

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| enable_version_control | Check | 1 | 文書のバージョンを自動追跡 |
| enable_access_logging | Check | 1 | 文書アクセスイベントをログに記録 |
| e_book_preservation_enabled | Check | 0 | 電子帳簿保存法対応を有効化 |
| default_retention_years | Int | 7 | 新規文書のデフォルト保存期間（年） |
| max_file_size_mb | Int | 50 | 最大ファイルアップロードサイズ（MB） |

---

## Compliance Settings（コンプライアンス設定）

**ナビゲーション**: コンプライアンス > Compliance Settings

AI分類とRAG検索パイプラインを設定する Single DocType です。

### Gemini API

| フィールド | 型 | 説明 |
|---|---|---|
| gemini_api_key | Password | Google Gemini API キー |
| gemini_model | Data | 埋め込み用Geminiモデル名（例: `text-embedding-004`） |
| classification_model | Data | テキスト分類用Geminiモデル（例: `gemini-1.5-flash`） |

### Qdrant接続

| フィールド | 型 | 説明 |
|---|---|---|
| qdrant_url | Data | Qdrant サーバーURL（例: `http://localhost:6333`） |
| qdrant_api_key | Password | Qdrant API キー（認証が有効な場合） |
| qdrant_collection_name | Data | ベクトル保存用コレクション名 |

### チャンキングパラメータ

| フィールド | 型 | 説明 |
|---|---|---|
| chunk_size | Int | チャンクあたりの最大文字数 |
| chunk_overlap | Int | 連続するチャンク間のオーバーラップ文字数 |

### 検索重み

| フィールド | 型 | 説明 |
|---|---|---|
| default_vector_weight | Float | ベクトル類似度スコアのデフォルト重み（0.0-1.0） |
| default_fulltext_weight | Float | 全文検索スコアのデフォルト重み（0.0-1.0） |

---

## Audit Settings（監査設定）

**ナビゲーション**: 内部監査 > Audit Settings

内部監査の動作を設定する Single DocType です。

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| jsox_enabled | Check | 0 | J-SOX（金融商品取引法）対応フィールドを有効化 |
| risk_matrix_enabled | Check | 1 | リスクマトリクス機能を有効化 |
| risk_matrix_size | Select | 5x5 | リスクマトリクスの次元（3x3, 4x4, 5x5） |
| risk_review_cycle_days | Int | 90 | リスク審査の必須サイクル（日） |
| auto_reminder_days | Int | 7 | 期日の何日前にアクションリマインダーを送信するか |
| overdue_check_frequency | Select | Daily | 期限超過アクションのチェック頻度 |

---

## E-Signature Provider Settings（電子署名プロバイダ設定）

**ナビゲーション**: 契約管理 > E-Signature Provider Settings

標準DocType（複数レコード可）。電子署名プロバイダごとに1レコードを作成します。

| フィールド | 型 | 説明 |
|---|---|---|
| provider_name | Data | プロバイダの表示名 |
| provider_type | Select | CloudSign または DocuSign |
| enabled | Check | このプロバイダが有効かどうか |
| api_url | Data | プロバイダAPI ベースURL |
| api_key | Password | API認証キー |
| api_secret | Password | APIシークレット/クライアントシークレット |
| client_id | Data | OAuth クライアントID（DocuSign） |
| account_id | Data | プロバイダのアカウントID |
| default_expiry_days | Int | 署名依頼のデフォルト有効期限（日） |
| webhook_secret | Password | Webhookペイロード検証用シークレット |
| sandbox_mode | Check | サンドボックス/テスト環境を使用 |

### プロバイダ固有の設定

**CloudSign**:
- `api_url` は通常 `https://api.cloudsign.jp`
- `api_key` は CloudSign のクライアントID
- 登録するWebhook URL: `https://your-site/api/method/lifegence_business.contract_approval.api.esignature.callback_signature_complete`

**DocuSign**:
- `api_url` 本番: `https://na1.docusign.net`（リージョンにより異なる）
- `api_url` サンドボックス: `https://demo.docusign.net`
- OAuth認証に `client_id` と `api_secret` が必要
- `account_id` は DocuSign アカウントのGUID

---

## ロール割り当て

### ロールの作成方法

ロールは2つの方法で作成されます:

1. **フィクスチャ**（10ロール）: `bench export-fixtures` で出力され、install/migrate時にインポートされます。`hooks.py` の `fixtures` キーで定義されています。

2. **インストールスクリプト**（2ロール）: `install.py` の `after_install` と `after_migrate` でプログラム的に作成されます。

### モジュール別ロール権限

#### 契約管理

モジュール固有のロールはありません。標準のFrappe権限が Contract および関連DocTypeに使用されます。

#### コンプライアンス

| ロール | Committee Report | Classification Category | Report Chunk | Indexing Log | Compliance Settings |
|---|---|---|---|---|---|
| Compliance Manager | CRUD + エクスポート | CRUD | CRUD | CRUD | 読取 + 書込 |
| Compliance User | 読取 + エクスポート | 読取 | 読取 | 読取 | 読取 |

#### 与信管理

| ロール | Credit Limit | Credit Assessment | Credit Alert | Anti-Social Check | Credit Settings |
|---|---|---|---|---|---|
| Credit Manager | CRUD | CRUD | CRUD | CRUD | 読取 + 書込 |
| Credit Approver | 読取 + 書込 | 読取 | 読取 | 読取 | 読取 |

#### 予算管理

| ロール | Budget Plan | Budget Revision | Budget Forecast | Budget Settings |
|---|---|---|---|---|
| Budget Manager | CRUD | CRUD | CRUD | 読取 + 書込 |

#### ヘルプデスク

| ロール | HD Ticket | HD Category | HD SLA Policy | HD Knowledge Base |
|---|---|---|---|---|
| Support Manager | CRUD | CRUD | CRUD | CRUD |
| Support Agent | 読取 + 書込 | 読取 | 読取 | 読取 + 書込 |

#### 文書管理

| ロール | Managed Document | Document Folder | Document Access Rule | DMS Settings |
|---|---|---|---|---|
| DMS Manager | CRUD | CRUD | CRUD | 読取 + 書込 |
| DMS User | 読取 + 書込 | 読取 | 読取 | 読取 |

#### 内部監査

| ロール | Audit Plan | Audit Finding | Corrective Action | Risk Register | Audit Settings |
|---|---|---|---|---|---|
| Audit Manager | CRUD | CRUD | CRUD | CRUD | 読取 + 書込 |
| Auditor | 読取 + 書込 | CRUD | 読取 + 書込 | 読取 | 読取 |
| Risk Manager | 読取 | 読取 | 読取 | CRUD | 読取 |

### ユーザーへのロール割り当て方法

1. **User** リストに移動
2. 対象のユーザーレコードを開く
3. **ロール** セクションまでスクロール
4. 上記テーブルから必要なロールを追加
5. 保存

benchコマンドでも設定可能です:

```bash
bench --site your-site add-user-role user@example.com "Credit Manager"
```

---

## 外部サービス設定

### Qdrant（コンプライアンスモジュール）

Qdrant はコンプライアンスモジュールのセマンティック類似度検索に使用するベクトルデータベースです。

**セットアップ方法**:

1. **Docker**（開発環境推奨）:

```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

2. **Qdrant Cloud**（本番環境推奨）:
   - [cloud.qdrant.io](https://cloud.qdrant.io) でアカウントを作成
   - クラスタを作成し、URLとAPIキーを取得

**Compliance Settings への入力例**:

| 設定項目 | 設定値例 |
|---|---|
| qdrant_url | `http://localhost:6333` または `https://xxx.cloud.qdrant.io` |
| qdrant_api_key | （ローカルの場合は空、クラウドの場合は必須） |
| qdrant_collection_name | `compliance_reports` |

コレクションは初回のインデキシング操作時に存在しない場合は自動作成されます。

### Google Gemini API（コンプライアンスモジュール）

Geminiはテキスト埋め込み（RAG検索）およびAI分類に使用されます。

**セットアップ**:

1. [Google AI Studio](https://aistudio.google.com/) にアクセス
2. APIキーを作成
3. Compliance Settings にキーを入力

**推奨モデル**:

| 用途 | モデル | 備考 |
|---|---|---|
| 埋め込み | `text-embedding-004` | 768次元ベクトル |
| 分類 | `gemini-1.5-flash` | 分類タスクにコスト効率が良い |

### CloudSign（契約管理モジュール）

国内契約の電子署名に使用する日本の電子署名サービスです。

**セットアップ**:

1. CloudSign の法人アカウントを作成
2. 開発者コンソールからAPI認証情報を取得
3. CloudSign設定画面でWebhook URLを登録
4. E-Signature Provider Settings レコードを `provider_type = CloudSign` で作成

**Webhook URL形式**:

```
https://your-site.example.com/api/method/lifegence_business.contract_approval.api.esignature.callback_signature_complete
```

### DocuSign（契約管理モジュール）

国際的な電子署名サービスです。

**セットアップ**:

1. [developers.docusign.com](https://developers.docusign.com) で開発者アカウントを作成
2. インテグレーション（アプリ）を作成し、クライアントIDとシークレットを取得
3. OAuthの同意画面とリダイレクトURIを設定
4. E-Signature Provider Settings レコードを `provider_type = DocuSign` で作成
5. テスト時は `sandbox_mode` を有効化

### TDB / TSR API（与信管理モジュール）

日本企業向けの外部信用情報サービスです。

**TDB（帝国データバンク）**:
- TDBに連絡してAPI利用の認証情報を取得
- Credit Settings にAPIのURLとキーを入力

**TSR（東京商工リサーチ）**:
- TSRに連絡してAPI利用の認証情報を取得
- Credit Settings にAPIのURLとキーを入力

これらのAPIは `run_anti_social_check` API および与信審査プロセスで呼び出されます。オプション機能であり、手動データ入力でも与信管理は利用可能です。

---

## 関連ドキュメント

- [セットアップガイド](setup.md) -- インストールと初期設定
- [モジュールリファレンス](modules.md) -- 詳細なモジュール・APIドキュメント
- [トラブルシューティング](troubleshooting.md) -- よくある問題と解決策
