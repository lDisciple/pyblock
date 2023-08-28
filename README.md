# Pyblock

#### Note: This is a hobby project and is not in active development. If you would like assistance or to develop this further please raise an issue or contact me.

Pyblock is a Scratch-like code builder that runs via Python on your local machine.
The aim of the project is to allow budding programmers interact with a real general purpose language
while still using a toolbox that is easy to use.

The toolbox can also easily be extended by updating the engine (**and toolbox.xml**).

The project makes use of Scratch blocks which is a fork of Google's Blockly project.

## Installation
```
# Install Python dependencies
pip install -r requirements.txt
# Build the editor view
./build-editor.sh
```
The editor can be built standalone, however, it does depend on the engine running

## Running
```
uvicorn main:app --reload --port 3001
```

# Possible roadmap
- [ ] Add toolbox functionality