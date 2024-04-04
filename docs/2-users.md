# ユーザー作成と更新のフロー

このセクションでは、chat-serviceのユーザー作成と更新に関連するREST APIのシーケンスを説明します。

## 1. ユーザー情報の取得

認証済みのユーザーは、自分の情報を取得するためにこのエンドポイントを使用します。

```http
GET /api/users
Authorization: Bearer アクセストークン
```

## 2. ユーザー情報の更新

ユーザーは自分の情報を更新することができます。例えば、ユーザー名、表示名の可視性、通知の種類などです。このAPIには連打防止にスロットリングが設定されています。

```http
PUT /api/users
Authorization: Bearer アクセストークン
Content-Type: application/json

{
  "is_name_visible": false,
  "username": "testuser12345",
  "first_name": "John",
  "last_name": "Smith",
  "new_email": null,
  "notification_type": "mobile_push"
}
```

## 3. メールアドレスの確認

ユーザーはメールアドレスを確認するために、確認コードを送信する必要があります。このAPIには連打防止にスロットリングが設定されています。

```http
PATCH /api/users/verify_email
Authorization: Bearer アクセストークン
Content-Type: application/json

{
  "code": "123456"
}
```