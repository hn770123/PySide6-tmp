# モダンな企業向けユーザーテーブル設計ガイド

企業ユース（B2B/Enterprise）における、堅牢で拡張性の高いユーザーテーブル（データベーススキーマ）の設計指針をまとめました。セキュリティ、監査、マルチテナント対応を重視しています。

## 1. 基本方針

*   **IDのランダム化**: 連番（Auto Increment）ではなく、UUID（v4またはv7）を採用し、推測不可能性と分散システムへの適応性を確保する。
*   **個人情報の分離**: 認証情報（`users`）とプロフィール情報（`user_profiles`）を分離し、セキュリティリスクの局所化とパフォーマンスの最適化を図る。
*   **論理削除（Soft Delete）**: 監査ログや復元可能性を考慮し、物理削除ではなくフラグ（または削除日時）による論理削除を基本とする。
*   **監査証跡**: 「誰が」「いつ」作成・更新したかを常に記録する。

---

## 2. 推奨テーブル構造

### A. Users テーブル (認証・コア情報)

アカウントの「存在」と「認証」を管理するテーブルです。

| カラム名 | データ型 | 説明・備考 |
| :--- | :--- | :--- |
| **`id`** | UUID / ULID | **主キー**。UUID v7を採用すると時系列ソートが可能になりパフォーマンスに有利。 |
| **`organization_id`** | UUID | **外部キー**。所属組織（テナント）。マルチテナントSaaSでは必須。 |
| **`email`** | VARCHAR(255) | **ユニーク制約**。ログインIDとして使用。すべて小文字化して保存することを推奨。 |
| **`password_hash`** | VARCHAR(255) | パスワードのハッシュ値（Argon2id または bcrypt）。平文は厳禁。 |
| **`status`** | ENUM / VARCHAR | アカウント状態（例: `active`, `inactive`, `suspended`, `locked`, `pending_invite`）。 |
| **`role`** | VARCHAR | 簡易的なロール（`admin`, `member`, `viewer`）。複雑な権限管理が必要な場合は別途 `user_roles` テーブルを作成。 |
| **`email_verified_at`** | TIMESTAMP | メールアドレス確認日時。NULLの場合は未確認。 |
| **`phone_number`** | VARCHAR(20) | 多要素認証(SMS)等で使用する場合。E.164形式で保存。ユニーク制約を検討。 |
| **`two_factor_enabled`** | BOOLEAN | 2要素認証が有効かどうかのフラグ。 |
| **`last_login_at`** | TIMESTAMP | 最終ログイン日時。休眠アカウントの特定に使用。 |
| **`failed_login_attempts`**| INTEGER | 連続ログイン失敗回数。アカウントロック機能に使用。 |
| **`locked_until`** | TIMESTAMP | アカウントロックの解除日時。 |
| **`password_changed_at`** | TIMESTAMP | パスワード最終変更日時。定期変更を促す場合に利用。 |
| **`created_at`** | TIMESTAMP | 作成日時。 |
| **`updated_at`** | TIMESTAMP | 更新日時。 |
| **`deleted_at`** | TIMESTAMP | **論理削除用**。NULLなら有効、日時が入っていれば削除済み。ユニーク制約（Email等）との兼ね合いに注意が必要（部分インデックス等で対応）。 |

### B. User Profiles テーブル (属性情報)

ビジネスロジックで頻繁に変更されるプロフィール情報は別テーブルに分離します。

| カラム名 | データ型 | 説明・備考 |
| :--- | :--- | :--- |
| **`user_id`** | UUID | **主キー 兼 外部キー**。Usersテーブルと 1:1 対応。 |
| **`first_name`** | VARCHAR | 名。 |
| **`last_name`** | VARCHAR | 姓。 |
| **`display_name`** | VARCHAR | 表示名。システム内での表示用。 |
| **`department`** | VARCHAR | 部署名。 |
| **`position`** | VARCHAR | 役職。 |
| **`language`** | VARCHAR(10) | 言語設定（例: `ja-JP`, `en-US`）。ロケール対応用。 |
| **`timezone`** | VARCHAR(50) | タイムゾーン（例: `Asia/Tokyo`）。日時表示の補正用。 |
| **`avatar_url`** | VARCHAR | プロフィール画像のURL。 |

---

## 3. 企業ユースにおける重要な考慮事項

### セキュリティ設計
*   **パスワードハッシュ**: ソルト（Salt）を含むアルゴリズム（Argon2id推奨）を使用する。
*   **監査ログ**: `users` テーブルへの変更履歴（誰がいつ何を書き換えたか）を別途 `audit_logs` テーブルに記録することを強く推奨する。
*   **セッション管理**: データベースにはセッショントークン自体は保存せず（Redis等を利用）、無効化が必要な場合（強制ログアウト）のために `token_version` カラムをUserテーブルに持たせる手法がある。

### コンプライアンスとプライバシー (GDPR/APPI)
*   **同意管理**: 利用規約やプライバシーポリシーへの同意日時・バージョンを記録するテーブル（`user_agreements`）を別途設ける。
*   **データ削除**: 論理削除されたデータに対し、一定期間（例: 30日）経過後に物理削除を行うバッチ処理、または個人情報をマスク（匿名化）する仕組みを実装する。

### インデックス戦略
*   **検索用**: `email`, `organization_id` には必ずインデックスを貼る。
*   **複合インデックス**: マルチテナントの場合、`(organization_id, email)` のような複合インデックスが有効な場合が多い。
*   **部分インデックス**: 論理削除を採用する場合、`email` のユニーク制約は `WHERE deleted_at IS NULL` の条件付きユニークインデックスにする必要がある（DBエンジンによる）。

## 4. SQL例 (PostgreSQL)

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL, -- FK constraint to organizations
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    email_verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- 論理削除されていないユーザーに対してのみEmailのユニーク制約を適用
CREATE UNIQUE INDEX idx_users_email_unique ON users (email) WHERE deleted_at IS NULL;
```
