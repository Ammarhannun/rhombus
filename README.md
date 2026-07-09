# Rhombus

This is a web app where you upload a CSV or Excel file, describe in plain English what you want to find (like "email addresses"), and it replaces all the matches with whatever you want. The pattern matching is done by turning your description into a regex with an LLM, and the actual replacement runs in the background with Spark so it can handle big files.

## Demo

https://youtu.be/HKKAMtLz8cQ?si=04jRm4aTDCeX0G_g

## How it works

You upload a file and pick which column(s) to work on. You type something like "find email addresses" and a replacement value like "REDACTED". The backend sends your description to OpenAI which gives back a regex, then it kicks off a background job that applies that regex over the column with Spark and writes out a new file. While that's happening the frontend keeps checking the job status so you get a progress bar, and when it's done it shows you the results in a table with paging.

I split it into two Django apps: `api` handles the HTTP stuff (uploads, checking status, getting results) and `processing` has the Celery task, the LLM call and the Spark engine. `config` is the Django project itself plus the Celery setup.

## Why Celery and Redis

The whole point is that a big file can take a while, and you can't make the browser sit there waiting on one request. So when you upload, the API just saves the job to the database, hands it off to Celery and immediately returns a job id. Celery is the thing that actually does the work in the background, and Redis is what Celery uses to pass jobs to the worker. I also use Redis as a cache for the regexes, so if two people ask for the same thing I don't pay for the OpenAI call twice. The task updates a progress number on the job as it goes, and the frontend polls for it.

Redis ends up doing three jobs here: Celery broker, Celery result backend, and the Django cache. It's all pointed at `redis://localhost:6379/0` (or whatever `REDIS_URL` is set to).

## Why Spark

Instead of looping over the rows in pandas one at a time, Spark loads the file into partitions and runs the regex replace across all of them at once, so it uses all the cores. Because replacing text in a row doesn't depend on any other row, there's no shuffling needed and it just scales with how many partitions/cores you have. When I tested a 1 million row file it split into 8 partitions and finished in about 10 seconds. If you ever needed more you'd point it at a real Spark cluster instead of `local[*]`.

There's also a pandas fallback in the engine. That's just so it still runs on my machine when I don't have the Java/Spark stuff installed locally : in Docker it uses real Spark.

## The API

- `POST /api/columns/` : send a file, get its column names back
- `POST /api/jobs/` : send the file + prompt + columns, get a job id straight away
- `GET /api/jobs/<id>/` : check status and progress
- `GET /api/jobs/<id>/results/?page=&page_size=` : get the processed rows, paged
- `POST /api/jobs/<id>/cancel/` : cancel a job that's running

## Running it with Docker

This is the easiest way and it runs the real Spark engine.

```bash
cp .env.example .env
```

Put your real OpenAI key in `.env`, then:

```bash
docker compose up --build
```

- App: http://localhost:3000
- API: http://localhost:8000/api
- Flower (to watch the worker): http://localhost:5555

## Running it without Docker

You need Redis running for this. Then:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

In another terminal start the worker:

```bash
source venv/bin/activate
celery -A config worker --loglevel=info
```

And the frontend:

```bash
cd frontend
npm install
npm run dev
```

Without Docker the engine uses the pandas fallback since Spark isn't set up locally.

## Testing a big file

I made a 1 million row CSV to check it holds up:

```bash
python -c "import pandas as pd; n=1000000; pd.DataFrame({'id':range(n),'email':['user%d@example.com'%i for i in range(n)]}).to_csv('big.csv', index=False)"
```

Then just upload `big.csv`, target the `email` column, type "find email addresses", replacement "REDACTED", and watch it finish.

## Notes

- I used SQLite to keep it simple. For production you'd swap in Postgres.
- Results are written to a CSV and sent back a page at a time so the browser never has to load millions of rows.
- The regex from the LLM gets validated before it runs (checks it compiles and isn't something that'll blow up with catastrophic backtracking).
