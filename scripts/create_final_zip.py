import os
import zipfile
import sys

# Paths
source_dir = r"d:\SABHA ID\Devalaya Billing System\dist"
zip_path = r"d:\SABHA ID\Devalaya Billing System\Devalaya_Portable_Final.zip"

if not os.path.exists(source_dir):
    print(f"Error: Source directory '{source_dir}' does not exist.")
    sys.exit(1)

print(f"Zipping '{source_dir}' to '{zip_path}'")

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            file_path = os.path.join(root, file)
            # Make path inside zip relative to dist folder
            arcname = os.path.relpath(file_path, source_dir)
            try:
                zipf.write(file_path, arcname)
                # print(f"Added: {arcname}")
            except Exception as e:
                print(f"Skipping {arcname}: {e}", file=sys.stderr)
print('Zip creation completed.')
