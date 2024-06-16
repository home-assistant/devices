# Device collection

_This is experimental and may change at any time._

Each device is stored in: `devices/<integration>/<device manufacturer>/<device model>/`

The integration, manufacturer and model are the data reported in Home Assistant.

## Adding new devices

Paste the below template to the template developer tool to generate data from your Home Assistant instance.

To get the data into the repo, paste the output in a GitHub issue or share the file with me on Discord (@balloob).

You can also process it yourself and open a PR. To do that, put the output in the `to_process` folder and run the `script/process.py` script.

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
  ignore_entry_type=["service"]
) %}

integration,manufacturer,model,sw_version,hw_version,has_via_device,has_suggested_area,has_configuration_url,entry_type
{% for state in states -%}
{% set dev_id = device_id(state.entity_id) -%}
{% if dev_id not in ns.devices -%}
{% set ns.devices = ns.devices + [dev_id] -%}
{# temporary until primary integration is included -#}
{% set ns.integration = None -%}
{% for ident in device_attr(dev_id, 'identifiers') -%}
{% set ns.integration = ident[0] -%}
{% endfor -%}
{% if ns.integration not in ns.ignore_integration and
   device_attr(dev_id, 'manufacturer') and
   device_attr(dev_id, 'model') and
   device_attr(dev_id, 'entry_type') not in ns.ignore_entry_type -%}
{{- ns.integration }},
{#-#}"{{ device_attr(dev_id, 'manufacturer') }}",
{#-#}"{{ device_attr(dev_id, 'model') }}",
{#-#}"{{ device_attr(dev_id, 'sw_version') }}",
{#-#}"{{ device_attr(dev_id, 'hw_version') }}",
{{- device_attr(dev_id, 'via_device_id') != None }},
{{- device_attr(dev_id, 'suggested_area') != None }},
{{- device_attr(dev_id, 'configuration_url') != None }},
{{- device_attr(dev_id, 'entry_type') }}
{% endif -%}
{% endif -%}
{% endfor %}
```
