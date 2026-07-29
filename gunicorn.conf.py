# Gunicorn config for mini-social-media
import multiprocessing

bind = "0.0.0.0:9197"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
preload_app = True
timeout = 30
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
accesslog = "-"
errorlog = "-"
capture_output = True
