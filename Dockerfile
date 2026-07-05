FROM mcr.microsoft.com/playwright:v1.40.0-jammy
RUN apt-get update && apt-get install -y python3-pip
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY . .
CMD ["python3", "bot.py"]
