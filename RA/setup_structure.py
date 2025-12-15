# Copyright (c) 2025
# Licensed under the MIT License

import os

# Create directory structure for research assistant
base_dir = r"c:\Users\SaadG\Desktop\Projects\Python\Agents\Agentic_Designs.worktrees\worktree-2025-12-13T03-45-20\research_assistant"

directories = [
    base_dir,
    os.path.join(base_dir, "tools"),
    os.path.join(base_dir, "gui"),
    os.path.join(base_dir, "logs"),
]

for directory in directories:
    os.makedirs(directory, exist_ok=True)
    print(f"Created: {directory}")

# Create __init__.py files
init_files = [
    os.path.join(base_dir, "tools", "__init__.py"),
    os.path.join(base_dir, "gui", "__init__.py"),
]

for init_file in init_files:
    with open(init_file, 'w') as f:
        f.write("# Package initialization\n")
    print(f"Created: {init_file}")

print("\nDirectory structure created successfully!")
