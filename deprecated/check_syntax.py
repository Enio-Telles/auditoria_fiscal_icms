#!/usr/bin/env python3
"""
Syntax checker for microservices
"""

import ast
import os


def check_syntax(file_path, service_name):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        ast.parse(content)
        return True, "OK"
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except IndentationError as e:
        return False, f"Indentation error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def main():
    print("🔍 Checking microservices syntax...")
    services = [
        "auth-service",
        "tenant-service",
        "product-service",
        "import-service",
        "ai-service",
        "classification-service",
    ]

    errors_found = 0
    for service in services:
        main_py = os.path.join("microservices", service, "main.py")
        if os.path.exists(main_py):
            success, message = check_syntax(main_py, service)
            if success:
                print(f"✅ {service}: {message}")
            else:
                print(f"❌ {service}: {message}")
                errors_found += 1
        else:
            print(f"⚠️ {service}: File not found")

    print(f"\n📊 Total errors: {errors_found}")
    return errors_found == 0


if __name__ == "__main__":
    main()
