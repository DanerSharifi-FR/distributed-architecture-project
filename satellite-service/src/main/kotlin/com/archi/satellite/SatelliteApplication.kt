package com.archi.satellite

import com.archi.satellite.config.SatelliteProperties
import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.context.properties.EnableConfigurationProperties
import org.springframework.boot.runApplication

@SpringBootApplication
@EnableConfigurationProperties(SatelliteProperties::class)
class SatelliteApplication

fun main(args: Array<String>) {
	runApplication<SatelliteApplication>(*args)
}
