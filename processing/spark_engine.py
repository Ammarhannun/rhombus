import re
import pandas as pd


def apply_regex_replacement(input_path, output_path, columns, pattern, replacement, progress_callback=None):
    try:
        return _spark_replace(input_path, output_path, columns, pattern, replacement, progress_callback)
    except Exception:
        return _pandas_replace(input_path, output_path, columns, pattern, replacement, progress_callback)


def _spark_replace(input_path, output_path, columns, pattern, replacement, progress_callback):
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import regexp_replace, col

    spark = SparkSession.builder \
        .appName('rhombus-regex') \
        .master('local[*]') \
        .config('spark.driver.memory', '2g') \
        .getOrCreate()

    spark.sparkContext.setLogLevel('ERROR')

    if progress_callback:
        progress_callback(10)

    if input_path.endswith('.csv'):
        df = spark.read.option('header', 'true').csv(input_path)
    else:
        pdf = pd.read_excel(input_path)
        df = spark.createDataFrame(pdf)

    if progress_callback:
        progress_callback(30)

    for column in columns:
        if column in df.columns:
            df = df.withColumn(column, regexp_replace(col(column), pattern, replacement))

    if progress_callback:
        progress_callback(70)

    pdf_result = df.toPandas()
    pdf_result.to_csv(output_path, index=False)
    total_rows = len(pdf_result)

    spark.stop()

    if progress_callback:
        progress_callback(95)

    return total_rows


def _pandas_replace(input_path, output_path, columns, pattern, replacement, progress_callback):
    if progress_callback:
        progress_callback(10)

    if input_path.endswith('.csv'):
        df = pd.read_csv(input_path)
    else:
        df = pd.read_excel(input_path)

    if progress_callback:
        progress_callback(40)

    for column in columns:
        if column in df.columns:
            df[column] = df[column].astype(str).apply(
                lambda val: re.sub(pattern, replacement, val)
            )

    if progress_callback:
        progress_callback(80)

    df.to_csv(output_path, index=False)

    if progress_callback:
        progress_callback(95)

    return len(df)
