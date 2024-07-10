FROM python:3.13.0b3-bookworm
WORKDIR /app
COPY . /app
ENV TERM=xterm
CMD ["python", "-u", "src/sync.py"]
