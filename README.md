# Py-Hue

## Control your [Phillips Hue Smart Plug](https://www.philips-hue.com/en-gb/p/hue-smart-plug/8719514342323) via Bluetooth

### Status: WIP

Vaguely based on [this dotnet project](https://github.com/kcede/plughub).
The Smart plug is a Bluetooth Low Energy device. It advertises a Power State Characteristic `932c32bd-0002-47a2-835a-a8d455b859dd`
which can be set to `0x00` when off and `0x01` when on.

This has been developed on Linux with a smart plug with model number LOM009 and Software Revision 1.104.2.
I haven't tested it on other environments.

This project contains a FastAPI server which exposes two endpoints:

- `/devices` - GET - return all detected bluetooth devices which might be Phillips Hue Smart Plugs
- `/devices/{uuid}/{activate|deactivate|toggle}` - GET - attempt to activate|deactivate|toggle the state of the device with the Bluetooth UUID `uuid`

This project is built with [poetry](https://github.com/python-poetry/poetry)


