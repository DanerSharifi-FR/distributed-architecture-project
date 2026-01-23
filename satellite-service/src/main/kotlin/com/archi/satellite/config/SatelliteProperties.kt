package com.archi.satellite.config

import org.springframework.boot.context.properties.ConfigurationProperties

@ConfigurationProperties("satellite")
class SatelliteProperties(
    val minio: Minio,
    val owm: Owm,
) {
    class Minio(
        val accessKey: String,
        val bucket: String,
        val endpoint: String,
        val publicEndpoint: String,
        val secretKey: String,
    )

    class Owm(
        val apiKey: String,
    )
}