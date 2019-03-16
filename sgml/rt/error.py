class RuntimeException(Exception):
    pass


def bail(fmt: str, *args, **kwargs):
    raise RuntimeException(fmt.format(*args, **kwargs))
