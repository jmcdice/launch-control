# Launch Control

AI-powered deployment management system.

## Installation

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package
pip install -e ".[dev]"
```

## Usage

```bash
# Start receiver
launch-control receive --debug

# Start transmitter with specific personas
launch-control transmit --persona the_dude

# Start both components
launch-control start --persona the_dude --debug
```
