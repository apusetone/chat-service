# プッシュ通知の設定

このセクションでは、chat-serviceにおけるプッシュ通知の設定に関連するREST APIのシーケンスを説明します。

## 1. セッションの更新

二要素認証によるログインが成功した後、モバイルユーザーはアクセストークン、リフレッシュトークン、デバイストークン、およびプラットフォームタイプ（例：android）を`/api/sessions`エンドポイントにPUTリクエストとして送信し、セッション情報を更新します。

```http
PUT {{endpoint}}/api/sessions
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
  "refresh_token": "{{refresh_token}}",
  "device_token": "5dcaed99-e1e0-44dc-bde2-b96188b99e9e",
  "platform_type": "android"
}
```

この手順により、サーバーはユーザーのデバイスにプッシュ通知を送信するための`device_token`を受け取ります。これにより、ユーザーがチャットルームからオフラインの場合でも重要なメッセージやアラートを受け取ることができる想定です。