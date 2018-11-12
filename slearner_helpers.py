import re


def get_sl_tokens(line):
    return re.split(r'[\s]+', line)
