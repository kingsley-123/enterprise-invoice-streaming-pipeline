from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

# Production Spark session with essential configs
spark = SparkSession.builder \
    .appName("InvoiceProcessor-Production") \
    .config("spark.sql.streaming.stopGracefullyOnShutdown", "true") \
    .config("spark.mongodb.read.connection.uri", "mongodb://admin:password123@mongodb:27017/invoices?authSource=admin") \
    .config("spark.mongodb.write.connection.uri", "mongodb://admin:password123@mongodb:27017/invoices?authSource=admin") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")
print("🚀 Production Invoice Processor Started")

# Schema for invoice data
invoice_schema = StructType([
    StructField("invoice_id", StringType(), False),
    StructField("timestamp", StringType(), False), 
    StructField("total_amount", DoubleType(), False),
    StructField("customer", StructType([
        StructField("customer_id", StringType(), False),
        StructField("first_name", StringType(), True),
        StructField("last_name", StringType(), True),
        StructField("email", StringType(), True),
        StructField("segment", StringType(), True),
        StructField("loyalty_status", StringType(), True),
        StructField("age", StringType(), True)
    ]), False),
    StructField("store", StructType([
        StructField("store_id", StringType(), False),
        StructField("name", StringType(), True),
        StructField("city", StringType(), True),
        StructField("state", StringType(), True),
        StructField("region", StringType(), True)
    ]), False),
    StructField("payment_method", StringType(), True)
])

# Read from Kafka with production settings
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "broker:29092") \
    .option("subscribe", "invoice-stream") \
    .option("startingOffsets", "earliest") \
    .option("failOnDataLoss", "false") \
    .option("kafka.consumer.group.id", "invoice-processor-prod") \
    .load()

# Process and validate data
invoice_df = df.select(
    from_json(col("value").cast("string"), invoice_schema).alias("data")
).select("data.*") \
.withColumn("processed_at", current_timestamp()) \
.filter(col("invoice_id").isNotNull()) \
.filter(col("total_amount") > 0)

# Write to MongoDB with production settings
query = invoice_df.writeStream \
    .outputMode("append") \
    .format("mongodb") \
    .option("checkpointLocation", "/opt/spark-data/checkpoints") \
    .option("database", "invoices") \
    .option("collection", "streaming_invoices") \
    .trigger(processingTime="5 seconds") \
    .start()

print("📊 Streaming to MongoDB every 5 seconds")
print(f"🔍 Query ID: {query.id}")

# Simple monitoring
try:
    query.awaitTermination()
except KeyboardInterrupt:
    print("🛑 Shutting down gracefully...")
    query.stop()
finally:
    spark.stop()