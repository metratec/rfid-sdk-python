# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`metratec_rfid` - asyncio library to control metraTec RFID readers over serial or TCP. Pure Python, no test suite, hardware required for any real verification.

Runtime dependencies are pinned: `pyserial==3.5`, `pyserial_asyncio==0.6`.

## Commands

```bash
# environment (README convention: venv in ./env)
python3 -m venv env && source env/bin/activate
python -m pip install -r requirements.txt
python -m pip install .            # or -e . for development

# build distributables
python -m pip install wheel twine setuptools
python setup.py sdist bdist_wheel

# documentation (sphinx)
cd docs
python -m pip install -r ../requirements.txt -r requirements.txt
make html                          # output in docs/build/html

# class diagrams (pylint/pyreverse)
pyreverse -o png metratec_rfid
pyreverse -o png -c metratec_rfid.pulsar_lr.PulsarLR metratec_rfid
```

### Verification

There are no automated tests. The `examples/` folder is the test harness and requires a physical reader:

```bash
python examples/inventory_minimal_cmd.py DeskIdUhfv2 /dev/ttyUSB0
python examples/inventory_fetch_example.py PulsarLR 192.168.2.153
```

Most examples take `<ReaderClassName> <port-or-ip>` via `examples/example_utils.py`. Without hardware, changes can only be reviewed statically - say so rather than claiming a change works.

## Architecture

### Layers

```
BaseClass (status_class.py)         logger + status dict + status callback
  RfidReader (reader.py)            lifecycle, watchdog, response buffer, inventory cache
    ReaderAscii (reader_ascii.py)   legacy line protocol, separator "\r"
      UhfReaderAscii / HfReaderAscii
    ReaderAT (reader_at.py)         AT command protocol, separator "\n"
      UhfReaderAT -> UhfReaderATMulti (multiplex/multi-antenna readers)
      NfcReaderAT
```

Concrete device classes (`pulsar_lr.py`, `qrg2.py`, `deskid_uhf.py`, ...) are thin: they pick a `Connection`, set device defaults, and combine a protocol class with optional AT mixins `ReaderATSound`, `ReaderATIO`, `ReaderATHID`.

`Connection` (`connection/`) is callback-driven, not awaited: `SerialConnection` and `SocketConnection` push into `set_cb_connection_made / _lost / _data_received`. `PulsarLRBase.__init__` picks serial vs socket by inspecting the address string per platform.

`Tag` subclasses `dict` - `UhfTag`, `HfTag`, `ISO15Tag`, `ISO14ATag`, `HfTagInfo`. Accessors are just typed dict get/set, so tags serialize directly.

### Connect lifecycle

`connect()` -> connection established -> `_connection_made` sets status BUSY and spawns `_config_device()`, which runs `_prepare_reader_communication()` (protocol handshake: ATE1 echo + stop inventory for AT; BRK/WAK/EOF dance for ASCII) then `_config_reader()` (reads reader info, validates it, caches into `self._config`), then sets status RUNNING and starts the `_check_connection()` watchdog. On failure it retries after 5 s.

`self._handle_data` is swapped from `_data_received_config` to `_data_received` at the end of configuration - this is why there are two receive handlers per protocol class.

### Reader identity check

The `@ExpectedReaderInfo(firmware_name, hardware_name, min_firmware)` class decorator (`reader.py`) stashes a `_expected_reader` dict on the class. `_config_reader()` compares it against the live `ATI`/`REV` response and raises if hardware, firmware name, or firmware version mismatch. Firmware version is parsed as `float("XX.YY")` from a 4-digit field. Bumping a minimum firmware means editing the decorator on the concrete class and the CHANGELOG.

### Data path and command/response

Incoming bytes -> `_connection_data_received` (records `_last_message_time`) -> `_handle_data`. The handler splits traffic in two: asynchronous events (`+CINV`/`+CMINV` inventory, `+IEV` input change, `+HBT`/`HBT` heartbeat, ASCII `...IVF` inventory frames) are dispatched to callbacks; everything else goes into `_receiver_buffer` (an `asyncio.Queue`) which `_send_command` / `_send_recv_command` drain via `_recv(timeout)`.

`_communication_lock` serializes command/response pairs. `_clear_response_buffer()` runs before each send and logs anything stale - unexpected leftovers in that log usually mean a parsing bug, not noise.

Reader responses arrive one line per `_recv()` call. `SerialConnection._work` splits on `\r`, `\n`, or `\r\n` and re-appends a `\r` because downstream handlers strip one trailing byte; some firmware terminates streaming events with a bare CR.

### Watchdog

`_check_connection()` runs while status >= RUNNING. Two triggers reset the reader (disconnect + reconnect): no traffic for `_connection_check_time` (default 10 s) with a failing `_connection_test()`, or - when a continuous inventory is active - no inventory event within `_continuous_inventory_check_time`, set by `start_inventory(timeout=...)`. While an inventory is running it polls at 100 ms so the deadline is honoured precisely.

### Inventory delivery

Two consumption models, both fed by `_fire_inventory_event`: register a callback with `set_cb_inventory()`, or poll `fetch_inventory()`, which drains the internal `_inventory` dict (deduplicated by tag ID, with `seen_count` and `last_seen` accumulated). If a callback is set, the internal cache is not filled - the two models are mutually exclusive.

## Conventions

- Google-style docstrings on all public methods (sphinx napoleon renders them). Reader methods document their `Raises: RfidReaderException`.
- Errors surface as `RfidReaderException` / `RfidTransponderException` only; lower-level `serial`/`socket`/`TimeoutError` are wrapped.
- pylint disables are inline per-file with the rule code and reason. There is no lint config in the repo; `checkCode.sh` is gitignored and not present.
- The package ships `py.typed`; keep annotations complete.
- `metratec_rfid/__init__.py` wraps concrete reader imports in `try/except ModuleNotFoundError` so the library still imports when an optional module is missing.

## Adding a reader class

1. New module in `metratec_rfid/`, subclassing the right protocol class plus mixins, decorated with `@ExpectedReaderInfo(...)`.
2. Export it from `metratec_rfid/__init__.py` inside the matching `try` block.
3. Register the firmware name in `FW_READER_LUT` in `utils.py` - `detect_readers()` maps the firmware string from `ATI` to the class.
4. Add it to `HF_READER` / `UHF_READER` in `examples/example_utils.py`.
5. Add an `autoclass` entry under `docs/source/api/uhf_reader/` or `hf_reader/`.

## Releasing

Version lives in three places and must be kept in sync: `setup.py` `version=`, `metratec_rfid/__init__.py` `__version__`, and a new section in `CHANGELOG.md` (reStructuredText, with `:Release Date:`). `docs/source/conf.py` has its own `release` field that currently lags the package version. Release commits are tagged `rX.Y.Z`.
