import subprocess
import json
import sys
from pathlib import Path

def generate_report(output_dir: str = "reports"):
    """Generate pylint JSON and HTML reports."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    json_file = output_path / "pylint_report.json"
    html_file = output_path / "pylint_report.html"

    print("[*] Generating pylint report...")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pylint", "--output-format=json", "src"],
            capture_output=True,
            text=True,
            check=False,
        )

        with open(json_file, "w", encoding="utf-8") as f:
            f.write(result.stdout)

        print(f"[+] JSON report saved: {json_file}")

        print("[*] Converting to HTML...")
        try:
            from pylint_json2html import main as json2html_main

            old_argv = sys.argv
            sys.argv = ["pylint-json2html", "-o", str(html_file), str(json_file)]

            try:
                json2html_main()
                print(f"[+] HTML report saved: {html_file}")
                print(f"\n[+] Report generated successfully!")
                return True
            finally:
                sys.argv = old_argv

        except Exception as e:
            print(f"[-] Error converting to HTML: {e}")
            return False

    except FileNotFoundError as e:
        print(f"[-] Error: {e}")
        print("Make sure pylint and pylint-json2html are installed:")
        print("  pip install -r requirements.txt")
        return False

if __name__ == "__main__":
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "reports"
    success = generate_report(output_dir)
    sys.exit(0 if success else 1)
