# Nature Remo Integration 調査メモ

## 現状
- このリポジトリは初期状態で、実装コードは未作成。
- 参考実装 `hass-nature-remo` は Cloud API 前提の古い custom integration で、YAML の `access_token` を使って `appliances` と `devices` を定期取得する構成。
- Home Assistant の現行方針では、custom integration は `custom_components/<domain>/` 配下に置き、`config_flow.py` と config entry を使うのが前提。

## 保存した API 仕様
- Cloud API: [`docs/apis/cloud.swagger.json`](/Users/hume/ghq/github.com/shsw228/hass-nature-remo-local/docs/apis/cloud.swagger.json)
- Local API YAML: [`docs/apis/local.swagger.yml`](/Users/hume/ghq/github.com/shsw228/hass-nature-remo-local/docs/apis/local.swagger.yml)
- Local API JSON 変換版: [`docs/apis/local.swagger.json`](/Users/hume/ghq/github.com/shsw228/hass-nature-remo-local/docs/apis/local.swagger.json)

## 公式 API から見えたこと
### Cloud API
- OpenAPI `3.0.3`、公開サーバーは `https://api.nature.global`。
- `appliances` `devices` `signals` `aircon_settings` `light` など、Home Assistant 連携に必要そうな高レベル API が揃っている。
- OAuth2 / Bearer token 前提。既存 repo では `Authorization: Bearer <token>` でアクセスしている。
- `signals` の取得系 response では `id` `name` `image` は見えるが、raw IR の `message` は返ってこない。
- raw IR の `message` は signal 作成時の request parameter としては存在する。
- つまり、公開 Cloud API 仕様だけでは「既存 signal の raw IR を読み戻して Local API に流す」経路は見えていない。

### Local API
- 公開仕様は Swagger `2.0`。
- 現在の公開 Swagger で確認できる endpoint は `/messages` のみ。
- `/messages` は IR 生データの取得・送信 API で、`X-Requested-With` ヘッダーが必須。
- ドキュメント上は Bonjour (`_remo._tcp`) による発見を前提にしている。

## 設計の仮説
- 「Cloud API で状態取得、Local API で実行」は方向として自然。
- ただし、公開されている Local API だけを見る限り、ローカルでできるのは生 IR 送受信であり、Cloud API のような `aircon_settings` や `light` 相当の高レベル操作は見えていない。
- さらに、公開されている Cloud API 仕様だけでは、既存 signal から raw IR を読み戻す動線は確認できていない。
- そのため、初期設計では「状態取得は Cloud」「ローカル実行は raw IR ベースで本当に成立するか」を最初の検証項目に置くべき。
- Local 実行後に Cloud を再取得して状態を寄せる案は妥当。ただし API rate limit と反映遅延の確認が必要。

## 初期対象 entity
- `climate`: エアコン
- `light`: 照明
- `sensor`: 気温、湿度

## Config Flow とは
- Home Assistant の UI から integration を追加するための設定ウィザード。
- `config_flow.py` で入力手順を定義し、結果を config entry として保存する。
- YAML より安全で、将来の設定移行もしやすい。

## この integration での Config Flow 案
1. ユーザーが Cloud token を入力する。
2. Cloud API で token を検証し、利用可能な Remo / appliance 一覧を取得する。
3. Local を使う場合は、Bonjour 発見または手入力ホストで `/messages` 疎通確認を行う。
4. config entry には token、接続モード、対象デバイス、poll 間隔などを保存する。
5. 詳細設定は options flow に逃がす。

## 未解決事項
- Local API で raw IR 以外の公開 endpoint が存在するか。
- Cloud API で既存 signal / appliance から raw IR を取得できる非公開または別経路があるか。
- Cloud API の rate limit と、Local 実行後に何秒後再同期するのが妥当か。
- 1 config entry を「Nature アカウント単位」にするか、「Remo デバイス単位」にするか。
- 照明を `light` として扱えるか、あるいは signal ベースの `button` / `select` に寄せるべきか。

## 次の調査候補
- Nature Home アプリ通信の観測で、非公開 endpoint や raw IR 取得 API があるか確認する。
- 手順メモ: [`docs/research/mitmproxy_capture_plan.md`](/Users/hume/ghq/github.com/shsw228/hass-nature-remo-local/docs/research/mitmproxy_capture_plan.md)
- もし非公開取得 API が無ければ、Local `/messages` で学習した raw IR を integration 側で保持する設計に切り替える。
- 高レベル制御が必要なエアコンは、Cloud API 実行を初版の正規ルートにする案を残す。
- 初版設計案: [`docs/research/initial_integration_design.md`](/Users/hume/ghq/github.com/shsw228/hass-nature-remo-local/docs/research/initial_integration_design.md)
