# ProteoBench

## Development setup

### Local installation
Install the package and dependencies with [Flit](https://flit.pypa.io/en/stable/):

```
pip install flit
flit install -s
```

Using a virtual environment is recommended.


### Unit tests

To run the tests run the command:

```
python -m unittest test/test_module_dda_quant.py
```


### Testing the web interface locally

Start the web server locally with:

```
streamlit run ./webinterface/Home.py
```

This will launch the Proteobench application in your web browser.


Changes to the code in `./webinterface` will trigger a reload of the web server.
However, changes in `./proteobench` require a full restart of the webserver
to be included.
