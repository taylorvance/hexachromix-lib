FROM python:3.10 as build
WORKDIR /app
COPY . .
RUN pip install cython
RUN python setup.py build_ext --inplace
RUN pip install .

FROM python:3.10-slim
COPY --from=build /usr/local/bin/ /usr/local/bin/
COPY --from=build /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
