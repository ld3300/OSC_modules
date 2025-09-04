# parts of the process:
- once in the project run to create the virtual environment:
"python -m venv venv"

# Then to activate
Windows: "venv\Scripts\activate"
macos/linux: "source venv/bin/activate"

# use pip install to add any project specific packages

# Create the requirements.txt file that holds the libraries and versions
pip freeze > requirements.txt

# To install packages after cloning project:
pip install -r requirements.txt

# .gitignore, make sure you include:
venv/
.env/
env/

# Make project installable after venv to reference files
# Create pyproject.toml file: example:
[project]
name = "osc_modules"
version = "0.1.0"

[tool.setuptools]
packages = ["osc", "apps"]  # These are the subfolder where callables are

# Then run:
pip install -e .

# to make executable, while in venv
pip install pyinstaller
pip freeze > requirements.txt
pyinstaller script_path/script_name.py
# Creates a build/ and dist/ folder, exec in dist folder add to gitignore
# Also creates a script_name.spec file. Troubleshooting and adding paths
# is done in this file. Future builds will use:
pyinstaller script_name.spec