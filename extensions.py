from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Explicit in-memory storage — fine for single-server temple deployment
limiter = Limiter(
    get_remote_address,
    default_limits=[],
    storage_uri="memory://",
)
