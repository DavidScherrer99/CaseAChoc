# CaseAChoc
> CaseAChoc est un petite infrastructure démontrant l'utilisation d'un message broker (ActiveMQ).
> Il permet de récupérer les tickets envoyé sur un webhook (en python).
> Le webhook les poussent sur un message broker (activeMQ)
> Un server flask recupère ces les messages emis sur le topic et les envoie via server sent event
> Finalement, le dashboard les récupère via un event source, les traite et les affiche.

**Requirements**: Docker and docker compose

```shell script
# Clone the repository
# Start docker compose
docker-compose up -d --build
# This will start all databases services, and build each portion of the app.
# The first time will take som time, because it will download all dependencies, and build app containers (you can found Dockerfiles in project dedicated directories). About 5 minutes on modest hardware.
```

### Test with webhook simulator

```shell script
python petzi_simulator.py http://127.0.0.1:5000/store secret
```