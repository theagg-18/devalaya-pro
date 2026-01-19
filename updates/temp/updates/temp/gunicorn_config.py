# Gunicorn configuration file for Devalaya Pro

# Bind to all interfaces on port 5000
bind = "0.0.0.0:5000"

# Number of worker processes. 
# Rule of thumb: (2 x number of cores) + 1
workers = 4

# Use threads for better handling of simultaneous requests
threads = 2

# Timeout for workers
timeout = 120

# Logging
accesslog = "access.log"
errorlog = "error.log"
loglevel = "info"

# Preload app for better memory efficiency
preload_app = True
