# parts of the process:
- once in the project run to create the virtual environment:
"python -m venv venv"

# Then to activate
Windows: "venv\Scripts\activate"
macos/linux: "source venv/bin/activate"

# use pip install to add any project specific packages

# Create the requirements.txt file that holds the libraries and versions
pip freeze > requirement.txt

# To install packages after cloning project:
pip install -r requirement.txt

# .gitignore, make sure you include:
venv/
.env/
env/