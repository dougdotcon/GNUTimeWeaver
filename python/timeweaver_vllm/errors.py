class UnsupportedEnvironmentError(RuntimeError):
    """Raised when vLLM/PyTorch or Linux/WSL prerequisites are absent."""

class CompatibilityError(ValueError):
    pass
