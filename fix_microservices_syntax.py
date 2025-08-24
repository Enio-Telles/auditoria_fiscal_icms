"""
Fix all microservices with orphaned database initialization lines
"""

import os
import re

services_to_fix = ["auth-service", "product-service", "import-service", "ai-service"]


def fix_service(service_name):
    main_py = f"microservices/{service_name}/main.py"

    if not os.path.exists(main_py):
        print(f"❌ {service_name}: File not found")
        return False

    try:
        with open(main_py, "r", encoding="utf-8") as f:
            content = f.read()

        # Fix the FastAPI app definition issues
        # Remove trailing comma before lifespan
        content = re.sub(
            r'version="1\.0\.0"\s*,\s*\n\s*lifespan=lifespan',
            'version="1.0.0",\n    lifespan=lifespan',
            content,
        )

        # Remove orphaned database initialization lines after FastAPI app definition
        # Pattern: find lines after app = FastAPI(...) that start with engine = or Base.metadata
        app_pattern = (
            r"(app = FastAPI\([^)]*\))"  # app definition
            r"\s*\n\s*(engine = db_config\.initialize\(\)"  # engine init
            r"\s*\nBase\.metadata\.create_all\(bind=engine\)"  # metadata create
            r"\s*\nlogger\.info\([^)]*\))"  # logger line
        )

        def replace_orphaned_db_lines(match):
            app_def = match.group(1)
            return app_def  # Just return the app definition, remove the orphaned lines

        content = re.sub(
            app_pattern,
            replace_orphaned_db_lines,
            content,
            flags=re.MULTILINE | re.DOTALL,
        )

        # Fix the lifespan function if it's incomplete
        # Find incomplete lifespan functions and fix them
        incomplete_lifespan = (
            r"@asynccontextmanager\s*\nasync def lifespan\(app: FastAPI\):\s*\n"
            r'\s*"""Initialize on startup"""\s*\n(.*?)\s*yield\s*\n'
            r"\s*# Cleanup code \(if needed\) would go here"
        )

        def fix_lifespan(match):
            return '''@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize on startup"""
    engine = db_config.initialize()
    Base.metadata.create_all(bind=engine)
    logger.info(f"{service_name.replace('-', ' ').title()} started")
    yield
    # Cleanup code (if needed) would go here'''

        content = re.sub(incomplete_lifespan, fix_lifespan, content, flags=re.DOTALL)

        # Write back
        with open(main_py, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ Fixed {service_name}")
        return True

    except Exception as e:
        print(f"❌ Error fixing {service_name}: {e}")
        return False


def main():
    print("🔧 Fixing microservices syntax errors...")

    for service in services_to_fix:
        fix_service(service)

    print("\n🧪 Testing syntax after fixes...")

    # Test all services
    import ast

    all_services = [
        "auth-service",
        "tenant-service",
        "product-service",
        "import-service",
        "ai-service",
        "classification-service",
    ]

    for service in all_services:
        path = f"microservices/{service}/main.py"
        try:
            with open(path, "r") as f:
                ast.parse(f.read())
            print(f"✅ {service}: Syntax OK")
        except Exception as e:
            print(f"❌ {service}: {str(e)[:60]}...")


if __name__ == "__main__":
    main()
