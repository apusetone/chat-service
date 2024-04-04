# chat-service

This is a chating service project of Async Web API with FastAPI + SQLAlchemy 2.0.
It includes asynchronous DB access using asyncpg and some test code covering them.

# Setup

## Installation and quick start up

```shell
$ direnv allow # set your secret to .env
$ make build
$ make up
$ make migrate
$ make test
```

You can now access [localhost:8000/docs](http://localhost:8000/docs) to see the API documentation.

# Run realtime chat server

```shell
$ make up
$ wscat -c ws://localhost:8000/ws/messages/chat/{{chat_id}} -H "Authorization: Bearer {{access_token}}"
Connected (press CTRL+C to quit)
> Hello world
< {"id":18,"sender_id":3,"content":"Hello world","created_at":"2024-04-03T15:15:35.571731","read_by_list":[]}
```

# Specification

 - [認証フロー](./docs/1-auth.md)

 - [ユーザー作成と更新のフロー](./docs/2-users.md)

 - [プッシュ通知の設定のフロー](./docs/3-sessions.md)

 - [チャットルームの作成と管理のフロー](./docs/4-chats.md)

 - [チャットメッセージの作成と管理のフロー](./docs/5-messages.md)

 - [リアルタイムチャット機能](./docs/6-realtime-chatting.md)

 - [インフラ構成](./docs/7-infra.md)

 - [リアルタイムチャット機能](./docs/6-realtime-chatting.md)

# Future issues

- [ ] テストについての不足

  - websocketのテスト全般

  - modelsのテスト全般

  - viewsのテスト

    - 異常系

    - Warning箇所の修正

    - スロットリングを利用しているviewテストをskipしている

    - awsクライアントによる通知送信しているが、未テスト

- [ ] ロギングについての不足

  - req/res内容をマスクした上での表示

  - 

- [ ] Redisについての不足

  - トークン周辺の暗号化が乏しい

- [ ] 機能についての不足

  - 失効したデバイストークンを利用してpublishした際に、返却されるバウンス処理、サーバーから情報を削除する

  - SNS/Email送信履歴の保存、BigQueryなど別サービスでDBに格納

  - awsクライアントによる通知送信しているが、未テスト

- [ ] APIのレスポンス形式について

  - リクエスト形式を誤って実行したときなどにおいて、FastAPIと分かる422エラーとBodyが返却されるので隠蔽が必要

  - 500エラーの際にコード箇所が表示されるので隠蔽が必要

- [ ] アーキテクチャについて

  - websocketでのrouterを設定、viewsの正しい呼び方

  - .envファイルが混在しているため、整理が必要
