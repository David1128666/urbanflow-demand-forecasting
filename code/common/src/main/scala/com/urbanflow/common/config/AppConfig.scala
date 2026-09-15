package com.urbanflow.common.config

object AppConfig {
  val KafkaBootstrapServers: String =
    sys.env.getOrElse("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

  val KafkaDemandTopic: String =
    sys.env.getOrElse("KAFKA_DEMAND_TOPIC", "urbanflow-demand-events")

  val KafkaGroupId: String =
    sys.env.getOrElse("KAFKA_GROUP_ID", "urbanflow-realtime-group")

  val KafkaAutoOffsetReset: String =
    sys.env.getOrElse("KAFKA_AUTO_OFFSET_RESET", "latest")

  val MysqlUrl: String = {
    val host = sys.env.getOrElse("MYSQL_HOST", "localhost")
    val port = sys.env.getOrElse("MYSQL_PORT", "3306")
    val database = sys.env.getOrElse("MYSQL_DATABASE", "urbanflow")
    val timezone = sys.env.getOrElse("MYSQL_TIMEZONE", "Asia/Shanghai")
    s"jdbc:mysql://$host:$port/$database?useSSL=false&serverTimezone=$timezone&allowPublicKeyRetrieval=true"
  }

  val MysqlUser: String = sys.env.getOrElse("MYSQL_USER", "urbanflow")
  val MysqlPassword: String = sys.env.getOrElse("MYSQL_PASSWORD", "change-me")

  val SparkMaster: String = sys.env.getOrElse("SPARK_MASTER", "local[*]")

  val SparkCheckpointDir: String =
    sys.env.getOrElse("SPARK_CHECKPOINT_DIR", "checkpoint/realtime")
}
