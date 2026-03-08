# Lifegence Business -- トラブルシューティングガイド

lifegence_business モジュール使用時によく発生する問題の解決策です。

---

## 目次

1. [与信チェックによる受注ブロック](#与信チェックによる受注ブロック)
2. [発注時の予算チェックエラー](#発注時の予算チェックエラー)
3. [コンプライアンスのインデキシング失敗](#コンプライアンスのインデキシング失敗)
4. [電子署名Webhookが受信されない](#電子署名webhookが受信されない)
5. [DMSファイルサイズ制限](#dmsファイルサイズ制限)
6. [監査の期限超過通知が送信されない](#監査の期限超過通知が送信されない)
7. [一般的なトラブルシューティング](#一般的なトラブルシューティング)

---

## 与信チェックによる受注ブロック

### 症状

Sales Order の提出が「与信枠を超過しています」や「与信チェックに失敗しました」等の与信関連エラーで失敗する。

### 原因と対策

#### 1. 取引先に Credit Limit レコードが存在しない

**診断**: 取引先に Credit Limit レコードが存在するか確認します。

```bash
bench --site your-site console
```

```python
frappe.get_all("Credit Limit", filters={"customer": "CUST-0001"}, fields=["name", "credit_limit_amount", "used_amount", "available_amount"])
```

**対策**: 適切な与信枠金額で Credit Limit レコードを作成してください。

#### 2. 与信枠が実際に超過している

**診断**: 受注金額と利用可能な与信額を比較します。

```python
# bench console にて
from lifegence_business.credit.api.credit_status import get_credit_status
print(get_credit_status("CUST-0001"))
```

**対策**: `update_credit_limit` API で与信枠を増額するか、受注金額を減額してください。

#### 3. 取消済みトランザクション後に残高が古い

**診断**: Credit Limit レコードの `used_amount` が実際の未収金残高と一致しない。

**対策**: 残高再計算を実行します:

```python
from lifegence_business.credit.services.balance_calculator import recalculate_customer_balance
recalculate_customer_balance("CUST-0001", "Your Company Name")
```

#### 4. 自動ブロックが不要なのに有効になっている

**診断**: Credit Settings を確認します。

**対策**: **Credit Settings** に移動し、`auto_block_on_exceed` のチェックを外します。自動ブロックが無効の場合、チェック結果は記録されますが提出はブロックされません。

---

## 発注時の予算チェックエラー

### 症状

Purchase Order または Journal Entry の提出が予算利用可能性のエラーで失敗する。

### 原因と対策

#### 1. 承認済みの Budget Plan が存在しない

**診断**: 該当する会計年度とコストセンターの承認済み計画を確認します。

```python
frappe.get_all("Budget Plan", filters={"fiscal_year": "2025-2026", "status": "Approved", "docstatus": 1}, fields=["name", "cost_center", "total_annual_amount"])
```

**対策**: 発注で使用するコストセンターと勘定科目をカバーする Budget Plan を作成・承認してください。

#### 2. 予算が消化済み

**診断**: 予算対実績APIで消化状況を確認します。

```python
from lifegence_business.budget.api.budget_actual import get_budget_vs_actual
result = get_budget_vs_actual(company="Your Company", fiscal_year="2025-2026")
print(result)
```

**対策**: Budget Revision で予算配分を増額するか、発注金額を調整してください。

#### 3. 差異アクションが "Stop" に設定されているが "Warn" が適切

**診断**: Budget Settings を確認します。

**対策**: **Budget Settings** に移動し、`variance_action` を "Stop" から "Warn" に変更します。警告は表示されますが提出は可能になります。

#### 4. コストセンターのマッピングが不正

**診断**: 発注のコストセンターがどの Budget Plan にも一致しない。

**対策**: 発注のコストセンターが該当する承認済み Budget Plan のコストセンターと一致することを確認してください。

---

## コンプライアンスのインデキシング失敗

### 症状

`index_report` または `index_batch` の呼び出しが失敗する、またはインデキシング後に報告書が検索できない。

### Qdrant 接続の問題

#### 症状

エラーログに "Connection refused"、"ConnectionError"、または "Qdrant" を含むエラーメッセージが表示される。

#### 診断

```bash
# Qdrant が稼働しているか確認
curl -s http://localhost:6333/dashboard/ | head -5

# bench console から確認
bench --site your-site console
```

```python
settings = frappe.get_single("Compliance Settings")
print(f"URL: {settings.qdrant_url}")
print(f"Collection: {settings.qdrant_collection_name}")
```

#### 対策

1. **Qdrant が稼働していない**: Qdrant サービスを起動します。

   ```bash
   # Docker
   docker start qdrant

   # または新しいコンテナを起動
   docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant
   ```

2. **設定のURLが間違っている**: Compliance Settings の `qdrant_url` を正しいアドレスとポートに更新してください。

3. **Qdrant Cloud の認証エラー**: `qdrant_api_key` が正しいこと、クラスタがアクティブであることを確認してください。

4. **コレクションが存在しない**: コレクションは通常自動作成されます。削除された場合は、報告書を再インデックスして再作成します:

   ```python
   from lifegence_business.compliance.api.indexing import index_report
   index_report("REPORT-0001")
   ```

### Gemini API の問題

#### 症状

エラーログに "API key"、"quota"、"model not found"、または "embedding" を含むエラーメッセージが表示される。

#### 診断

```python
settings = frappe.get_single("Compliance Settings")
print(f"API Key set: {bool(settings.gemini_api_key)}")
print(f"Model: {settings.gemini_model}")
```

#### 対策

1. **無効なAPIキー**: [Google AI Studio](https://aistudio.google.com/) でAPIキーを再生成し、Compliance Settings を更新してください。

2. **クォータ超過**: Google Cloud の課金ダッシュボードを確認してください。無料枠の上限に達している可能性があります。クォータのリセットを待つか、有料プランにアップグレードしてください。

3. **モデルが見つからない**: Compliance Settings のモデル名を確認してください。埋め込みには `text-embedding-004`、分類には `gemini-1.5-flash` を使用してください。

4. **ネットワーク接続**: Frappe サーバーが `generativelanguage.googleapis.com` のポート443に接続できることを確認してください。

### PDF処理の問題

#### 症状

報告書はインデックスされるが検索結果が返されない、またはインデキシングが0チャンクで完了する。

#### 対策

1. **PDFに抽出可能なテキストがない**（スキャン文書）: 現在の実装はテキストベースのPDFを必要とします。OCR処理は組み込まれていません。アップロード前に外部OCRツールでスキャン文書を変換してください。

2. **PDFが暗号化またはパスワード保護されている**: アップロード前にパスワードを解除してください。

3. **チャンクサイズが大きすぎる**: チャンクが埋め込みモデルに対して大きすぎる場合、Compliance Settings の `chunk_size` を縮小してください（推奨: 500-1000文字）。

---

## 電子署名Webhookが受信されない

### 症状

署名者が CloudSign や DocuSign でアクションを実行した後、電子署名リクエストのステータスが更新されない。

### 原因と対策

#### 1. Webhook URL がプロバイダに登録されていない

**診断**: プロバイダの開発者コンソールで登録済みのWebhookエンドポイントを確認します。

**対策**: 正しいWebhook URLを登録してください:

```
https://your-site.example.com/api/method/lifegence_business.contract_approval.api.esignature.callback_signature_complete
```

#### 2. Webhook URL がインターネットからアクセスできない

**診断**: Webhookエンドポイントはインターネットから到達可能でなければなりません。ローカル開発環境（`localhost`）ではWebhookを受信できません。

**対策**:

- 本番環境: サイトがパブリックドメインでHTTPS経由でアクセス可能であることを確認してください。
- 開発環境: トンネリングサービス（例: ngrok）を使用してローカル環境を公開します:

  ```bash
  ngrok http 8000
  ```

  ngrok のURLをプロバイダに登録してください。

#### 3. SSL証明書の問題

**診断**: 多くのWebhookプロバイダは有効なSSL証明書を要求します。

**対策**: サイトが有効なSSL証明書を使用していることを確認してください（本番環境では自己署名証明書は不可）。以下で確認:

```bash
curl -I https://your-site.example.com/api/method/lifegence_business.contract_approval.api.esignature.callback_signature_complete
```

#### 4. ファイアウォールが受信リクエストをブロック

**診断**: サーバーのファイアウォールルールを確認します。

**対策**: プロバイダのIPレンジからのHTTPSトラフィック（ポート443）を許可してください。プロバイダのドキュメントでIPホワイトリストを確認してください。

#### 5. ゲストアクセスが制限されている

**診断**: コールバックエンドポイントは `@frappe.whitelist(allow_guest=True)` を使用しています。サーバーレベル（nginx設定等）でゲストアクセスが制限されている場合、コールバックは拒否されます。

**対策**: APIエンドポイントパスがnginxや他のリバースプロキシルールでブロックされていないことを確認してください。エンドポイントは認証なしでアクセス可能である必要があります。

#### 6. 重複イベントの抑制

**診断**: 同じ `provider_event_id` が2回送信された場合、システムは重複を無視します。

**対策**: これは期待される動作です。E-Signature Log でイベントを確認してください。初回のイベントが処理されたがリクエストステータスが更新されなかった場合は、`_update_request_status` のロジックを調査してください。

---

## DMSファイルサイズ制限

### 症状

文書のアップロードがファイルサイズエラーで失敗する。

### 原因と対策

#### 1. DMS Settings のファイルサイズ制限

**診断**: 設定された上限値を確認します。

```python
settings = frappe.get_single("DMS Settings")
print(f"最大ファイルサイズ: {settings.max_file_size_mb} MB")
```

**対策**: DMS Settings の `max_file_size_mb` を増やしてください。

#### 2. Frappe フレームワークのファイルサイズ制限

**診断**: Frappe独自の最大ファイルサイズ設定があります。

**対策**: Frappe の **System Settings** で `max_file_size` フィールド（MB単位）を増やしてください。

#### 3. Nginx のリクエストボディサイズ制限

**診断**: Nginx が "413 Request Entity Too Large" エラーを返す。

**対策**: nginx設定を編集します:

```nginx
# サイトのnginx設定内
client_max_body_size 100m;
```

nginx を再起動:

```bash
sudo systemctl restart nginx
```

#### 4. MariaDB のパケットサイズ制限

**診断**: 非常に大きなファイルが MariaDB の `max_allowed_packet` 設定を超過する場合があります。

**対策**: `/etc/mysql/mariadb.conf.d/50-server.cnf` を編集:

```ini
[mysqld]
max_allowed_packet = 256M
```

MariaDB を再起動:

```bash
sudo systemctl restart mariadb
```

---

## 監査の期限超過通知が送信されない

### 症状

期限を過ぎた是正措置が通知を生成しない、または監査ダッシュボードに期限超過アイテムが表示されない。

### 原因と対策

#### 1. スケジューラが稼働していない

**診断**: Frappe スケジューラの状態を確認します。

```bash
bench --site your-site scheduler status
```

**対策**: スケジューラを有効化・起動します:

```bash
bench --site your-site scheduler enable
bench --site your-site scheduler resume
```

#### 2. スケジュールタスクが登録されていない

**診断**: タスクがスケジューラに登録されているか確認します。

```bash
bench --site your-site show-pending-jobs
```

`lifegence_business.audit.services.corrective_action_service.check_overdue_actions` と `lifegence_business.audit.services.notification_service.send_due_reminders` のエントリを探してください。

**対策**: `bench migrate` を実行してフックを登録します:

```bash
bench --site your-site migrate
```

#### 3. 期限超過チェック頻度の不一致

**診断**: Audit Settings を確認します。

```python
settings = frappe.get_single("Audit Settings")
print(f"期限超過チェック頻度: {settings.overdue_check_frequency}")
print(f"自動リマインダー日数: {settings.auto_reminder_days}")
```

**対策**: `overdue_check_frequency` が "Daily" に設定されていること、`auto_reminder_days` が0より大きいことを確認してください。

#### 4. メールが設定されていない

**診断**: 通知にはFrappeのメール設定が必要です。

**対策**: **Email Account** 設定で送信メールアカウントを設定してください。以下で確認:

```bash
bench --site your-site send-test-email user@example.com
```

#### 5. 是正措置のステータスが不正

**診断**: ステータスが "Open" または "In Progress" かつ期限を過ぎたアクションのみがフラグされます。

```python
from frappe.utils import today
overdue = frappe.get_all("Corrective Action", filters={
    "status": ["in", ["Open", "In Progress"]],
    "due_date": ["<", today()],
}, fields=["name", "action_title", "due_date", "status"])
print(overdue)
```

**対策**: 是正措置のステータスと期日が正しいことを確認してください。

---

## 一般的なトラブルシューティング

### エラーログの確認

Frappe は **Error Log** DocType にエラーを記録します。最近のエラーを確認:

```bash
bench --site your-site console
```

```python
errors = frappe.get_all("Error Log", filters={"seen": 0}, fields=["name", "method", "error"], order_by="creation desc", limit=10)
for e in errors:
    print(f"{e.name}: {e.method}")
    print(e.error[:200])
    print("---")
```

### フック登録の確認

doc_events と scheduler_events が登録されているか確認:

```bash
bench --site your-site console
```

```python
import lifegence_business.hooks as hooks
print("Doc events:", list(hooks.doc_events.keys()))
print("Daily tasks:", hooks.scheduler_events.get("daily", []))
print("Weekly tasks:", hooks.scheduler_events.get("weekly", []))
```

### キャッシュクリア

設定変更が反映されない場合:

```bash
bench --site your-site clear-cache
bench --site your-site clear-website-cache
```

### マイグレーション実行

アプリ更新後は必ずマイグレーションを実行:

```bash
bench --site your-site migrate
```

### アセットの再ビルド

CSSの変更（例: compliance.css）が反映されない場合:

```bash
bench build --app lifegence_business
```

---

## 関連ドキュメント

- [セットアップガイド](setup.md) -- インストールと初期設定
- [モジュールリファレンス](modules.md) -- 詳細なモジュール・APIドキュメント
- [設定リファレンス](configuration.md) -- 設定、ロール、外部サービス
