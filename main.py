from app import create_app
import os

app = create_app()

# Run enum case fix on startup
try:
    from startup_fix_enum import check_and_fix_enum_case
    check_and_fix_enum_case()
except Exception as e:
    print(f"Warning: Could not run enum case fix: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
