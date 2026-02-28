from slowapi import Limiter
from slowapi.util import get_remote_address

# Singleton rate limiter — imported by main.py (to register on app)
# and by routers (to use the @limiter.limit decorator)
limiter = Limiter(key_func=get_remote_address)
