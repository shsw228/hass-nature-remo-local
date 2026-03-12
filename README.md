# Nature Remo Local for Home Assistant

[![Latest Release](https://img.shields.io/github/v/release/shsw228/hass-nature-remo-local?sort=semver)](https://github.com/shsw228/hass-nature-remo-local/releases/latest)

Custom Home Assistant integration for [Nature Remo](https://nature.global/), focused on a clean config flow, HACS installation, and a Cloud API based first release.

This repository is rebuilding the integration from scratch for newer Home Assistant versions. The current implementation uses the Nature Remo Cloud API for discovery, state updates, and control. Local API support is planned separately once the practical control path is clearer.

Current release: `1.0.0`

## Current Features

- Config Flow based setup from Home Assistant UI
- HACS compatible repository layout
- Temperature and humidity sensors from Remo devices
- `climate` entities for air conditioners
- `light` entities for supported lighting appliances
- `button` entities for individual lighting appliance buttons
- Rate limit aware polling and post-action refresh control

## Installation

### HACS

1. Open `HACS -> Integrations -> Custom repositories`
2. Add this repository URL as category `Integration`
3. Install `Nature Remo Local`
4. Restart Home Assistant

### Manual

Copy `custom_components/nature_remo_local` into your Home Assistant `custom_components` directory, then restart Home Assistant.

## Configuration

This integration is configured from the UI only.

1. Go to `Settings -> Devices & Services`
2. Click `Add Integration`
3. Search for `Nature Remo Local`
4. Enter your Nature Remo Cloud access token
5. Choose an update interval

The token needs at least:

- `basic.read` for device and state retrieval
- `sendir` for air conditioner and light control

## Supported Entities

- `sensor`: temperature, humidity
- `sensor`: temperature, humidity, rate limit diagnostics
- `climate`: air conditioners
- `light`: lights supported by Nature Remo Cloud API
- `button`: individual buttons returned for supported light appliances

## Notes

- The current release is Cloud API based. Local API control is not enabled yet.
- Default polling is `180` seconds.
- Nature rate limits requests per account. The integration reads `X-Rate-Limit-*` headers and reduces refresh pressure when the remaining budget is low.
- Diagnostic sensors expose the latest `X-Rate-Limit-Limit`, `X-Rate-Limit-Remaining`, and `X-Rate-Limit-Reset` values.
- Light on/off currently depends on matching known button names from the Nature Remo API response.
- Light appliances also expose each available Nature Remo button as a Home Assistant `button` entity.

## Known Limitations

- Local API based control is not implemented in this release.
- `climate` `hvac_action` is inferred from mode and temperature difference, so it may show `idle` when the air conditioner is powered on but not actively cooling or heating.
- `light` brightness is exposed as Nature Remo button actions rather than a native Home Assistant brightness slider.
- Available light button names depend on the appliance data returned by the Nature Remo Cloud API.

## Dashboard

For a better climate UI, the standard Home Assistant `thermostat` card is usually a better fit than `tile`.

Example dashboard snippets:

- [`docs/research/home_assistant_dashboard_examples.md`](docs/research/home_assistant_dashboard_examples.md)

## Development Notes

Design and API research notes are kept under [`docs/research/`](docs/research/).

- [`docs/research/initial_integration_design.md`](docs/research/initial_integration_design.md)
- [`docs/research/nature_remo_integration_notes.md`](docs/research/nature_remo_integration_notes.md)

Saved API specs:

- [`docs/apis/cloud.swagger.json`](docs/apis/cloud.swagger.json)
- [`docs/apis/local.swagger.yml`](docs/apis/local.swagger.yml)

## Support

If setup or entity behavior fails, please open an issue with the Home Assistant log output and the affected entity type (`sensor`, `climate`, `light`, or `button`).

## License

MIT
