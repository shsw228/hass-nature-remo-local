# Home Assistant Dashboard 例

## 目的
`climate` entity を Home Assistant 標準 UI で見やすく表示する。

公式ドキュメント:
- Thermostat card: https://www.home-assistant.io/dashboards/thermostat/
- Dashboard card features: https://www.home-assistant.io/dashboards/features/

## 第一候補: Thermostat card
`thermostat` card は climate entity 向けの標準カードで、温度変更とモード変更がしやすい。
`show_current_as_primary: true` を使うと、設定温度ではなく現在温度を大きく出せる。

```yaml
type: thermostat
entity: climate.living_room_aircon
name: Living Room AC
show_current_as_primary: true
features:
  - type: climate-hvac-modes
    hvac_modes:
      - cool
      - heat
      - dry
      - fan_only
      - auto
      - "off"
  - type: target-temperature
  - type: climate-fan-modes
    style: dropdown
```

## 比較用: Tile card
`tile` card は一覧性が高く、複数の climate を並べるときに向く。

```yaml
type: tile
entity: climate.living_room_aircon
name: Living Room AC
features_position: bottom
features:
  - type: climate-hvac-modes
    style: icons
    hvac_modes:
      - cool
      - heat
      - dry
      - fan_only
      - auto
      - "off"
  - type: target-temperature
```

## 制約
- `hvac_action` の文字を大きく出すかどうかは、基本的に Home Assistant 標準カード側の見た目に依存する。
- integration 側で制御できるのは `hvac_mode` や `hvac_action` を正しく返すところまで。
- 「冷房中」「待機中」をもっと強調したい場合は、補助 sensor を追加して別カードで見せる方が現実的。

## 試し方
1. ダッシュボードを編集する
2. `Manual card` を追加する
3. 上の YAML を貼る
4. `entity` を実際の Nature Remo の climate entity ID に置き換える
