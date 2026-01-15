# RedactX CLI

Command-line interface for RedactX PII redaction tool.

## Installation

```bash
# Install Core dependency first
uv pip install -e ../core
uv pip install -e .
```

## Usage

```bash
redactx redact --text "My name is John Doe"
redactx batch ./input ./output
redactx --help
```
