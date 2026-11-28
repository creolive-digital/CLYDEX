"""Only stable allowlisted error codes cross cloud API/log boundaries."""


class CloudError(Exception):
    def __init__(self, code: str, status: int = 400, **metadata):
        self.code, self.status = code, status
        self.metadata = {k: v for k, v in metadata.items() if k in ('current_version', 'retry_after') and type(v) is int}
        super().__init__(code)
