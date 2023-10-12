FROM python:3.10 as build

RUN pip install cython

WORKDIR /app

# Install pip requirements (image layer optimization).
COPY requirements.txt .
RUN pip install -r requirements.txt

# Cythonize Hexachromix source code (image layer optimization).
COPY hexachromix/core.pyx hexachromix/
COPY setup.py .
RUN python setup.py build_ext --inplace

# Copy the rest of the source code.
COPY hexachromix/ hexachromix/
RUN pip install .

RUN python -m unittest discover -s hexachromix/tests


FROM python:3.10-slim

COPY --from=build /usr/local/bin/ /usr/local/bin/
COPY --from=build /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

CMD ["uvicorn", "hexachromix.api:app", "--host", "0.0.0.0", "--port", "80"]
