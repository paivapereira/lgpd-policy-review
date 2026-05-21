"""Synthetic fixture — CNH collection via attribute assignment.

Pattern (c) of recognizers_pack_br: attribute assignment.

Synthetic CNH: 56284913773 (algorithmically valid check digits over an
arbitrary base; see README.md §Identificadores sintéticos for provenance).
"""


class Driver:
    """Driver record holding a CNH license number."""

    def __init__(self) -> None:
        self.cnh: str = ""
        self.name: str = ""


def load_driver_from_form(form_data: dict) -> Driver:
    """Populate a Driver instance from form data."""
    driver = Driver()
    driver.cnh = form_data["cnh"]
    driver.name = form_data["name"]
    return driver


form_input = {"cnh": "56284913773", "name": "Synthetic Driver"}
driver = load_driver_from_form(form_input)
