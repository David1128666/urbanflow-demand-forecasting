package com.urbanflow.realtime

import java.sql.{Connection, DriverManager, PreparedStatement}
import java.util.Properties

import com.urbanflow.common.config.AppConfig
import org.apache.spark.sql.functions._
import org.apache.spark.sql.streaming.{StreamingQuery, Trigger}
import org.apache.spark.sql.types._
import org.apache.spark.sql.{DataFrame, SparkSession}

object RealtimeAnalysisApp {

  private final case class RealtimeArgs(
      bootstrapServers: String = AppConfig.KafkaBootstrapServers,
      topic: String = AppConfig.KafkaDemandTopic,
      groupId: String = AppConfig.KafkaGroupId,
      mysqlUrl: String = AppConfig.MysqlUrl,
      mysqlUser: String = AppConfig.MysqlUser,
      mysqlPassword: String = AppConfig.MysqlPassword,
      checkpointDir: String = AppConfig.SparkCheckpointDir,
      watermarkMinutes: Int = 10,
      windowMinutes: Int = 30,
      triggerSeconds: Int = 10,
      startingOffsets: String = AppConfig.KafkaAutoOffsetReset,
      runSeconds: Int = 0,
      maxOffsetsPerTrigger: Long = 5000L
  )

  private val eventSchema: StructType = new StructType()
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

  def main(args: Array[String]): Unit = {
    val cli = parseArgs(args)
    val spark = SparkSession
      .builder()
      .appName("UrbanFlow-Realtime-Analysis")
      .master(AppConfig.SparkMaster)
      .config("spark.sql.session.timeZone", "Asia/Shanghai")
      .config("spark.sql.shuffle.partitions", "4")
      .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true")
      .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    var query: StreamingQuery = null
    try {
      val rawEvents = spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", cli.bootstrapServers)
        .option("subscribe", cli.topic)
        .option("kafka.group.id", cli.groupId)
        .option("startingOffsets", cli.startingOffsets)
        .option("failOnDataLoss", "false")
        .option("maxOffsetsPerTrigger", cli.maxOffsetsPerTrigger.toString)
        .load()

      val parsedEvents = rawEvents
        .select(from_json(col("value").cast(StringType), eventSchema).as("data"))
        .select("data.*")
        .withColumn(
          "event_timestamp",
          to_timestamp(col("event_time"), "yyyy-MM-dd HH:mm:ss")
        )
        .filter(col("event_id").isNotNull && length(col("event_id")) > 0)
        .filter(col("city_id").isNotNull && length(col("city_id")) > 0)
        .filter(col("station_id").isNotNull && length(col("station_id")) > 0)
        .filter(col("event_timestamp").isNotNull)
        .filter(col("demand_count").isNotNull && col("demand_count") >= 0)

      val watermarkDuration = s"${cli.watermarkMinutes} minutes"
      val windowDuration = s"${cli.windowMinutes} minutes"

      val metrics = parsedEvents
        .withWatermark("event_timestamp", watermarkDuration)
        .dropDuplicates("event_id")
        .groupBy(
          window(col("event_timestamp"), windowDuration),
          col("city_id"),
          col("station_id")
        )
        .agg(
          sum("demand_count").as("demand_count"),
          count(lit(1)).as("event_count")
        )
        .select(
          col("window.start").as("window_start"),
          col("window.end").as("window_end"),
          col("city_id"),
          col("station_id"),
          col("demand_count"),
          col("event_count")
        )

      query = metrics.writeStream
        .outputMode("append")
        .option("checkpointLocation", cli.checkpointDir)
        .trigger(Trigger.ProcessingTime(s"${cli.triggerSeconds} seconds"))
        .foreachBatch { (batch: DataFrame, batchId: Long) =>
          writeBatch(batch, batchId, cli)
        }
        .start()

      println(
        s">>> Realtime analysis started: topic=${cli.topic}, " +
          s"window=${cli.windowMinutes}m, watermark=${cli.watermarkMinutes}m"
      )

      if (cli.runSeconds > 0) {
        val completed = query.awaitTermination(cli.runSeconds.toLong * 1000L)
        if (!completed && query.isActive) {
          query.stop()
          query.awaitTermination()
        }
      } else {
        query.awaitTermination()
      }
    } finally {
      if (query != null && query.isActive) {
        query.stop()
        query.awaitTermination()
      }
      spark.stop()
    }
  }

  private def writeBatch(
      batch: DataFrame,
      batchId: Long,
      args: RealtimeArgs
  ): Unit = {
    val rows = batch.collect()
    if (rows.isEmpty) {
      println(s"[realtime] batch=$batchId rows=0")
      return
    }

    val properties = new Properties()
    properties.setProperty("user", args.mysqlUser)
    properties.setProperty("password", args.mysqlPassword)
    properties.setProperty("driver", "com.mysql.cj.jdbc.Driver")

    var connection: Connection = null
    var statement: PreparedStatement = null
    try {
      Class.forName("com.mysql.cj.jdbc.Driver")
      connection = DriverManager.getConnection(args.mysqlUrl, properties)
      connection.setAutoCommit(false)

      statement = connection.prepareStatement(
        """INSERT INTO realtime_demand_metrics
          |  (city_id, station_id, window_start, window_end,
          |   demand_count, event_count)
          |VALUES (?, ?, ?, ?, ?, ?)
          |ON DUPLICATE KEY UPDATE
          |  demand_count = VALUES(demand_count),
          |  event_count = VALUES(event_count)""".stripMargin
      )

      rows.foreach { row =>
        statement.setString(1, row.getAs[String]("city_id"))
        statement.setString(2, row.getAs[String]("station_id"))
        statement.setTimestamp(3, row.getAs[java.sql.Timestamp]("window_start"))
        statement.setTimestamp(4, row.getAs[java.sql.Timestamp]("window_end"))
        statement.setLong(5, row.getAs[Long]("demand_count"))
        statement.setLong(6, row.getAs[Long]("event_count"))
        statement.addBatch()
      }

      statement.executeBatch()
      connection.commit()
      println(s"[realtime] batch=$batchId rows=${rows.length}")
    } catch {
      case error: Throwable =>
        if (connection != null) {
          connection.rollback()
        }
        throw error
    } finally {
      if (statement != null) {
        statement.close()
      }
      if (connection != null) {
        connection.close()
      }
    }
  }

  private def parseArgs(args: Array[String]): RealtimeArgs = {
    def value(name: String, default: String): String = {
      val index = args.indexOf(name)
      if (index >= 0 && index + 1 < args.length) args(index + 1) else default
    }

    RealtimeArgs(
      bootstrapServers = value(
        "--bootstrap-servers",
        AppConfig.KafkaBootstrapServers
      ),
      topic = value("--topic", AppConfig.KafkaDemandTopic),
      groupId = value("--group-id", AppConfig.KafkaGroupId),
      mysqlUrl = value("--mysql-url", AppConfig.MysqlUrl),
      mysqlUser = value("--mysql-user", AppConfig.MysqlUser),
      mysqlPassword = value("--mysql-password", AppConfig.MysqlPassword),
      checkpointDir = value("--checkpoint-dir", AppConfig.SparkCheckpointDir),
      watermarkMinutes = value("--watermark-minutes", "10").toInt,
      windowMinutes = value("--window-minutes", "30").toInt,
      triggerSeconds = value("--trigger-seconds", "10").toInt,
      startingOffsets = value(
        "--starting-offsets",
        AppConfig.KafkaAutoOffsetReset
      ),
      runSeconds = value("--run-seconds", "0").toInt,
      maxOffsetsPerTrigger = value("--max-offsets-per-trigger", "5000").toLong
    )
  }
}
