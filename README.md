# ProteoBench

## Installation instructions

For developement, install with:

```
pip install --editable .
```

For development on the web interface, install with the optional dependencies:

```
pip install --editable .[web]
```

Using a virtual environment is recommended.

To run the tests run the command:

```
python -m unittest test/test_module_dda_quant.py
```

## Running the Web Application
Run the following command in the terminal/command prompt:
```
streamlit run ./webinterface/Home.py
```

This will launch the Proteobench application in your web browser.


