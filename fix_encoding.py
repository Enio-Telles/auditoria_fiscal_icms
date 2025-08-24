import os


def clean_file_advanced(file_path):
    """
    Reads a file, removes non-printable and specific control characters,
    and saves it back as clean UTF-8.
    """
    try:
        # Read the file in binary mode
        with open(file_path, "rb") as f:
            content_bytes = f.read()

        # Attempt to decode with utf-8-sig to handle BOM, then fall back to utf-8
        try:
            content_str = content_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            content_str = content_bytes.decode("utf-8", errors="replace")

        # Remove the specific problematic character and other common control chars
        # The character `\x8d` is a control character, `isprintable()` will be false.
        cleaned_str = "".join(
            c for c in content_str if c.isprintable() or c in "\n\r\t"
        )

        # Write the cleaned content back to the file using UTF-8 encoding without BOM
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(cleaned_str)

        print(f"Successfully performed advanced cleaning on {file_path}")

    except Exception as e:
        print(f"An error occurred during advanced cleaning: {e}")


if __name__ == "__main__":
    # Use an absolute path to be safe
    config_file_path = (
        r"c:\Users\eniot\OneDrive\Desenvolvimento\Projetos_IA_RAG\auditoria_fiscal_icms"
        r"\configs\ai_config.yaml"
    )
    if os.path.exists(config_file_path):
        clean_file_advanced(config_file_path)
    else:
        print(f"Error: File not found at {config_file_path}")
