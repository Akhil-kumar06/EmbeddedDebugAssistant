# Embedded Debug Assistant — v0.1

A local desktop assistant for recorded FirmwareLab and CANLab telemetry. Deterministic checks cite log lines; Ollama explains the evidence. No paid API or pip packages required.

## Windows setup

Install Windows Python 3 from https://www.python.org/downloads/windows/ with Tcl/Tk and the Python launcher. Python 3.10 or newer is sufficient. Your Ubuntu Python installation does not provide Windows Python.

Install native Windows Ollama from https://ollama.com/download/windows and start it.
In Windows PowerShell:

    ollama pull qwen3:4b

Extract the complete ZIP into your OneDrive Projects folder. Open the EmbeddedDebugAssistant directory containing app.py, core.py and samples/. In Windows PowerShell:

    cd "C:\Users\akhil\OneDrive\Projects\EmbeddedDebugAssistant"
    py -m unittest discover -s tests -v
    py app.py

If py is missing, finish Windows Python installation and open a fresh terminal. No pip install is needed. If using Linux instead, use python3 and install python3-tk.

## First demo

Click CAN example, then read the evidence panel. These are synthetic example records, not measurements from your system. Engine TIMEOUT starts at line 3 and clearing is observed at line 5. Click Explain evidence with local AI. Repeat with Firmware example, then load your actual logs.

The evidence report works without Ollama. AI explanations may contain mistakes: verify them against the line-numbered evidence. Each question is independent, with no persistent chat memory. The assistant sends a bounded report to loopback Ollama at 127.0.0.1:11434. It does not send source files or execute model-generated commands.

## Capture actual FirmwareLab telemetry

In Ubuntu, from your FirmwareLab folder:

    python3 demo.py > telemetry.jsonl

Load this completed file in the assistant. FirmwareLab timestamps are simulated time.

## Capture actual CANLab telemetry

With vcan0 configured, run this in Ubuntu from CANLab:

    ./build/ecu monitor vcan0 > telemetry.jsonl

Open the CANLab dashboard from another terminal and trigger faults. The extra read-only monitor can coexist with the dashboard monitor. Stop the logging monitor with Ctrl+C before loading telemetry.jsonl. CANLab timestamps are elapsed host monotonic time.

Only the two documented JSONL schemas are accepted, up to 5 MiB. One project and one monotonic run per file. Bad rows are reported and skipped. Gaps can hide transitions. The app analyzes a snapshot, not a live subscription. Clearing timestamps are first observed samples; firmware faults may remain during recovery debounce after the initiating condition ends.

## Existing project tests

Click Run project build/tests, select a trusted FirmwareLab or CANLab folder containing build.py, then confirm. The fixed command runs python3 build.py in Ubuntu through WSL. A Linux timeout limits it to 60 seconds. Output includes the actual exit code and the final 12,000 characters. Exit code 124 normally indicates timeout.

This executes the selected build.py, so it is not a sandbox. The AI has no path to invoke this action. Windows requires the existing Ubuntu distribution and its compiler. FirmwareLab build.py includes its integration tests; CANLab build.py runs protocol unit checks only. Run CANLab live tests separately as before.

## Hardware and scope

Default: qwen3:4b, 4096-token context, thinking disabled, short answers. This is a starting configuration for i5/16 GB RAM/GTX 1660 Ti 6 GB. Check actual GPU use with ollama ps. No speed guarantee.

This is a recorded-telemetry debugging assistant foundation. It does not access MCU memory, hardware debuggers, source code or live devices. Voice and live CAN integration are future milestones.

Read core.py first, then tests/test_core.py, local_ai.py, runner.py and app.py. Add your own changes and test evidence before presenting it in interviews. This starter was AI-assisted.

## Next milestones

- Live CAN telemetry and protocol-aware frame decoding.
- Test-run comparisons and saved investigation reports.
- Push-to-talk and spoken replies.

API reference: https://docs.ollama.com/api/chat
