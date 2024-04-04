# 認証フロー

このセクションでは、認証プロセスに関連するREST APIのシーケンスを説明します。

## 1. ログイン

ユーザーはメールアドレスを使用してログインを試みます。

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com"
}
```

成功すると、一時的な認証トークンが返されると同時にメールアドレス宛に6桁の2FAコードが送信されます。このAPIには連打防止にスロットリングが設定されています。

## 2. 二要素認証 (2FA)

次に、ユーザーは2FAコードと一時トークンを使用して二要素認証を行います。

```http
POST /api/auth/2fa
Content-Type: application/json

{
  "code": "123456",
  "token": "一時トークン"
}
```

このステップが成功すると、アクセストークンとリフレッシュトークンが提供されます。このAPIには連打防止にスロットリングが設定されています。

## 3. トークンの更新

リフレッシュトークンを使用してアクセストークンを更新できます。

```http
POST /api/auth/refresh
Authorization: Bearer リフレッシュトークン
```

新しいアクセストークンが返されます。このAPIには連打防止にスロットリングが設定されています。

## 4. ログアウト

アクセストークンを使用してログアウトします。リフレッシュトークンも一緒に送信する必要があります。

```http
POST /api/auth/logout
Authorization: Bearer アクセストークン
Content-Type: application/json

{
  "refresh_token": "リフレッシュトークン"
}
```

## 5. アカウントの削除

最後に、アクセストークンを使用してアカウントを削除できます。

```http
DELETE /api/auth/unregister
Authorization: Bearer アクセストークン
```
