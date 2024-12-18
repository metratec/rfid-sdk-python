# RFID SDK Python - Documentation

The SDK documentation is a separate Python module since it has dependencies
that are not relevant for the `metratec_rfid` library itself.

The docs are generated with the Python documentation generator *Sphinx*.

## Generating the documentation

Follow the instructions of the projects main README to create a virtual
environment and activate it.

Afterwards, install Sphinx and other project dependencies with:

```bash
pip install -r ../requirements.txt -r requirements.txt
```

Then run

```bash
make html
```

to build the documentation, which will be located in the `build/html` folder. 

To view the documentation, double-click the `index.html` or drag it into
your browser.

## Creating class diagrams

The `pylint` package contains `pyreverse` which can be used to create
class diagrams. To create a PNG diagram for the whole `metratec_rfid` module, use:

```
pyreverse -o png metratec_rfid
```

This may yield a very large diagram, so in order to create a diagram
for a specific class, e.g. the PulsarLR reader class, use:

```
pyreverse -o png -c metratec_rfid.pulsar_lr.PulsarLR metratec_rfid
```