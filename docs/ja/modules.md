# Lifegence Business -- モジュールリファレンス

lifegence_business アプリに含まれる全7モジュールのドキュメントです。

---

## 目次

1. [契約管理](#契約管理)
2. [コンプライアンス](#コンプライアンス)
3. [与信管理](#与信管理)
4. [予算管理](#予算管理)
5. [ヘルプデスク](#ヘルプデスク)
6. [文書管理 (DMS)](#文書管理-dms)
7. [内部監査](#内部監査)

---

## 契約管理

**英語名**: Contract Approval

契約のライフサイクル管理、承認ワークフロー、電子署名連携機能を提供します。

### DocType一覧 (7)

| DocType | 用途 |
|---|---|
| Contract | 契約本体。ライフサイクルステータスの追跡 |
| Contract Template | 再利用可能な契約テンプレート |
| Contract Approval Rule | 種別・金額による自動承認ルーティングルール |
| Contract Approval Log | 承認アクションの監査証跡 |
| E-Signature Provider Settings | CloudSign/DocuSign プロバイダ設定 |
| E-Signature Request | 署名依頼と署名者ステータスの追跡 |
| E-Signature Log | 署名イベントのログ |

### 契約ライフサイクル

```
ドラフト --> 承認待ち --> 承認済み --> 有効 --> 期限切れ
                     \-> 却下           \-> 解約
```

### 契約種別

- 業務委託
- 売買
- 賃貸借
- NDA（秘密保持契約）
- 雇用
- ライセンス
- その他

### 承認ルーティング

契約が承認申請されると、**Contract Approval Rule** レコードを順次評価します。ルールは以下の条件でマッチングされます:

- **契約種別** -- 特定の種別に限定（または全種別にマッチ）
- **金額範囲** -- `min_amount` / `max_amount` の閾値
- **承認者** -- 特定のユーザー、または指定ロールを持つ最初のユーザー

最初にマッチした有効なルールの承認者が選択されます。

### 電子署名連携

電子署名サブシステムは **E-Signature Provider Settings** DocType を通じて CloudSign と DocuSign をサポートします。ワークフローは以下の通りです:

1. API認証情報とデフォルト有効期限を含むプロバイダ設定レコードを作成
2. 署名者情報を指定して `create_signature_request` を呼び出し
3. システムが E-Signature Request を作成しプロバイダに送信
4. Webhook コールバックが `callback_signature_complete` 経由で署名者ステータスを更新
5. 全署名者が署名完了すると、リクエストのステータスが「Completed」に変更

**Webhook エンドポイント** (allow_guest):

```
POST /api/method/lifegence_business.contract_approval.api.esignature.callback_signature_complete
```

受信するJSONペイロード:

| フィールド | 必須 | 説明 |
|---|---|---|
| envelope_id | はい | プロバイダのエンベロープ/ドキュメントID |
| event_type | はい | Sent, Viewed, Signed, Declined, Expired, Cancelled, Error |
| signer_email | いいえ | 署名者のメールアドレス |
| signer_name | いいえ | 署名者の氏名 |
| ip_address | いいえ | 署名者のIPアドレス |
| certificate_data | いいえ | デジタル証明書データ |
| provider_event_id | いいえ | プロバイダのイベントID（重複排除用） |

### APIリファレンス

#### `submit_for_approval`

ドラフト契約を承認申請します。

```
POST /api/method/lifegence_business.contract_approval.api.approval.submit_for_approval
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| contract_name | string | はい | Contract ドキュメント名 |

戻り値: `{ success, approver }`

#### `approve_contract`

承認待ちの契約を承認します。

```
POST /api/method/lifegence_business.contract_approval.api.approval.approve_contract
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| contract_name | string | はい | Contract ドキュメント名 |
| comments | string | いいえ | 承認コメント |

戻り値: `{ success }`

#### `reject_contract`

承認待ちの契約を却下します。

```
POST /api/method/lifegence_business.contract_approval.api.approval.reject_contract
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| contract_name | string | はい | Contract ドキュメント名 |
| comments | string | いいえ | 却下理由 |

戻り値: `{ success }`

#### `create_signature_request`

承認済みまたは有効な契約に対して電子署名リクエストを作成します。

```
POST /api/method/lifegence_business.contract_approval.api.esignature.create_signature_request
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| contract_name | string | はい | Contract ドキュメント名 |
| signers | JSON文字列 | はい | `{name, email, order}` の配列 |
| provider_name | string | いいえ | E-Signature Provider Settings 名（デフォルト: 最初に有効なプロバイダ） |
| expiry_days | int | いいえ | 有効期限日数のオーバーライド |

戻り値: `{ success, signature_request, envelope_id, expiry_date }`

#### `check_signature_status`

電子署名リクエストの現在のステータスを確認します。

```
POST /api/method/lifegence_business.contract_approval.api.esignature.check_signature_status
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| signature_request_name | string | いいえ* | E-Signature Request ドキュメント名 |
| contract_name | string | いいえ* | Contract名（最新のリクエストを検索） |

*いずれか1つは必須。

戻り値: `{ success, found, signature_request, status, signers, logs }`

---

## コンプライアンス

**英語名**: Compliance

第三者委員会報告書の分析、AI分類、RAG（検索拡張生成）検索機能を提供します。

### DocType一覧 (6)

| DocType | 用途 |
|---|---|
| Committee Report | 第三者委員会調査報告書 |
| Classification Category | 3レイヤー39カテゴリの分類体系 |
| Report Classification | 子テーブル: 報告書とカテゴリの紐付け |
| Report Chunk | 検索用にテキストを分割したチャンク |
| Indexing Log | PDFの処理・インデキシング操作のログ |
| Compliance Settings | Gemini API、Qdrant、検索パラメータの設定 |

### 分類タクソノミー（39カテゴリ）

**レイヤーA -- 不正類型**: 14カテゴリ

| コード | カテゴリ |
|---|---|
| A01 | 会計不正・粉飾決算 |
| A02 | 横領・着服 |
| A03 | 贈収賄 |
| A04 | 品質偽装 |
| A05 | データ改ざん |
| A06 | 情報漏洩 |
| A07 | ハラスメント |
| A08 | 独占禁止法違反 |
| A09 | インサイダー取引 |
| A10 | 利益相反 |
| A11 | 環境違反 |
| A12 | 労働法違反 |
| A13 | 知的財産侵害 |
| A14 | その他 |

**レイヤーB -- 組織メカニズム**: 15カテゴリ (B01-B15)

監査機能不全、内部通報制度の問題、取締役会の監督不足、リスク管理体制の不備、内部統制の不備、コンプライアンス体制の不備、情報開示の不備、人事評価制度の問題、教育研修の不足、ITシステムの不備、子会社管理の不備、外部委託管理の不備、文書管理の不備、権限管理の不備、その他。

**レイヤーC -- 組織文化**: 10カテゴリ (C01-C10)

同調圧力、権威勾配、業績至上主義、閉鎖的組織文化、属人的経営、前例踏襲主義、縦割り組織、不十分な倫理観、現場と経営の乖離、その他。

### RAG検索パイプライン

1. **PDF処理**: Committee Report ドキュメントとして報告書をアップロード
2. **テキスト抽出**: 添付PDFからテキストを抽出
3. **チャンキング**: 設定可能なサイズとオーバーラップでテキストを分割
4. **埋め込み**: Google Gemini API でチャンクをベクトル化
5. **保存**: ベクトルを Qdrant に保存、チャンクを Report Chunk レコードとして保存
6. **検索**: ベクトル類似度と MySQL FULLTEXT スコアのハイブリッド検索

### ロール

| ロール | 権限 |
|---|---|
| Compliance Manager | 全コンプライアンスDocTypeのフルCRUD |
| Compliance User | 報告書、カテゴリ、チャンク、ログ、設定の読み取り |

### ダッシュボード

`/app/compliance-dashboard` にカスタムページとして RAG 検索インターフェースを提供します。

### APIリファレンス

#### 分類API

**`get_taxonomy`** -- 3レイヤーの分類タクソノミー全体を取得。

```
GET /api/method/lifegence_business.compliance.api.classification.get_taxonomy
```

**`get_stats`** -- 分類統計とカテゴリ分布を取得。

```
GET /api/method/lifegence_business.compliance.api.classification.get_stats
```

**`analyze_text`** -- AIによるテキスト分類。

```
POST /api/method/lifegence_business.compliance.api.classification.analyze_text
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| text | string | はい | 分類対象のテキスト |

**`get_report_classification`** -- 特定の報告書の分類結果を取得。

```
GET /api/method/lifegence_business.compliance.api.classification.get_report_classification
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| report_name | string | はい | Committee Report ドキュメント名 |

#### インデキシングAPI

**`index_report`** -- 単一の報告書をインデックス（抽出、チャンク、埋め込み、保存）。

```
POST /api/method/lifegence_business.compliance.api.indexing.index_report
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| report_name | string | はい | Committee Report ドキュメント名 |

**`index_batch`** -- 未処理の報告書を一括インデックス。

```
POST /api/method/lifegence_business.compliance.api.indexing.index_batch
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| limit | int | いいえ | 処理件数（デフォルト: 10） |

**`reindex_report`** -- インデックス済み報告書の再インデックス。

```
POST /api/method/lifegence_business.compliance.api.indexing.reindex_report
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| report_name | string | はい | Committee Report ドキュメント名 |

#### 検索API

**`hybrid_search`** -- ベクトル検索と全文検索のハイブリッド検索。

```
POST /api/method/lifegence_business.compliance.api.search.hybrid_search
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| query | string | はい | 検索クエリテキスト |
| limit | int | いいえ | 最大結果数 |
| year | int | いいえ | 報告書の年度でフィルタ |
| company_name | string | いいえ | 企業名でフィルタ |
| classification | string | いいえ | 分類カテゴリでフィルタ |
| vector_weight | float | いいえ | ベクトルスコアの重み |
| fulltext_weight | float | いいえ | 全文検索スコアの重み |
| group_by_report | string | いいえ | 報告書単位でグループ化（"0"で無効） |

**`vector_search`** -- ベクトル類似度検索のみ。

```
POST /api/method/lifegence_business.compliance.api.search.vector_search
```

パラメータ: `hybrid_search` と同様（重みパラメータなし）。

**`fulltext_search`** -- MySQL FULLTEXT 検索のみ。

```
POST /api/method/lifegence_business.compliance.api.search.fulltext_search
```

パラメータ: `vector_search` と同様。

**`find_similar`** -- 指定した報告書に類似する報告書を検索。

```
POST /api/method/lifegence_business.compliance.api.search.find_similar
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| report_name | string | はい | Committee Report ドキュメント名 |
| limit | int | いいえ | 最大結果数（デフォルト: 5） |

---

## 与信管理

**英語名**: Credit Management

取引先ごとの与信枠管理、受注時の自動与信チェック、リスクスコアリング、反社会的勢力チェック機能を提供します。

### DocType一覧 (6)

| DocType | 用途 |
|---|---|
| Credit Limit | 取引先ごとの与信枠と利用状況の追跡 |
| Credit Assessment | 5要素評価によるリスクスコアリング |
| Credit Alert | 期限切れ、閾値超過、延滞請求書のアラート |
| Credit Limit History | 与信枠変更履歴 |
| Anti-Social Check | 反社会的勢力チェック記録 |
| Credit Settings | デフォルト期間、閾値、グレードスコア、API設定 |

### 受注時の与信チェック

Sales Order の提出時に `before_submit` フックが自動的に以下を実行します:

1. 取引先の Credit Limit を検索
2. 受注金額と利用可能な与信枠を比較
3. `auto_block_on_exceed` が有効で与信枠を超過する場合、提出をブロック
4. チェック結果を `credit_check_passed` および `credit_check_note` カスタムフィールドに記録

Sales Order、Sales Invoice、Payment Entry の提出・取消時に取引先残高が再計算されます。

### リスクスコアリング

与信審査は5つの要素で評価します（合計: 100点満点）:

| 要素 | 最大点数 |
|---|---|
| 財務健全性 | 30 |
| 取引実績 | 15 |
| 資本充実度 | 15 |
| 支払実績 | 25 |
| 取引量 | 15 |

**リスクグレード**:

| グレード | スコア範囲 |
|---|---|
| A | 80以上 |
| B | 60-79 |
| C | 40-59 |
| D | 20-39 |
| E | 20未満 |

### ERPNext DocType へのカスタムフィールド

**Customer（取引先）**:

| フィールド | 型 | 説明 |
|---|---|---|
| risk_grade（リスクグレード） | Data（読取専用） | 現在のリスクグレード（A-E） |
| credit_status（与信ステータス） | Data（読取専用） | 現在の与信枠ステータス |
| anti_social_check_result（反社チェック結果） | Data（読取専用） | 最新の反社チェック結果 |

**Sales Order（受注）**:

| フィールド | 型 | 説明 |
|---|---|---|
| credit_check_passed（与信チェック合格） | Check（読取専用） | 提出時の与信チェック結果 |
| credit_check_note（与信チェック備考） | Small Text（読取専用） | 与信チェックの詳細 |

### スケジュールタスク（日次）

- 与信枠の有効期限チェック
- 審査期日のリマインダー
- 延滞請求書のアラート
- 反社チェック有効期限のアラート

### APIリファレンス

#### `get_credit_status`

取引先の与信ステータスを取得します。

```
GET /api/method/lifegence_business.credit.api.credit_status.get_credit_status
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| customer | string | はい | Customer ドキュメント名 |
| company | string | いいえ | 会社でフィルタ |

戻り値: `{ success, credit_status: { credit_limit_amount, used_amount, available_amount, usage_percentage, risk_grade, anti_social_check, open_alerts } }`

#### `update_credit_limit`

与信枠を更新し、変更履歴を記録します。

```
POST /api/method/lifegence_business.credit.api.credit_limit.update_credit_limit
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| customer | string | はい | Customer ドキュメント名 |
| new_amount | float | はい | 新しい与信枠金額 |
| change_reason | string | はい | 変更理由 |
| company | string | いいえ | 会社（デフォルト: サイトのデフォルト会社） |
| change_detail | string | いいえ | 追加の詳細 |

戻り値: `{ success, previous_amount, new_amount, history }`

#### `create_assessment`

新しい与信審査を作成します。

```
POST /api/method/lifegence_business.credit.api.assessment.create_assessment
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| customer | string | はい | Customer ドキュメント名 |
| requested_amount | float | はい | 申請金額 |
| assessment_type | string | いいえ | デフォルト: "新規取引" |
| revenue | float | いいえ | 取引先の売上高 |
| profit | float | いいえ | 取引先の利益 |
| capital | float | いいえ | 取引先の資本金 |
| years_in_business | int | いいえ | 設立からの年数 |

戻り値: `{ success, assessment, risk_score, risk_grade, recommended_limit }`

#### `run_anti_social_check`

新しい反社チェック記録を作成します。

```
POST /api/method/lifegence_business.credit.api.anti_social.run_anti_social_check
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| customer | string | はい | Customer ドキュメント名 |
| check_source | string | はい | データソース（TDB, TSR等） |
| result | string | はい | チェック結果 |
| result_detail | string | いいえ | 詳細所見 |

戻り値: `{ success, check, result, valid_until }`

---

## 予算管理

**英語名**: Budget Management

部門・コストセンター別の年間予算計画、月次内訳、差異チェック、決算予測機能を提供します。

### DocType一覧 (7)

| DocType | 用途 |
|---|---|
| Budget Plan | 月次明細を含む年間予算 |
| Budget Plan Item | 子テーブル: 勘定科目別の月次金額 |
| Budget Revision | 承認済み予算の修正 |
| Budget Revision Item | 子テーブル: 勘定科目別の修正金額 |
| Budget Forecast | 期間別の決算予測 |
| Budget Forecast Item | 子テーブル: 勘定科目別の予測詳細 |
| Budget Settings | 会計年度、通貨、承認、差異チェックの設定 |

### 予算ライフサイクル

```
ドラフト --> 提出済み --> 承認済み --> 修正済み（Budget Revision 経由）
                    \-> 差戻し
```

### 差異チェック

Purchase Order および Journal Entry の提出時に `before_submit` フックが予算の利用可能性をチェックします:

- **Warn（警告）**: 警告を表示するが提出は許可
- **Stop（停止）**: 予算超過の場合は提出をブロック
- **Ignore（無視）**: チェックを実行しない

閾値は Budget Settings でパーセンテージとして設定可能です。

### 予測手法

| 手法 | 説明 |
|---|---|
| Linear（線形） | 実績に基づく線形推計 |
| Average（平均） | 月次平均による外挿 |
| Trend（トレンド） | 過去パターンに基づくトレンド推計 |
| Manual（手動） | ユーザー指定の予測金額 |

### スケジュールタスク（日次）

- 予算閾値アラート通知

### APIリファレンス

#### `get_budget_vs_actual`

予算対実績比較データを取得します。

```
GET /api/method/lifegence_business.budget.api.budget_actual.get_budget_vs_actual
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| company | string | はい | 会社名 |
| fiscal_year | string | はい | 会計年度名 |
| department | string | いいえ | 部門でフィルタ |
| cost_center | string | いいえ | コストセンターでフィルタ |
| budget_type | string | いいえ | 予算タイプでフィルタ |
| as_of_date | string | いいえ | 基準日（デフォルト: 当日） |
| period | string | いいえ | "Cumulative"（デフォルト） |

戻り値: `{ success, data: { summary, by_department, by_account } }`

#### `submit_budget_plan`

Budget Plan のワークフローを進めます。

```
POST /api/method/lifegence_business.budget.api.budget_plan.submit_budget_plan
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| budget_plan | string | はい | Budget Plan ドキュメント名 |
| action | string | はい | "submit", "approve", "reject" |
| comment | string | いいえ* | actionが "reject" の場合は必須 |

戻り値: `{ success, data: { budget_plan, previous_status, new_status } }`

#### `create_revision`

承認済み予算の修正を作成します。

```
POST /api/method/lifegence_business.budget.api.budget_plan.create_revision
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| budget_plan | string | はい | Budget Plan ドキュメント名 |
| reason | string | はい | 修正理由 |
| revision_type | string | はい | 修正タイプ |
| revised_items | JSON文字列 | いいえ | 修正明細の配列 |

戻り値: `{ success, data: { revision, revision_number, total_change_amount } }`

#### `update_forecast`

予算予測を更新または作成します。

```
POST /api/method/lifegence_business.budget.api.forecast.update_forecast
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| budget_forecast | string | いいえ* | 既存の予測名 |
| budget_plan | string | いいえ* | Budget Plan名（新規予測の場合） |
| forecast_month | string | いいえ | 新規予測の対象月 |
| method | string | いいえ | 予測手法のオーバーライド |

*`budget_forecast` または `budget_plan` のいずれかが必須。

戻り値: `{ success, data: { budget_forecast, approved_budget, actual_to_date, forecast_to_year_end, variance_from_budget } }`

### スクリプトレポート

**予算対実績** -- レポート画面から利用可能。部門別・勘定科目別の予算比較と消化率を表示します。

---

## ヘルプデスク

**英語名**: Helpdesk

社内外のサポートチケット管理、SLA追跡、ナレッジベース機能を提供します。

### DocType一覧 (6)

| DocType | 用途 |
|---|---|
| HD Ticket | 優先度・SLA追跡付きサポートチケット |
| HD Ticket Comment | 子テーブル: チケットへのコメント/返信 |
| HD Category | チケットカテゴリ（IT, HR, 経理等） |
| HD SLA Policy | 優先度別の応答・解決時間目標 |
| HD SLA Timer | SLAタイマー状態の追跡 |
| HD Knowledge Base | 検索可能なナレッジベース記事 |

### チケットワークフロー

```
オープン --> 対応中 --> 顧客待ち --> 解決済み --> クローズ
```

### プリインストールデータ

**カテゴリ**:

| カテゴリ | 説明 | タイプ |
|---|---|---|
| IT | IT関連の問い合わせ | 社内 |
| HR | 人事・労務の問い合わせ | 社内 |
| 経理 | 経理・会計の問い合わせ | 社内 |
| 顧客サポート | 顧客からの問い合わせ | 外部 |

**デフォルトSLAポリシー**（「標準SLA」）:

| 優先度 | 応答時間 | 解決時間 |
|---|---|---|
| Low | 24時間 | 72時間 |
| Medium | 8時間 | 24時間 |
| High | 4時間 | 8時間 |
| Urgent | 1時間 | 4時間 |

営業時間: 09:00 - 18:00

### ナレッジベース

記事は以下をサポートします:

- カテゴリベースの整理
- 公開範囲の制御（内部のみ、外部公開、両方）
- 「役に立った」カウントによる有用性の追跡
- タイトル、本文、タグのキーワード検索

### APIリファレンス

#### `create_ticket`

新しいヘルプデスクチケットを作成します。

```
POST /api/method/lifegence_business.helpdesk.api.ticket.create_ticket
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| subject | string | はい | チケット件名 |
| description | string | はい | チケット説明 |
| category | string | いいえ | HD Category 名 |
| priority | string | いいえ | Low, Medium（デフォルト）, High, Urgent |
| ticket_type | string | いいえ | "社内"（デフォルト）または "外部" |
| raised_by_name | string | いいえ | 起票者名（デフォルト: ログインユーザー） |
| raised_by_email | string | いいえ | 起票者メール（デフォルト: ログインユーザー） |

戻り値: `{ success, ticket, status, assigned_to, sla_policy, response_due, resolution_due }`

#### `update_ticket_status`

チケットのステータスを更新します。

```
POST /api/method/lifegence_business.helpdesk.api.ticket.update_ticket_status
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| ticket | string | はい | HD Ticket ドキュメント名 |
| status | string | はい | 新しいステータス |
| resolution | string | いいえ | 解決内容（解決済み/クローズ時） |

#### `add_comment`

チケットにコメントを追加します。

```
POST /api/method/lifegence_business.helpdesk.api.ticket.add_comment
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| ticket | string | はい | HD Ticket ドキュメント名 |
| comment | string | はい | コメントテキスト |
| is_internal | int | いいえ | 1: 内部コメント（デフォルト: 0） |

#### `get_helpdesk_dashboard`

チケット件数、SLAコンプライアンス率、カテゴリ・優先度別の内訳を含むダッシュボードを取得します。

```
GET /api/method/lifegence_business.helpdesk.api.dashboard.get_helpdesk_dashboard
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| company | string | いいえ | 会社でフィルタ |

#### `search_knowledge_base`

ナレッジベース記事を検索します。

```
GET /api/method/lifegence_business.helpdesk.api.knowledge_base.search_knowledge_base
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| query | string | いいえ | 検索キーワード |
| category | string | いいえ | カテゴリでフィルタ |
| visibility | string | いいえ | "外部公開" または "内部のみ" |

---

## 文書管理 (DMS)

**英語名**: DMS (Document Management System)

バージョン管理、アクセスログ、保存ポリシー、電子帳簿保存法対応の文書管理機能を提供します。

### DocType一覧 (10)

| DocType | 用途 |
|---|---|
| Managed Document | バージョニング付き文書レコード |
| Document Version | 子テーブル: 文書の各バージョン |
| Document Folder | 階層的フォルダ構造 |
| Document Access Rule | 文書ごとのアクセス制御ルール |
| Document Access Log | 文書アクセスの追跡ログ |
| Document Review | 文書レビューワークフロー |
| Document Template | 再利用可能な文書テンプレート |
| Retention Policy | 保存期間ルールの設定 |
| E-Book Preservation Log | 電子帳簿保存法のコンプライアンスログ |
| DMS Settings | バージョン管理、アクセスログ、ファイルサイズの設定 |

### プリインストール保存ポリシー

| ポリシー | 期間 | 期限到来時のアクション |
|---|---|---|
| 法定7年保存 | 7年 | 通知 |
| 法定10年保存 | 10年 | 通知 |
| 永久保存 | 無期限 (0) | 通知 |
| 3年保存 | 3年 | アーカイブ |

### 文書ライフサイクル

1. 文書をアップロード（コンテンツハッシュとバージョン1が自動生成）
2. 文書の更新に合わせて新しいバージョンを作成
3. 任意でファイナライズして文書を不変にする
4. 保存ポリシーにより文書のアーカイブ・削除時期を追跡

### フォルダ構造

文書は階層的なフォルダツリーで管理されます。各フォルダは:

- 部門に所属可能
- プライベート設定が可能
- サブフォルダとドキュメントを格納可能

### アクセス制御

Document Access Rule は以下のルールタイプをサポートします:

| ルールタイプ | 説明 |
|---|---|
| User | 特定のユーザーにアクセスを付与 |
| Role | 特定のロールを持つ全ユーザーにアクセスを付与 |
| Department | 特定の部門の全ユーザーにアクセスを付与 |

アクセスレベル: Read, Write, Full Access

### APIリファレンス

#### `upload_document`

新しい管理文書をアップロードします。

```
POST /api/method/lifegence_business.dms.api.document.upload_document
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| document_name | string | はい | 文書の表示名 |
| file | string | はい | ファイルURLまたは添付 |
| folder | string | いいえ | Document Folder 名 |
| document_type | string | いいえ | デフォルト: "その他" |
| tags | string | いいえ | カンマ区切りのタグ |
| description | string | いいえ | 文書の説明 |
| retention_policy | string | いいえ | Retention Policy 名 |
| company | string | いいえ | 会社 |

戻り値: `{ success, document, status, current_version, content_hash, retention_until }`

#### `create_new_version`

既存の文書に新しいバージョンを追加します。

```
POST /api/method/lifegence_business.dms.api.document.create_new_version
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| document | string | はい | Managed Document 名 |
| file | string | はい | 新しいファイルURL |
| change_summary | string | いいえ | 変更の概要 |

#### `finalize_document`

文書をファイナライズし、以降の変更を不可にします。

```
POST /api/method/lifegence_business.dms.api.document.finalize_document
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| document | string | はい | Managed Document 名 |

#### `get_folder_tree`

フォルダ階層を取得します。

```
GET /api/method/lifegence_business.dms.api.folder.get_folder_tree
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| parent_folder | string | いいえ | 親フォルダ名（省略でルートフォルダ） |

各フォルダに `child_count` と `document_count` が含まれます。

#### `search_documents`

キーワード、フォルダ、種別、タグで文書を検索します。

```
GET /api/method/lifegence_business.dms.api.search.search_documents
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| query | string | いいえ | 検索キーワード |
| folder | string | いいえ | フォルダでフィルタ |
| document_type | string | いいえ | 文書種別でフィルタ |
| tags | string | いいえ | タグでフィルタ |

---

## 内部監査

**英語名**: Audit

監査計画、監査実施、発見事項、是正措置、リスクレジスター、J-SOX対応の内部監査管理機能を提供します。

### DocType一覧 (10)

| DocType | 用途 |
|---|---|
| Audit Plan | 年次/定期監査計画 |
| Audit Engagement | 計画に基づく個別の監査実施 |
| Audit Finding | 監査で発見された問題 |
| Audit Checklist | スコアリング付き監査チェックリスト |
| Audit Checklist Item | 子テーブル: 個別のチェックリスト項目 |
| Corrective Action | 監査発見事項に対する是正措置 |
| Risk Register | 組織のリスクカタログ |
| Risk Assessment | 発生可能性 x 影響度によるリスク評価 |
| Control Activity | 内部統制の文書化とテスト |
| Audit Settings | J-SOX、リスクマトリクス、リマインダーの設定 |

### リスクマトリクス

設定可能なグリッド（デフォルト5x5）の発生可能性と影響度スコアを使用します:

```
影響度
  5 |  5  10  15  20  25
  4 |  4   8  12  16  20
  3 |  3   6   9  12  15
  2 |  2   4   6   8  10
  1 |  1   2   3   4   5
    +--------------------
       1   2   3   4   5
              発生可能性
```

スコアからリスクレベルが導出されます:

| スコア範囲 | リスクレベル |
|---|---|
| 1-4 | Low（低） |
| 5-9 | Medium（中） |
| 10-15 | High（高） |
| 16-25 | Critical（重大） |

### リスクカテゴリ

- 戦略
- 財務
- 業務
- コンプライアンス
- IT
- 災害
- レピュテーション
- その他

### J-SOX対応

Audit Settings で有効化すると、監査関連DocTypeに以下の追加フィールドが使用可能になります:

- 財務諸表のアサーション
- プロセスカテゴリ
- 統制の有効性評価

### DocEvent

| イベント | 動作 |
|---|---|
| Corrective Action `on_update` | 紐付けられた Audit Finding にステータス変更を連動 |
| Audit Checklist Item `on_update` | 親チェックリストのサマリースコアを再計算 |

### スケジュールタスク

**日次**:
- 期限超過の是正措置チェック
- 期限前リマインダーの送信

**週次**:
- リスクレジスターのレビュー期日チェック

### APIリファレンス

#### `get_audit_dashboard`

監査ダッシュボードの包括的データを取得します。

```
GET /api/method/lifegence_business.audit.api.audit.get_audit_dashboard
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| fiscal_year | string | いいえ | 会計年度でフィルタ |

戻り値: `{ success, data: { plan_summary, findings_summary, corrective_actions_summary, risk_summary } }`

#### `create_finding`

新しい監査発見事項を作成します。

```
POST /api/method/lifegence_business.audit.api.finding.create_finding
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| audit_engagement | string | はい | Audit Engagement 名 |
| finding_title | string | はい | 発見事項のタイトル |
| severity | string | はい | 重要度 |
| category | string | はい | 発見事項のカテゴリ |
| description | string | はい | 詳細説明 |
| recommendation | string | はい | 推奨アクション |

#### `create_corrective_action`

発見事項に対する是正措置を作成します。

```
POST /api/method/lifegence_business.audit.api.corrective_action.create_corrective_action
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| audit_finding | string | はい | Audit Finding 名 |
| action_title | string | はい | 是正措置のタイトル |
| action_description | string | はい | 是正措置の説明 |
| responsible_person | string | はい | 実施責任者（ユーザー） |
| due_date | string | はい | 期限（YYYY-MM-DD） |
| priority | string | いいえ | デフォルト: "Normal" |

#### `get_risk_matrix`

リスクマトリクスのヒートマップデータを取得します。

```
GET /api/method/lifegence_business.audit.api.risk.get_risk_matrix
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| department | string | いいえ | 部門でフィルタ |
| risk_category | string | いいえ | リスクカテゴリでフィルタ |
| jsox_only | bool | いいえ | J-SOX関連リスクのみ表示 |

#### `get_risk_trend`

特定のリスクのスコアトレンドデータを取得します。

```
GET /api/method/lifegence_business.audit.api.risk.get_risk_trend
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| risk_register | string | はい | Risk Register ドキュメント名 |
| period | string | いいえ | 期間フィルタ |

戻り値: `{ success, data: { risk_register, assessments, total_assessments } }`

---

## ERPNext依存DocType

各モジュールから参照される ERPNext の DocType 一覧:

| ERPNext DocType | 使用モジュール |
|---|---|
| Customer（取引先） | 与信管理（カスタムフィールド追加） |
| Sales Order（受注） | 与信管理（カスタムフィールド追加、DocEvent） |
| Sales Invoice（売上請求書） | 与信管理（DocEvent） |
| Payment Entry（支払） | 与信管理（DocEvent） |
| Purchase Order（発注） | 予算管理（DocEvent） |
| Journal Entry（仕訳帳） | 予算管理（DocEvent） |
| GL Entry（総勘定元帳） | 予算管理（実績金額クエリ） |
| Fiscal Year（会計年度） | 予算管理 |
| Company（会社） | 予算管理、与信管理、ヘルプデスク、DMS |
| Department（部門） | 予算管理 |
| Cost Center（コストセンター） | 予算管理 |
| Account（勘定科目） | 予算管理 |
