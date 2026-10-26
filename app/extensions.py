"""Flask extensions, created once and attached to the app in create_app()."""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_session import Session
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()
server_session = Session()
# Rate limits are keyed by the client's IP address.
limiter = Limiter(key_func=get_remote_address, default_limits=[])
