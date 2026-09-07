# StormDesk for Home Assistant

A custom integration for [StormDesk](https://github.com/d4vid87/stormdesk) — a self-hosted
dashboard for your own weather station.

Polls the dashboard's `/api/v1` over your LAN. No cloud, no account, no broker.

## Do you need this?

Not necessarily, and it is worth being clear about that.

StormDesk already publishes to Home Assistant over MQTT, with discovery, and that path needs no
custom code at all. If you have a broker, start there — it is in the
[StormDesk docs](https://github.com/d4vid87/stormdesk/blob/main/docs/homeassistant.md).

Install this integration if:

- **you have no MQTT broker** and would rather not run one for a single station, or
- **you want a weather entity.** Home Assistant's MQTT discovery has no weather platform, so the
  MQTT route gives you a pile of sensors and no forecast card. This adds a real weather entity —
  current conditions from the station in your garden, five-day forecast, drawn by the standard
  forecast card.

Running both is fine. They are separate devices and neither writes to the other's entities.

## Install

**HACS** → Integrations → ⋮ → Custom repositories → `d4vid87/ha-stormdesk`, category
*Integration* → Install → restart Home Assistant.

**By hand** → copy `custom_components/stormdesk` into your `config/custom_components/` →
restart.

## Set up

StormDesk announces itself on the LAN, so Home Assistant usually offers it under
**Settings → Devices & Services** without being asked. Accept it and you are done.

If it doesn't appear — a dashboard on another subnet, or a container without host networking,
where mDNS doesn't carry — add it by hand: **Add Integration → StormDesk**, then the address you
open in a browser (`192.168.1.20:8088`, or with a scheme if it isn't plain http).

The address has to be the dashboard's own server. A static copy of the page served by nginx has
no `/api/v1` behind it, and setup will say so rather than half-working.

## What you get

A weather entity, and one sensor per reading **your station actually takes** — a station with no
lightning sensor doesn't get three entities permanently showing *unknown*.

`Temperature` · `Feels like` · `Humidity` · `Pressure` · `Pressure trend` · `Wind` · `Gust` ·
`Wind lull` · `Wind direction` · `UV index` · `Solar radiation` · `Illuminance` · `Rain` ·
`Rain today` · `Lightning strikes` · `Lightning distance` · `Battery` *(disabled by default)*

Everything arrives in SI — °C, m/s, hPa, mm — and Home Assistant converts for display. That is
deliberate: a units switch on the dashboard must never rewrite months of Home Assistant history.

`Rain today` is a `total_increasing` sensor, so its reset at local midnight reads as a new day
rather than as a meter running backwards.

There is also a **StormDesk** entry in the sidebar, framing the dashboard itself. Hide it the way
you hide any sidebar item — long-press the Home Assistant logo — if you would rather not have it.
An iframe rather than a custom Lovelace card on purpose: the dashboard is a whole application with
its own layout engine, and reimplementing part of it as a card would be two things to keep in step.

> A Home Assistant served over `https` cannot frame a dashboard served over `http` — browsers
> block the mixed content and the panel comes up blank. That is a browser rule, not something this
> can work around.

## Polling

Once a minute. The archive gains a row a minute at best, and one request serves every entity —
twenty sensors each polling for themselves would be rude to a machine that is also drawing a radar
loop.

## Blueprints

Three importable automations ship with StormDesk itself:
[`blueprints/automation/stormdesk`](https://github.com/d4vid87/stormdesk/tree/main/blueprints/automation/stormdesk).
They are written against the MQTT sensors; point them at these entities instead if that is the
route you took.

## Troubleshooting

**"Nothing at that address answered as a StormDesk."** Open `http://<address>/api/v1` in a
browser. You should get JSON starting `{"api":1`. If you get the dashboard's HTML, the address is
right but you are on a static host with no server behind it. If you get nothing, it's the address.

**Entities go unavailable.** The integration reports unavailable when it cannot reach the
dashboard — check the machine running it is awake. Note that a station that has stopped reporting
is a *different* problem: the entities keep their last values, because `/api/v1` keeps answering
with the newest row it has. The dashboard's own Diagnostics panel is where that shows up.

**Wind looks wrong.** Home Assistant is converting m/s into your display unit. Change it per
entity under the entity's settings if you want a different one.

## Licence

MIT, same as StormDesk.
