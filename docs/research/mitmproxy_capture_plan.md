# mitmproxy 調査計画

## 目的
Nature Home アプリが、公開 Swagger にない API を使って raw IR (`message`) を取得していないか確認する。

## まず試す方法
mitmproxy 公式では、外部デバイスの観測は Regular Proxy を最初に試すのが推奨。

1. Mac で `mitmweb` または `mitmproxy` を起動する
2. iPhone を同じ Wi-Fi に接続する
3. iPhone の Wi-Fi 詳細設定で HTTP Proxy を `Manual` にし、Mac の IP と `8080` を指定する
4. iPhone の Safari で `http://mitm.it` を開き、mitmproxy CA をインストールする
5. `設定 > 一般 > 情報 > 証明書信頼設定` で mitmproxy 証明書をフルトラストにする
6. Nature Home アプリを起動し、Remo / signal / appliance まわりの画面を操作する

## 期待する観測ポイント
- `api.nature.global` 以外の host が出るか
- `signals` 一覧取得のレスポンスに raw IR が含まれるか
- signal 詳細取得のような未公開 endpoint があるか
- エアコンや照明操作時に Cloud API 以外の通信が出るか

## 見つけたいキーワード
- `message`
- `signals`
- `appliances`
- `aircon_settings`
- `light`
- `send`

## 注意点
- アプリが OS の proxy 設定を無視する場合、Regular Proxy では流れない
- アプリが certificate pinning をしている場合、接続失敗または TLS 復号不可になる
- その場合は mitmproxy の WireGuard / Transparent 方式や、別の動的解析手段を検討する

## 取れたら保存したい情報
- request URL
- method
- request body
- response body
- 必要ヘッダー

## 調査後の判断
- raw IR を返す非公開 API が見つかれば、Cloud から取り込んで Local `/messages` に流す設計を再検討できる
- 見つからなければ、Local 学習結果を integration 側で保持するか、初版は Cloud 実行を正規ルートにする
