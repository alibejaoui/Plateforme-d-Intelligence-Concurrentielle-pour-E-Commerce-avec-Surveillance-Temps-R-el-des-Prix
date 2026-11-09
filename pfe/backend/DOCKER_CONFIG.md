# Configuration Docker vs Développement Local

## 🐳 Architecture Docker

Quand vous utilisez Docker Compose, tous les services communiquent via leur **nom de service** dans le réseau Docker interne.

```
Backend (Docker)  →  mysql (nom du service)
                 →  redis (nom du service)
                 →  rabbitmq (nom du service)
```

## 📝 Configuration des Hostnames

### ✅ Dans Docker (docker-compose.yml)

Tous les services utilisent les **noms de services** comme hostnames :

```yaml
# Database
DATABASE_URL: mysql+pymysql://root:password@mysql:3306/competitive_intelligence
#                                                      ^^^^^
#                                                      Nom du service

# Redis
REDIS_HOST: redis
#          ^^^^^
#          Nom du service

# RabbitMQ
CELERY_BROKER_URL: amqp://guest:guest@rabbitmq:5672//
#                                        ^^^^^^^^
#                                        Nom du service
```

### 🖥️ Développement Local (sans Docker)

Si vous lancez le backend directement sur Windows (sans Docker), utilisez `localhost` :

```env
# Database
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/competitive_intelligence

# Redis
REDIS_HOST=localhost

# RabbitMQ
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
```

## 🔄 Alembic Migrations

### Dans Docker

```bash
# Exécuter depuis le conteneur backend
docker exec -it competitive_intelligence_backend alembic upgrade head
```

Alembic utilisera automatiquement `settings.DATABASE_URL` qui pointe vers `mysql`.

### Développement Local

Si vous exécutez Alembic depuis Windows :

1. Assurez-vous que MySQL tourne sur `localhost:3306`
2. Modifiez temporairement `alembic.ini` ou utilisez une variable d'environnement :

```bash
# Option 1: Modifier alembic.ini
sqlalchemy.url = mysql+pymysql://root:password@localhost:3306/competitive_intelligence

# Option 2: Utiliser variable d'environnement
export DATABASE_URL=mysql+pymysql://root:password@localhost:3306/competitive_intelligence
alembic upgrade head
```

## 🧪 Tester la Connexion

### Depuis le conteneur backend

```bash
docker exec -it competitive_intelligence_backend python -c "
from app.core.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('✅ Database connection OK!')
"
```

### Depuis Windows (outil externe)

Si vous voulez vous connecter à MySQL depuis un outil externe (DBeaver, MySQL Workbench, etc.) :

1. Le port MySQL est exposé : `3306:3306` dans docker-compose.yml
2. Utilisez : `localhost:3306`
3. Credentials : `root` / `password`

## 📋 Récapitulatif

| Service | Dans Docker | Développement Local |
|---------|-------------|---------------------|
| MySQL   | `mysql:3306` | `localhost:3306` |
| Redis   | `redis:6379` | `localhost:6379` |
| RabbitMQ| `rabbitmq:5672` | `localhost:5672` |

## ⚠️ Points Importants

1. **Ne mélangez pas** : Si le backend tourne dans Docker, utilisez les noms de services
2. **Ports exposés** : Les ports sont exposés pour accès externe, mais la communication interne utilise les noms de services
3. **Healthchecks** : Les healthchecks dans docker-compose garantissent que les services sont prêts avant le démarrage du backend

