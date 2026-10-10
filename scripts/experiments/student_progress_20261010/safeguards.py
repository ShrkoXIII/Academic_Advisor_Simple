"""Authenticate experiment records and publish completion after protection checks."""
from .workflow import configuration_signature, write_json


def sign_record(value):
    if 'integrity_sha256' in value:
        raise ValueError('Record already contains an integrity signature')
    return {**value,'integrity_sha256':configuration_signature(value)}


def authenticate_record(value):
    if 'integrity_sha256' not in value:
        raise ValueError('Refusing unsigned experimental tuning evidence')
    payload={key:item for key,item in value.items() if key!='integrity_sha256'}
    if value['integrity_sha256']!=configuration_signature(payload):
        raise ValueError('Experimental tuning integrity mismatch')
    return payload


def authenticate_selection(value, expected_context):
    """Bind a signed tuning result to its run, specification and temporal rows."""
    payload=authenticate_record(value)
    if payload.get('context')!=expected_context:
        raise ValueError('Experimental tuning context mismatch')
    return payload['selected']


def publish_completion(path, payload, verifier):
    try:
        isolation=verifier()
    except BaseException as error:
        write_json(path,{'status':'FAILED','reason':str(error),**payload})
        raise
    write_json(path,{'status':'COMPLETE',**payload,'isolation':isolation})
