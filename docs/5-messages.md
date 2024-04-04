# チャットメッセージの作成と管理のフロー

このセクションでは、chat-serviceのチャットメッセージの作成と管理に関連するREST APIのシーケンスを説明します。

## 1. すべてのメッセージの取得

認証済みのユーザーは、特定のチャットルームのメッセージのリストを取得するためにこのエンドポイントを使用します。

```http
GET /api/messages/chat/{{chat_id}}?offset=0&limit=10
Authorization: Bearer アクセストークン
```

## 2. メッセージの作成

ユーザーは新しいメッセージをチャットルームに投稿することができます。チャットルームに入室しなくても外部連携的な用途でメッセージを投稿できます。

```http
POST /api/messages/chat/{{chat_id}}
Authorization: Bearer アクセストークン
Content-Type: application/json

{
  "content": "Sample message"
}
```

## 3. メッセージの削除

ユーザーは自分のメッセージを削除することができます。

```http
DELETE /api/messages/{{message_id}}
Authorization: Bearer アクセストークン
```