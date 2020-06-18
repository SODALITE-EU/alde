FROM python:3.5-slim AS compile
RUN python -m venv /opt/venv
WORKDIR /usr/src/alde
COPY . .
RUN . /opt/venv/bin/activate; pip install pybuilder==0.11.17; pyb -o

FROM python:3.5-alpine
WORKDIR /opt/alde
RUN apk add -qU openssh-client
COPY --from=compile /usr/src/alde/target/dist/alde-1.0.dev0/ .
COPY resources/bin/copy_keys.sh /usr/local/bin
RUN pip install .
EXPOSE 5000
ENTRYPOINT ["python", "app.py"]
