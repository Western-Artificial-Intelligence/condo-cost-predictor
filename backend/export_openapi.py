# exporting current api schem to backend/openapi.json 
import json
from pathlib import Path
from app.main import create_app  

def main():
    app = create_app()
    schema = app.openapi()
    out = Path(__file__).with_name("openapi.json")
    out.write_text(json.dumps(schema, indent=2))
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()
