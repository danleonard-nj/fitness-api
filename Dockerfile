FROM azureks.azurecr.io/base/pybase:v2 as base

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

FROM base AS main

COPY . .
EXPOSE 80

CMD ["bash", "startup.sh"]
