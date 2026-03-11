# Home Assistant Dashboard 例

## 目的
`climate` entity を Home Assistant 標準 UI で見やすく表示する。

公式ドキュメント:
- Thermostat card: https://www.home-assistant.io/dashboards/thermostat/
- Dashboard card features: https://www.home-assistant.io/dashboards/features/
- Button card: https://www.home-assistant.io/dashboards/button/

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

## ライトの Bright / Dark ボタン
`Bright` / `Dark` のような相対操作は、標準の `light` brightness UI よりも `button` entity のまま見せる方が自然。
標準 UI なら `horizontal-stack` で 2 つ並べるのが一番分かりやすい。

```yaml
type: horizontal-stack
cards:
  - type: button
    entity: button.living_room_light_bright
    name: Bright
    icon: mdi:brightness-7
    tap_action:
      action: toggle
  - type: button
    entity: button.living_room_light_dark
    name: Dark
    icon: mdi:brightness-5
    tap_action:
      action: toggle
```

複数のライトボタンをまとめて並べるなら `grid` でもよい。

```yaml
type: grid
columns: 2
square: false
cards:
  - type: button
    entity: button.living_room_light_bright
    name: Bright
    icon: mdi:brightness-7
  - type: button
    entity: button.living_room_light_dark
    name: Dark
    icon: mdi:brightness-5
  - type: button
    entity: button.living_room_light_night
    name: Night
    icon: mdi:weather-night
  - type: button
    entity: button.living_room_light_full
    name: Full
    icon: mdi:lightbulb-on
```

`toggle` は `button` entity では実質 `press` と同じ扱いになるため、標準の `button` card と組み合わせると押しやすい。

## 制約
- `hvac_action` の文字を大きく出すかどうかは、基本的に Home Assistant 標準カード側の見た目に依存する。
- integration 側で制御できるのは `hvac_mode` や `hvac_action` を正しく返すところまで。
- 「冷房中」「待機中」をもっと強調したい場合は、補助 sensor を追加して別カードで見せる方が現実的。
- `Bright` / `Dark` は相対操作なので、標準の brightness slider に自然には落とし込みにくい。
- そのため、標準 UI では `button` card を並べる構成が最も無理が少ない。

## 試し方
1. ダッシュボードを編集する
2. `Manual card` を追加する
3. 上の YAML を貼る
4. `entity` を実際の Nature Remo の climate entity ID に置き換える
