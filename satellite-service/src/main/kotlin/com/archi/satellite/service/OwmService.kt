package com.archi.satellite.service

import com.archi.satellite.config.SatelliteProperties
import org.springframework.http.HttpStatus
import org.springframework.http.MediaType
import org.springframework.stereotype.Service
import org.springframework.web.reactive.function.client.WebClient
import org.springframework.web.reactive.function.client.bodyToMono
import java.lang.Math.toRadians
import kotlin.math.floor
import org.springframework.web.reactive.function.client.awaitBody
import org.springframework.web.server.ResponseStatusException
import kotlin.math.cos
import kotlin.math.ln
import kotlin.math.pow
import kotlin.math.tan

enum class OwmLayer {
    CLOUDS_NEW,
    PRECIPITATION_NEW,
    PRESSURE_NEW,
    WIND_NEW,
    TEMP_NEW,
}

@Service
class OwmService(
    private val webClient: WebClient,
    satelliteProperties: SatelliteProperties
) {
    companion object {
        const val ZOOM = 2
        const val MAX_LAT = 85.05112878
    }

    val apiKey = satelliteProperties.owm.apiKey

    // See https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
    // and https://stackoverflow.com/questions/37464824/converting-longitude-latitude-to-tile-coordinates
    fun getTilesCoordinates(lat: Double, lon: Double): Pair<Int, Int> {
        val n: Double = 2.0.pow(ZOOM)

        fun sec(rad: Double) = 1 / cos(rad)
        fun Int.coerceBetween() = this.coerceIn(0, n.toInt() -1)

        val x: Int = floor(n * (lon + 180) / 360).toInt()
        val latRad: Double = toRadians(lat.coerceIn(-MAX_LAT, MAX_LAT))

        val y: Int = floor(n * (1 - (ln(tan(latRad) + sec(latRad)) / Math.PI)) / 2).toInt()

        return Pair(x.coerceBetween(), y.coerceBetween())
    }

    suspend fun getTileLayerPicture(layer: OwmLayer, lat: Double, lon: Double): ByteArray {
        val (x, y) = getTilesCoordinates(lat, lon)
        val url = "https://tile.openweathermap.org/map/${layer.name.lowercase()}/${ZOOM}/${x}/${y}.png?appid=${apiKey}"
        return webClient
            .get()
            .uri(url)
            .accept(MediaType.IMAGE_PNG)
            .retrieve()
            .onStatus({ it.is4xxClientError }) { response ->
                // handle 4xx errors
                response.bodyToMono<String>()
                    .map { body ->
                        ResponseStatusException(
                            HttpStatus.INTERNAL_SERVER_ERROR,
                            "Error ${response.statusCode()} when accessing OpenWeatherMap API"
                        )
                    }
            }
            .onStatus({ it.is5xxServerError }) { response ->
                // handle 4xx errors
                response.bodyToMono<String>()
                    .map { body ->
                        ResponseStatusException(
                            HttpStatus.SERVICE_UNAVAILABLE,
                            "Error ${response.statusCode()} when accessing OpenWeatherMap API"
                        )
                    }
            }
            .awaitBody<ByteArray>()
    }

    suspend fun getTileLayersPicture(lat: Double, lon: Double): Map<OwmLayer, ByteArray> {
        return OwmLayer.entries.associateWith { layer -> getTileLayerPicture(layer, lat, lon) }
    }
}