FROM python:3.10 as build

RUN pip install cython

WORKDIR /app
COPY requirements.txt .
COPY setup.py .
COPY hexachromix/ hexachromix

RUN python setup.py build_ext --inplace && \
	pip install .

#RUN python -m unittest discover -s hexachromix/tests


FROM python:3.10-slim

COPY --from=build /usr/local/bin/ /usr/local/bin/
COPY --from=build /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

CMD ["uvicorn", "hexachromix.api:app", "--host", "0.0.0.0", "--port", "80"]
