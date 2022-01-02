# Kill after docker is done!
init:
	pdm install
	npm install
	docker-compose up

# Postgres runs on localhost:5432
# Redis    runs on localhost:6379
# Flask    runs on localhost:4000
# React    runs on localhost:3000
start:
	screen -S docker-services -X stuff ^C; \
	screen -S react-dev-server -X stuff ^C; \
	screen -dmS docker-services docker-compose up; \
	screen -dmS react-dev-server bash -c "sleep 5 && npm run start"; \
	sleep 3 && pdm run start; \
	screen -S docker-services -X stuff ^C; \
	screen -S react-dev-server -X stuff ^C;
