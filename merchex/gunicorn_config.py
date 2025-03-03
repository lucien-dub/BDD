# Gunicorn configuration file
import multiprocessing

# Serveur socket
bind = "213.32.91.54:8000"

# Nombre de processus worker
workers = multiprocessing.cpu_count() * 2 + 1

# Type de worker (recommandé pour Django)
worker_class = "gthread"

# Nombre de threads par worker
threads = 2

# Timeout maximum pour les requêtes (en secondes)
timeout = 60

# Autres paramètres utiles
keepalive = 5
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/merchex/logs/gunicorn-access.log"
errorlog = "/merchex/logs/gunicorn-error.log"
loglevel = "info"

# Utilisateur et groupe sous lesquels Gunicorn s'exécutera
user = "ubuntu"
group = "MinesBetIndustrie"

# Préchargement de l'application pour de meilleures performances
preload_app = True