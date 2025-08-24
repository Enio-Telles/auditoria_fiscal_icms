"""
Script to fix deprecated FastAPI on_event usage across all microservices
Converts @app.on_event("startup") to new lifespan pattern
"""

import os
import re

# Microservices to fix
services = [
    "auth-service",
    "tenant-service",
    "product-service",
    "import-service",
    "ai-service",
]

microservices_dir = r"C:\Users\eniot\OneDrive\Desenvolvimento\Projetos_IA_RAG\auditoria_fiscal_icms\microservices"


def fix_service(service_name):
    main_py_path = os.path.join(microservices_dir, service_name, "main.py")

    if not os.path.exists(main_py_path):
        print(f"❌ File not found: {main_py_path}")
        return False

    try:
        with open(main_py_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check if already has lifespan
        if "async def lifespan" in content:
            print(f"✅ {service_name} already has lifespan pattern")
            return True

        # Check if has contextlib import
        if "from contextlib import asynccontextmanager" not in content:
            # Add import after existing imports
            imports_pattern = r"(from typing import[^\n]*\n)"
            if re.search(imports_pattern, content):
                content = re.sub(
                    imports_pattern,
                    r"\1from contextlib import asynccontextmanager\n",
                    content,
                )
            else:
                # Add at the beginning if no typing import found
                content = "from contextlib import asynccontextmanager\n" + content

        # Replace startup event with lifespan
        startup_pattern = (
            r'@app\.on_event\("startup"\)\s*\nasync def startup_event\(\):\s*\n(.*?)\n'
        )
        startup_match = re.search(startup_pattern, content, re.DOTALL)

        if startup_match:
            startup_body = startup_match.group(1).strip()

            # Create lifespan function
            lifespan_code = f'''@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize on startup"""
    {startup_body}
    yield
    # Cleanup code (if needed) would go here

'''

            # Remove the old startup event
            content = re.sub(startup_pattern, "", content, flags=re.DOTALL)

            # Find FastAPI app creation and add lifespan
            app_pattern = r"(app = FastAPI\([^)]*)\)"
            if re.search(app_pattern, content):
                content = re.sub(app_pattern, r"\1,\n    lifespan=lifespan\n)", content)

            # Insert lifespan function before app creation
            app_creation_pattern = r"(# FastAPI [Aa]pp\s*\n)"
            if re.search(app_creation_pattern, content):
                content = re.sub(app_creation_pattern, lifespan_code + r"\1", content)
            else:
                # If no comment found, insert before app = FastAPI
                app_pattern = r"(app = FastAPI)"
                content = re.sub(app_pattern, lifespan_code + r"\1", content)

        # Write back the file
        with open(main_py_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ Fixed {service_name}")
        return True

    except Exception as e:
        print(f"❌ Error fixing {service_name}: {e}")
        return False


if __name__ == "__main__":
    print("🔧 Fixing deprecated FastAPI on_event usage...")

    success_count = 0
    for service in services:
        if fix_service(service):
            success_count += 1

    print(f"\n✅ Fixed {success_count}/{len(services)} microservices")
    print("🚀 You can now restart the microservices!")
