import json
import sys
from pathlib import Path

# Ensure server root is in sys.path when running as a standalone script
server_dir = Path(__file__).resolve().parent.parent
root_dir = server_dir.parent
if str(server_dir) not in sys.path:
    sys.path.insert(0, str(server_dir))

from main import app  # noqa: E402


def export_schema(output_path: Path | None = None):
    openapi_data = app.openapi()
    target_path = output_path or (root_dir / "client" / "openapi.json")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w") as f:
        json.dump(openapi_data, f, indent=2)
    print(f"Successfully generated {target_path}")


if __name__ == "__main__":
    custom_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    export_schema(custom_path)



