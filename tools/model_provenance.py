"""Frozen model identity shared by training export and evaluation checks."""
import hashlib
import re
from pathlib import Path


def stamp_header(text):
    model_id = hashlib.sha256(text.encode('utf-8')).hexdigest()
    marker = '#define CART_MODEL_H\n'
    if marker not in text or '#define CART_MODEL_ID ' in text:
        raise ValueError('Expected an unstamped CART header')
    return text.replace(marker, marker + f'#define CART_MODEL_ID "{model_id}"\n', 1)


def header_identity(path):
    data = Path(path).read_bytes()
    found = re.findall(rb'^#define CART_MODEL_ID "([0-9a-f]{64})"\r?$', data, re.M)
    if len(found) != 1:
        raise ValueError('Header needs one generated CART_MODEL_ID')
    return {'model_id': found[0].decode(), 'model_header_sha256': hashlib.sha256(data).hexdigest()}


def freeze_record(header_path, sessions):
    return {**header_identity(header_path),
            'development_sessions': sorted(set(map(str, sessions)))}
