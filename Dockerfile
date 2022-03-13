FROM python:3.9-alpine as builder

RUN apk add --no-cache build-base

RUN python -m venv /opt/venv

ENV \
  PATH="/opt/venv/bin:$PATH" \
  CFLAGS="-fcommon"

COPY requirements.txt .
RUN pip install -r requirements.txt

FROM python:3.9-alpine

WORKDIR /pi-fan-controller

ENV \
  PATH="/opt/venv/bin:$PATH" \
  CFLAGS="-fcommon" \
  # Which PORT Prometheus will open to expose the metrics.
  PROMETHEUS_PORT="8000" \
  # (degrees Celsius) Fan kicks on at this temperature.
  ON_THRESHOLD="65" \
  # (degress Celsius) Fan shuts off at this temperature.
  OFF_THRESHOLD="55" \
  # (seconds) How often we check the core temperature.
  SLEEP_INTERVAL="5" \
  # Which GPIO pin you're using to control the fan.
  GPIO_PIN="17"

COPY --from=builder /opt/venv /opt/venv

COPY fancontrol.py fancontrol.py

ENTRYPOINT [ "/pi-fan-controller/fancontrol.py" ]

EXPOSE 8000
