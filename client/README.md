# Client

Client-side application for the SmartMailbox project.
The code runs on a Raspberry Pi capturing images from a connected camera and sends them to the server for processing.

## Setup

This project uses `pyproject.toml` to manage dependencies. 
You can use either the standard `venv` with `pip` or the faster `uv` tool.

### Using `venv` and `pip`

1.  **Create and activate a virtual environment**:
    From the `client` directory, run:
    ```bash
    # Create the environment
    python -m venv .venv

    # Activate the environment
    # On Windows
    .venv\\Scripts\\activate
    # On macOS/Linux/Raspberry Pi OS
    source .venv/bin/activate
    ```

2.  **Install Dependencies**:
    With the virtual environment activated, run:
    ```bash
    pip install .
    ```

### Using `uv`

1.  **Create and activate a virtual environment**:
    From the `client` directory, run:
    ```bash
    # Create and activate the environment
    uv venv
    
    # Activate the environment
    # On Windows
    .venv\\Scripts\\activate
    # On macOS/Linux/Raspberry Pi OS
    source .venv/bin/activate
    ```

2.  **Install Dependencies**:
    With the virtual environment activated, run:
    ```bash
    uv pip install .
    ```

## Configuration

Open `config.toml` and adjust the settings as needed.

## Run

Ensure your virtual environment is activated. You can run the application from the `client` directory.

### Using `python`

```bash
python -m src.main
```

### Using `uv`

```bash
uv run python -m src.main
```