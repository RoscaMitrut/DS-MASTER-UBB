import hashlib
import glob
import os
import sys

def generate_checksums():
    files = glob.glob('data/raw/*')
    with open('docs/checksums.sha256', 'w') as f:
        for file_path in files:
            clean_path = file_path.replace(os.sep, '/')
            with open(file_path, 'rb') as data:
                digest = hashlib.file_digest(data, 'sha256').hexdigest()
                f.write(f"{digest}  {clean_path}\n")
    print("Checksums generated in docs/checksums.sha256")

def verify_checksums():
    if not os.path.exists('docs/checksums.sha256'):
        print("Error: docs/checksums.sha256 not found.")
        sys.exit(1)
        
    with open('docs/checksums.sha256', 'r') as f:
        stored_hashes = [line.strip().split() for line in f]

    all_good = True
    for digest, rel_path in stored_hashes:
        local_path = rel_path.replace('/', os.sep)
        
        if not os.path.exists(local_path):
            print(f"MISSING: {local_path}")
            all_good = False
            continue
            
        with open(local_path, 'rb') as data:
            current_digest = hashlib.file_digest(data, 'sha256').hexdigest()
            
        if current_digest == digest:
            print(f"OK: {local_path}")
        else:
            print(f"FAIL: {local_path}")
            all_good = False

    if not all_good:
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        verify_checksums()
    else:
        generate_checksums()