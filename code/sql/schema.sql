CREATE DATABASE IF NOT EXISTS urbanflow
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE urbanflow;

CREATE TABLE IF NOT EXISTS station_dim (
    station_id VARCHAR(64) NOT NULL,
    city_id VARCHAR(32) NOT NULL,
    station_name VARCHAR(100) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL,
    latitude DECIMAL(10, 6) NOT NULL,
    capacity INT NOT NULL,
    region_id VARCHAR(32) NOT NULL,
    is_active TINYINT NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (station_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS demand_observation (
    observation_id BIGINT NOT NULL AUTO_INCREMENT,
    city_id VARCHAR(32) NOT NULL,
    station_id VARCHAR(64) NOT NULL,
    window_start DATETIME NOT NULL,
    window_end DATETIME NOT NULL,
    demand_count INT NOT NULL DEFAULT 0,
    temperature DECIMAL(6, 2) NULL,
    precipitation DECIMAL(6, 2) NULL,
    is_holiday TINYINT NOT NULL DEFAULT 0,
    data_version VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (observation_id),
    UNIQUE KEY uk_demand_window (
        city_id, station_id, window_start, data_version
    ),
    KEY idx_demand_station_time (station_id, window_start),
    KEY idx_demand_city_time (city_id, window_start)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS realtime_demand_metrics (
    metric_id BIGINT NOT NULL AUTO_INCREMENT,
    city_id VARCHAR(32) NOT NULL,
    station_id VARCHAR(64) NOT NULL,
    window_start DATETIME NOT NULL,
    window_end DATETIME NOT NULL,
    demand_count INT NOT NULL,
    event_count INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (metric_id),
    UNIQUE KEY uk_realtime_window (city_id, station_id, window_start),
    KEY idx_realtime_time (window_start)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS forecast_run (
    forecast_run_id BIGINT NOT NULL AUTO_INCREMENT,
    city_id VARCHAR(32) NOT NULL,
    model_version VARCHAR(64) NOT NULL,
    feature_version VARCHAR(64) NOT NULL,
    data_cutoff DATETIME NOT NULL,
    forecast_start DATETIME NOT NULL,
    horizon_steps INT NOT NULL,
    status VARCHAR(20) NOT NULL,
    error_message VARCHAR(500) NULL,
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (forecast_run_id),
    KEY idx_run_city_time (city_id, data_cutoff)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS forecast_result (
    forecast_result_id BIGINT NOT NULL AUTO_INCREMENT,
    forecast_run_id BIGINT NOT NULL,
    city_id VARCHAR(32) NOT NULL,
    station_id VARCHAR(64) NOT NULL,
    target_time DATETIME NOT NULL,
    horizon_step INT NOT NULL,
    predicted_demand DECIMAL(12, 4) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (forecast_result_id),
    UNIQUE KEY uk_forecast_point (
        forecast_run_id, station_id, horizon_step
    ),
    KEY idx_forecast_query (city_id, station_id, target_time),
    CONSTRAINT fk_forecast_run
        FOREIGN KEY (forecast_run_id)
        REFERENCES forecast_run (forecast_run_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS model_metric (
    metric_id BIGINT NOT NULL AUTO_INCREMENT,
    model_version VARCHAR(64) NOT NULL,
    feature_version VARCHAR(64) NOT NULL,
    split_name VARCHAR(20) NOT NULL,
    horizon_step INT NULL,
    metric_name VARCHAR(32) NOT NULL,
    metric_value DECIMAL(16, 6) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (metric_id),
    KEY idx_metric_model (model_version, metric_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS job_run_log (
    job_run_id BIGINT NOT NULL AUTO_INCREMENT,
    job_name VARCHAR(64) NOT NULL,
    status VARCHAR(20) NOT NULL,
    started_at DATETIME NOT NULL,
    finished_at DATETIME NULL,
    message VARCHAR(500) NULL,
    PRIMARY KEY (job_run_id),
    KEY idx_job_started (job_name, started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS station_inventory_snapshot (
    snapshot_id BIGINT NOT NULL AUTO_INCREMENT,
    city_id VARCHAR(32) NOT NULL,
    station_id VARCHAR(64) NOT NULL,
    snapshot_time DATETIME NOT NULL,
    capacity INT NOT NULL,
    available_bikes INT NOT NULL,
    available_docks INT NOT NULL,
    station_status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (snapshot_id),
    UNIQUE KEY uk_station_snapshot (station_id, snapshot_time),
    KEY idx_snapshot_time (snapshot_time),
    KEY idx_snapshot_status (station_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dispatch_recommendation (
    recommendation_id BIGINT NOT NULL AUTO_INCREMENT,
    forecast_run_id BIGINT NOT NULL,
    recommendation_time DATETIME NOT NULL,
    dispatch_deadline DATETIME NOT NULL,
    from_station_id VARCHAR(64) NOT NULL,
    to_station_id VARCHAR(64) NOT NULL,
    recommended_quantity INT NOT NULL,
    distance_km DECIMAL(10, 3) NOT NULL,
    priority_score DECIMAL(12, 4) NOT NULL,
    shortage_before INT NOT NULL,
    shortage_after INT NOT NULL,
    near_term_demand DECIMAL(12, 2) NULL,
    safety_stock INT NULL,
    target_bikes INT NULL,
    reason VARCHAR(300) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (recommendation_id),
    UNIQUE KEY uk_dispatch_action (
        forecast_run_id, from_station_id, to_station_id, dispatch_deadline
    ),
    KEY idx_dispatch_run (forecast_run_id),
    CONSTRAINT fk_dispatch_forecast_run
        FOREIGN KEY (forecast_run_id)
        REFERENCES forecast_run (forecast_run_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
