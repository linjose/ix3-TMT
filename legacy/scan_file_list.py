import os

directory_path = "/path/to/your/directory"  # Replace with your desired directory
try:
    all_entries = os.listdir(directory_path)
    files = [f for f in all_entries if os.path.isfile(os.path.join(directory_path, f))]
    print("Files in the directory:")
    for file_name in files:
        print(file_name)
except FileNotFoundError:
    print(f"Error: Directory '{directory_path}' not found.")
except NotADirectoryError:
    print(f"Error: '{directory_path}' is not a directory.")
except PermissionError:
    print(f"Error: Permission denied to access '{directory_path}'.")
