# Device collection

_This is experimental and may change at any time._

This collection is automatically published at https://home-assistant.github.io/devices/.

Each device is stored in: `devices/<integration>/<device manufacturer>/<device model>/`

The integration, manufacturer and model are the data reported in Home Assistant.

## Adding new devices

Paste the below template to the [template developer tool](https://my.home-assistant.io/redirect/developer_template/) to generate data from your Home Assistant instance.

To get the data into the repo, paste the output in a GitHub issue or share the file with me on Discord (@balloob).

You can also process it yourself and open a PR. To do that, put the output in a CSV file in the `to_process` folder (for example `to_process/my_devices.csv`) and run the `script/process.py` script.

```jinja2
{% set ns = namespace(
  devices=[None],
  ignore_integration=[
    None,
    "hassio",
    "bluetooth",
    "mqtt",
    "esphome"
  ],
  ignore_entry_type=["service"],
  via_devices=[(None, None)]
) %}
{% for state in states -%}
{% set dev_id = device_id(state.entity_id) -%}
{% if dev_id -%}
{% set via_device = device_attr(dev_id, 'via_device_id') -%}
{% if via_device and device_attr(via_device, 'primary_config_entry') -%}
{% set ns.via_devices = ns.via_devices + [(via_device, {
  "sw_version": device_attr(via_device, 'sw_version'),
  "hw_version": device_attr(via_device, 'hw_version'),
  "integration": device_attr(via_device, 'primary_config_entry') | config_entry_attr('domain'),
  "model": device_attr(via_device, 'model'),
  "manufacturer": device_attr(via_device, 'manufacturer'),
})] -%}
{% endif -%}
{% endif -%}
{% endfor -%}
{% set ns.via_devices = dict.from_keys(ns.via_devices) %}

integration,manufacturer,model,sw_version,hw_version,via_device,has_suggested_area,has_configuration_url,entry_type,is_via_device
{% for state in states -%}
{% set dev_id = device_id(state.entity_id) -%}
{% if dev_id not in ns.devices -%}
{% set ns.devices = ns.devices + [dev_id] -%}
{% if device_attr(dev_id, 'primary_config_entry') and
   config_entry_attr(device_attr(dev_id, 'primary_config_entry'), 'domain') not in ns.ignore_integration and
   device_attr(dev_id, 'manufacturer') and
   device_attr(dev_id, 'model') and
   device_attr(dev_id, 'entry_type') not in ns.ignore_entry_type -%}
{{- integration }},
{#-#}"{{ device_attr(dev_id, 'manufacturer') }}",
{#-#}"{{ device_attr(dev_id, 'model') }}",
{#-#}"{{ device_attr(dev_id, 'sw_version') }}",
{#-#}"{{ device_attr(dev_id, 'hw_version') }}",
{#-#}"{{- ns.via_devices[device_attr(dev_id, 'via_device_id')] | to_json | base64_encode }}",
{{- device_attr(dev_id, 'suggested_area') != None }},
{{- device_attr(dev_id, 'configuration_url') != None }},
{{- device_attr(dev_id, 'entry_type') }},
{{- dev_id in ns.via_devices }}
{% endif -%}
{% endif -%}
{% endfor %}
```
