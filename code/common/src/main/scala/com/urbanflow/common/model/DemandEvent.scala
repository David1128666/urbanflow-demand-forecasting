package com.urbanflow.common.model

final case class DemandEvent(
    eventId: String,
    cityId: String,
    stationId: String,
    eventTime: String,
    demandCount: Int,
    temperature: Double,
    precipitation: Double,
    isHoliday: Boolean,
    isAnomaly: Boolean
)
