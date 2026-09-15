package com.urbanflow.offline

import java.nio.charset.StandardCharsets
import java.nio.file.{Files, Path, Paths}
import java.sql.Timestamp

import com.urbanflow.common.config.AppConfig
import org.apache.spark.sql.expressions.Window
import org.apache.spark.sql.functions._
import org.apache.spark.sql.types._
import org.apache.spark.sql.{DataFrame, SparkSession}

object OfflineAnalysisApp {

  private final case class OfflineArgs(
      inputPath: String = "data/virtual-v1/demand_observations.csv",
      stationsPath: String = "data/virtual-v1/stations.csv",
      outputPath: String = "data/features-v1",
      trainRatio: Double = 0.70,
      validationRatio: Double = 0.15
  )

  private val demandSchema: StructType = new StructType()
    .add("event_id", StringType)
    .add("city_id", StringType)
    .add("station_id", StringType)
    .add("event_time", StringType)
    .add("demand_count", IntegerType)
    .add("temperature", DoubleType)
    .add("precipitation", DoubleType)
    .add("is_holiday", IntegerType)
    .add("is_anomaly", IntegerType)
    .add("data_version", StringType)

  private val stationSchema: StructType = new StructType()
    .add("station_id", StringType)
    .add("city_id", StringType)
    .add("station_name", StringType)
    .add("longitude", DoubleType)
    .add("latitude", DoubleType)
    .add("capacity", IntegerType)
    .add("region_id", StringType)
    .add("station_type", StringType)
    .add("base_demand", DoubleType)

  def main(args: Array[String]): Unit = {
    val cli = parseArgs(args)
    sys.env
      .get("HADOOP_HOME")
      .foreach(path => System.setProperty("hadoop.home.dir", path))

    val spark = SparkSession
      .builder()
      .appName("UrbanFlow-Offline-Features")
      .master(AppConfig.SparkMaster)
      .config("spark.sql.session.timeZone", "Asia/Shanghai")
      .config("spark.sql.shuffle.partitions", "4")
      .config("spark.sql.adaptive.enabled", "true")
      .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
      .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    try {
      val demand = spark.read
        .option("header", "true")
        .schema(demandSchema)
        .csv(cli.inputPath)

      val stations = spark.read
        .option("header", "true")
        .schema(stationSchema)
        .csv(cli.stationsPath)
        .select(
          "station_id",
          "city_id",
          "station_name",
          "capacity",
          "region_id",
          "station_type",
          "base_demand"
        )

      val withTimestamp = demand
        .withColumn(
          "event_timestamp",
          to_timestamp(col("event_time"), "yyyy-MM-dd HH:mm:ss")
        )
        .filter(col("event_timestamp").isNotNull)
        .filter(col("demand_count").isNotNull && col("demand_count") >= 0)
        .join(stations, Seq("station_id", "city_id"), "left")

      val orderedByStation =
        Window.partitionBy("station_id").orderBy("event_timestamp")

      val previous1Hour = orderedByStation.rowsBetween(-2, -1)
      val previous6Hours = orderedByStation.rowsBetween(-12, -1)
      val previous24Hours = orderedByStation.rowsBetween(-48, -1)
      val previous7Days = orderedByStation.rowsBetween(-336, -1)

      val minuteOfDay =
        hour(col("event_timestamp")) * 60 + minute(col("event_timestamp"))
      val sparkWeekday = dayofweek(col("event_timestamp"))
      val twoPi = 2.0 * math.Pi

      val withHistory = withTimestamp
        .withColumn("demand_lag_1", lag("demand_count", 1).over(orderedByStation))
        .withColumn("demand_lag_2", lag("demand_count", 2).over(orderedByStation))
        .withColumn("demand_lag_48", lag("demand_count", 48).over(orderedByStation))
        .withColumn("demand_lag_336", lag("demand_count", 336).over(orderedByStation))
        .withColumn(
          "rolling_mean_1h",
          avg("demand_count").over(previous1Hour)
        )
        .withColumn(
          "rolling_std_1h",
          stddev_pop("demand_count").over(previous1Hour)
        )
        .withColumn(
          "rolling_mean_6h",
          avg("demand_count").over(previous6Hours)
        )
        .withColumn(
          "rolling_std_6h",
          stddev_pop("demand_count").over(previous6Hours)
        )
        .withColumn(
          "rolling_mean_24h",
          avg("demand_count").over(previous24Hours)
        )
        .withColumn(
          "rolling_std_24h",
          stddev_pop("demand_count").over(previous24Hours)
        )
        .withColumn(
          "rolling_mean_7d",
          avg("demand_count").over(previous7Days)
        )
        .withColumn(
          "rolling_std_7d",
          stddev_pop("demand_count").over(previous7Days)
        )
        .withColumn("target_next_30m", lead("demand_count", 1).over(orderedByStation))

      val withCalendar = withHistory
        .withColumn("hour_of_day", hour(col("event_timestamp")))
        .withColumn("minute_of_day", minuteOfDay)
        .withColumn("day_of_week", sparkWeekday)
        .withColumn("day_of_month", dayofmonth(col("event_timestamp")))
        .withColumn("week_of_year", weekofyear(col("event_timestamp")))
        .withColumn(
          "is_weekend",
          when(sparkWeekday.isin(1, 7), lit(1)).otherwise(lit(0))
        )
        .withColumn(
          "hour_sin",
          sin(lit(twoPi) * minuteOfDay / lit(1440.0))
        )
        .withColumn(
          "hour_cos",
          cos(lit(twoPi) * minuteOfDay / lit(1440.0))
        )
        .withColumn(
          "week_sin",
          sin(lit(twoPi) * sparkWeekday / lit(7.0))
        )
        .withColumn(
          "week_cos",
          cos(lit(twoPi) * sparkWeekday / lit(7.0))
        )
        .withColumn(
          "is_feature_complete",
          col("demand_lag_336").isNotNull &&
            col("rolling_mean_7d").isNotNull &&
            col("target_next_30m").isNotNull
        )

      val completeFeatures = withCalendar
        .filter(col("is_feature_complete"))
        .drop("is_feature_complete")
        .cache()

      val rowCount = completeFeatures.count()
      if (rowCount == 0L) {
        throw new IllegalStateException("no complete feature rows were generated")
      }

      val bounds = completeFeatures
        .agg(
          min("event_timestamp").as("min_timestamp"),
          max("event_timestamp").as("max_timestamp")
        )
        .head()

      val minTimestamp = bounds.getAs[Timestamp]("min_timestamp")
      val maxTimestamp = bounds.getAs[Timestamp]("max_timestamp")
      val totalMillis = maxTimestamp.getTime - minTimestamp.getTime
      val trainEnd = new Timestamp(
        minTimestamp.getTime + (totalMillis * cli.trainRatio).toLong
      )
      val validationEnd = new Timestamp(
        minTimestamp.getTime +
          (totalMillis * (cli.trainRatio + cli.validationRatio)).toLong
      )

      val splitFeatures = completeFeatures
        .withColumn(
          "split",
          when(col("event_timestamp") < lit(trainEnd), lit("train"))
            .when(col("event_timestamp") < lit(validationEnd), lit("validation"))
            .otherwise(lit("test"))
        )

      val outputDir = Paths.get(cli.outputPath).toAbsolutePath
      val parquetPath = outputDir.resolve("features.parquet")
      val samplePath = outputDir.resolve("sample.csv")
      val manifestPath = outputDir.resolve("feature_manifest.json")

      splitFeatures
        .coalesce(1)
        .write
        .mode("overwrite")
        .partitionBy("split")
        .parquet(parquetPath.toString)

      splitFeatures
        .select(
          "event_time",
          "city_id",
          "station_id",
          "demand_count",
          "demand_lag_1",
          "demand_lag_48",
          "demand_lag_336",
          "rolling_mean_1h",
          "rolling_mean_24h",
          "rolling_mean_7d",
          "hour_of_day",
          "day_of_week",
          "is_weekend",
          "is_holiday",
          "temperature",
          "precipitation",
          "target_next_30m",
          "split"
        )
        .limit(1000)
        .coalesce(1)
        .write
        .mode("overwrite")
        .option("header", "true")
        .csv(samplePath.toString)

      val splitCounts = splitFeatures
        .groupBy("split")
        .count()
        .collect()
        .map(row => row.getAs[String]("split") -> row.getAs[Long]("count"))
        .toMap

      writeManifest(
        manifestPath = manifestPath,
        inputPath = Paths.get(cli.inputPath).toAbsolutePath.toString,
        stationsPath = Paths.get(cli.stationsPath).toAbsolutePath.toString,
        rowCount = rowCount,
        stationCount = completeFeatures
          .select("station_id")
          .distinct()
          .count(),
        trainEnd = trainEnd,
        validationEnd = validationEnd,
        splitCounts = splitCounts,
        columns = splitFeatures.columns
      )

      println(">>> Offline feature generation completed")
      println(s">>> rows=$rowCount")
      println(s">>> splits=$splitCounts")
      println(s">>> parquet=${parquetPath.toString}")
      println(s">>> manifest=${manifestPath.toString}")

      completeFeatures.unpersist()
    } finally {
      spark.stop()
    }
  }

  private def writeManifest(
      manifestPath: Path,
      inputPath: String,
      stationsPath: String,
      rowCount: Long,
      stationCount: Long,
      trainEnd: Timestamp,
      validationEnd: Timestamp,
      splitCounts: Map[String, Long],
      columns: Array[String]
  ): Unit = {
    Files.createDirectories(manifestPath.getParent)
    val columnJson = columns.map(name => s""""$name"""").mkString(",")
    val splitJson = splitCounts.toSeq
      .sortBy(_._1)
      .map { case (name, count) => s""""$name":$count""" }
      .mkString(",")
    val json =
      s"""{
         |  "schema_version": "1.0",
         |  "input_path": "${escapeJson(inputPath)}",
         |  "stations_path": "${escapeJson(stationsPath)}",
         |  "row_count": $rowCount,
         |  "station_count": $stationCount,
         |  "train_end": "${trainEnd.toInstant}",
         |  "validation_end": "${validationEnd.toInstant}",
         |  "split_counts": {$splitJson},
         |  "columns": [$columnJson]
         |}
         |""".stripMargin
    Files.write(manifestPath, json.getBytes(StandardCharsets.UTF_8))
  }

  private def escapeJson(value: String): String =
    value.replace("\\", "\\\\").replace("\"", "\\\"")

  private def parseArgs(args: Array[String]): OfflineArgs = {
    def value(name: String, default: String): String = {
      val index = args.indexOf(name)
      if (index >= 0 && index + 1 < args.length) args(index + 1) else default
    }

    val cli = OfflineArgs(
      inputPath = value(
        "--input-path",
        "data/virtual-v1/demand_observations.csv"
      ),
      stationsPath = value(
        "--stations-path",
        "data/virtual-v1/stations.csv"
      ),
      outputPath = value("--output-path", "data/features-v1"),
      trainRatio = value("--train-ratio", "0.70").toDouble,
      validationRatio = value("--validation-ratio", "0.15").toDouble
    )

    if (cli.trainRatio <= 0 || cli.validationRatio <= 0) {
      throw new IllegalArgumentException("split ratios must be positive")
    }
    if (cli.trainRatio + cli.validationRatio >= 1.0) {
      throw new IllegalArgumentException(
        "train and validation ratios must sum to less than 1"
      )
    }
    cli
  }
}
