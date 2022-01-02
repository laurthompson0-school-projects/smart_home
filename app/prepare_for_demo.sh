#!/bin/bash

pdm run python generate_events.py
./init_remote_schema.exp
./init_remote_data.exp
sed -i '' 's/LOCAL_POSTGRES_URL/REMOTE_POSTGRES_URL/' ./public/app.py
