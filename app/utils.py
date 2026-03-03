from nh3 import clean
from email.utils import parseaddr
from flask import Request

def sanitise_form_inputs(request: Request, fields: list[str]) -> dict[str, str | None]:
    """
    Sanitise the form inputs from a flask request and return as a dictionary.
    Parameters:
        request (flask.Request): the flask request object.
        fields (list[str]): a list of form inputs to sanitise
    """
    values = {}
    for field in fields:
        value = request.form.get(field)
        if value != None:
            values[field] = clean(value)
        else:
            values[field] = None
    return values
