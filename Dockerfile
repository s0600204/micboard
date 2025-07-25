## Build frontend
FROM node:24-bookworm-slim AS micboard_frontend
WORKDIR /home/node/app

# Install node deps
COPY package.json webpack.config.js ./
RUN npm install --omit=dev

COPY css css
COPY js js
COPY static static

RUN npm run build


## Build backend
FROM python:3-alpine AS micboard_server
WORKDIR /usr/src/app

# Install Python deps
COPY py/requirements.txt py/requirements.txt
RUN pip3 install -r py/requirements.txt

COPY *.html *.json ./
COPY py py
COPY --from=micboard_frontend /home/node/app/static ./static

EXPOSE 8058
CMD ["python3", "py/micboard.py"]
