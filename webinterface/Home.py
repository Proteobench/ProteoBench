"""psm_utils Streamlit-based web server."""

import streamlit as st
from _base import StreamlitPage


class StreamlitPageHome(StreamlitPage):
    def _main_page(self):
        pass


if __name__ == "__main__":
    StreamlitPageHome()
