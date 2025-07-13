from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

# Create Spark session with MongoDB
spark = SparkSession.builder \
    .appName("InvoiceProcessor") \
    .config("spark.mongodb.read.connection.uri", "mongodb://admin:password123@mongodb:27017/invoices?authSource=admin") \
    .config("spark.mongodb.write.connection.uri", "mongodb://admin:password123@mongodb:27017/invoices?authSource=admin") \
    .getOrCreate()

print("🚀 Invoice streaming started - writing to MongoDB")

# EXACT schema matching your invoice data
invoice_schema = StructType([
    StructField("invoice_id", StringType()),
    StructField("timestamp", StringType()),
    StructField("total_amount", DoubleType()),
    StructField("customer", StructType([
        StructField("customer_id", StringType()),
        StructField("first_name", StringType()),
        StructField("last_name", StringType()),
        StructField("email", StringType()),
        StructField("segment", StringType()),
        StructField("loyalty_status", StringType()),
        StructField("age", StringType())
    ])),
    StructField("store", StructType([
        StructField("store_id", StringType()),
        StructField("name", StringType()),
        StructField("city", StringType()),
        StructField("state", StringType()),
        StructField("region", StringType())
    ])),
    StructField("payment_method", StringType())
])

# Read from Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "broker:29092") \
    .option("subscribe", "invoice-stream") \
    .option("startingOffsets", "latest") \
    .load()

# Parse JSON with exact schema
invoice_df = df.select(
    from_json(col("value").cast("string"), invoice_schema).alias("data")
).select("data.*")

# Write to MongoDB
query = invoice_df.writeStream \
    .outputMode("append") \
    .format("mongodb") \
    .option("checkpointLocation", "/opt/spark-data/checkpoints") \
    .option("database", "invoices") \
    .option("collection", "streaming_invoices") \
    .trigger(processingTime="10 seconds") \
    .start()

print("📊 Streaming complete invoices to MongoDB every 10 seconds")
query.awaitTermination()