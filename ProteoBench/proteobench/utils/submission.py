from pathlib import Path


def get_submission_dict(df):
    extra_path = Path("extracted_files")
    submission_files = []

    for idx, row in df.iterrows():
        base_path = extra_path / row["intermediate_hash"]

        if not base_path.exists():
            print(f"Warning: Base path {base_path} does not exist. Skipping.")
            continue

        # Read user comments
        comments_file = base_path / "comment.txt"
        if comments_file.exists():
            comments = "\n".join(open(comments_file).readlines())
        else:
            print(f"Warning: Comment file not found in {base_path}.")
            comments = ""

        # Search for input file starting with "input_file"
        input_files = list(base_path.glob("input_file*"))
        if input_files:
            input_file = input_files[0]  # Take the first match (or adjust selection logic)
        else:
            print(f"Warning: No input file starting with 'input_file' found in {base_path}.")
            input_file = None  # Or handle according to your application

        # Search for parameter file starting with "param_"
        param_files = list(base_path.glob("param_*"))
        if param_files:
            parameter_file = param_files[0]  # Take the first match
        else:
            print(f"Warning: No parameter file starting with 'param_' found in {base_path}.")
            parameter_file = None

        submission_files.append(
            {
                "input_file": input_file,
                "param_file": parameter_file,
                "input_type": row["software_name"],
                "default_cutoff_min_prec": 3,
                "user_comments": comments,
            }
        )

    return submission_files
