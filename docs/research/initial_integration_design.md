# 初版 Integration 設計案

## 前提
- 現時点では、公開 API 仕様から Cloud API で既存 signal の raw IR を取得する経路は確認できていない。
- Local API は `/messages` による raw IR 送受信が中心。
- そのため、初版は Cloud API を正規ルートにし、Local API は後続拡張とする。

## 初版の責務分割
### Cloud API
- デバイス一覧・ appliance 一覧の取得
- エアコン状態の取得
- 照明状態の取得
- 温度・湿度などセンサ値の取得
- エアコン、照明の実行

### Local API
- 初版では必須機能にしない
- 将来的に raw IR の再送機能を追加するときの拡張ポイントとして残す

## Home Assistant 上の構成案
- domain: `nature_remo_local`
- config entry ベース
- 共有更新処理は `DataUpdateCoordinator`
- platform は少なくとも `climate` `light` `sensor`

想定ディレクトリ:

```text
custom_components/nature_remo_local/
  __init__.py
  manifest.json
  const.py
  config_flow.py
  coordinator.py
  api.py
  climate.py
  light.py
  sensor.py
```

## データ取得方針
- 定期 poll は Cloud API の `devices` と `appliances` をまとめて取得する
- coordinator が API レスポンスを正規化し、各 entity は coordinator データだけを読む
- 実行後は即座に coordinator の再取得を走らせ、UI 上の反映遅れを最小化する

## 初期 entity 方針
### `climate`
- Nature Remo 上で aircon として表現される appliance
- 主に `hvac_mode` `target_temperature` `current_temperature` を出す

### `light`
- Nature Remo 上で light として表現される appliance
- まずは on/off を優先し、brightness や mode は API 実態を見て後追い

### `sensor`
- Remo device から取れる気温
- Remo device から取れる湿度
- 必要なら照度・人感・電力量は後から追加

## Config Flow 案
### 初回フロー
1. Cloud access token を入力
2. Cloud API へ接続して token を検証
3. 取得できたデバイス数と appliance 数を表示して entry 作成

### Options Flow
- poll interval
- どの appliance / device を有効化するか
- 将来: Local API を有効にするか
- 将来: Local host を手入力するか Bonjour discovery を使うか

## 実装順の提案
1. `config_flow` と `manifest` を作る
2. Cloud API client を作る
3. coordinator で `devices` / `appliances` を正規化する
4. `sensor` を先に出す
5. `climate` を追加する
6. `light` を追加する
7. Local API の扱いを別フェーズで検討する

## 設計上の注意
- token や host は `ConfigEntry.data` に保存し、可変値は `options` に逃がす
- entity は API を直接叩かず coordinator 経由に寄せる
- Local API は hidden API の有無がはっきりするまで core 設計に混ぜない

## 参考
- Home Assistant manifest: https://developers.home-assistant.io/docs/creating_integration_manifest/
- Home Assistant file structure: https://developers.home-assistant.io/docs/creating_integration_file_structure/
- Home Assistant config flow: https://developers.home-assistant.io/docs/config_entries_config_flow_handler/
- Home Assistant DataUpdateCoordinator: https://developers.home-assistant.io/docs/integration_fetching_data/
