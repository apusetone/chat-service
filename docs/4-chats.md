# チャットルームの作成と管理のフロー

このセクションでは、chat-serviceのチャットルームの作成と管理に関連するREST APIのシーケンスを説明します。

## 1. すべてのチャットの取得

認証済みのユーザーは、既存のチャットルームのリストを取得するためにこのエンドポイントを使用します。

```http
GET /api/chats?offset=0&limit=10&desc=true
Authorization: Bearer アクセストークン
```

## 2. チャットルームの作成

ユーザーは新しいチャットルームを作成することができます。作成時には、ルーム名と参加者のリストを指定する必要があります。

```http
POST /api/chats
Authorization: Bearer アクセストークン
Content-Type: application/json

{
  "name": "New room",
  "participant_names": [
    "user1", "user2", "user3"
  ]
}
```

## 3. チャットルームの参加者の取得

特定のチャットルームの参加者のリストを取得するためにこのエンドポイントを使用します。

```http
GET /api/chats/{{chat_id}}/participants
Authorization: Bearer アクセストークン
```

## 4. チャットルームの削除

ユーザーは特定のチャットルームを削除することができます。

```http
DELETE /api/chats/{{chat_id}}
Authorization: Bearer アクセストークン
```
