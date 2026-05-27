import os


def load_json_seeder(base_file: str):
    file_name = os.path.splitext(
        os.path.basename(base_file))[0] + ".json"
    file_path = f"{os.path.dirname(base_file)}/files/{file_name}"
    with open(file_path, "r") as f:
        data = f.read()
    return data
