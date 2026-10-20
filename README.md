# Device Test Bench — prototype

Windows desktop prototype for manual device testing with two serial ports.

## Features in this prototype
- Select and connect two independent COM ports.
- Read and display a text stream from the DUT UART.
- Detect a configurable marker string and pass the remainder of that line to a placeholder decoder.
- Modbus RTU read/write controls for the test fixture.
- Run a configured firmware CLI command and display output/exit code.
- Operator-driven test checklist and timestamped log.

## Setup (Windows)
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

If PowerShell blocks activation, run:
```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

## Important configuration
The UI intentionally uses placeholder serial settings and Modbus register values. Before connecting real hardware, set:
- Both UART baud rates, parity, data bits, stop bits and line ending.
- Marker text and actual payload format.
- Modbus slave ID, register address, function/register type and expected response.
- Firmware CLI executable and arguments.

Modbus operations are deliberately explicit buttons; no test command runs automatically.
Do not use the sample register address/value against real hardware until verified.

## Firmware CLI
Configure the executable and arguments in the Firmware tab. Arguments are split on spaces in this prototype, so paths with spaces should be entered as quoted arguments. For a production version, use separate argument fields or a command profile.

## Suggested next steps
1. Add a project configuration file (JSON/YAML) for device-specific settings.
2. Implement the actual payload decoder and validation rules.
3. Add a structured test result model and CSV/JSON report export.
4. Add timeouts, reconnect logic, and a hardware-safe stop/cleanup sequence.
5. Add automated tests for the decoder and Modbus command construction.
