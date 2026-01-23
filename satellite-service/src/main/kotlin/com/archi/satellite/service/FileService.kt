package com.archi.satellite.service

import com.archi.satellite.config.MinioConfig
import com.archi.satellite.config.SatelliteProperties
import io.minio.MinioAsyncClient
import io.minio.PutObjectArgs
import kotlinx.coroutines.future.await
import org.bson.types.ObjectId
import org.springframework.http.codec.multipart.FilePart
import org.springframework.stereotype.Service
import java.io.ByteArrayInputStream

@Service
class FileService(private val minioClient: MinioAsyncClient, satelliteProperties: SatelliteProperties) {

    companion object {
        const val SATELLITE_ROOT = "${MinioConfig.PUBLIC_ROOT}/satellite"
        const val SATELLITE_PICTURE_PREFIX = "$SATELLITE_ROOT/pictures"
    }

    private val properties = satelliteProperties.minio

    suspend fun putTileLayerPicture(impactId: String, layer: OwmLayer, data: ByteArray ): String {
        val fileKey = "$SATELLITE_PICTURE_PREFIX/$impactId/${layer.name.lowercase()}.png"

        val request =
            PutObjectArgs
                .builder()
                .apply {
                    bucket(properties.bucket)
                    `object`(fileKey)
                    contentType("image/png")
                    stream(ByteArrayInputStream(data), data.size.toLong(), -1L)
                }.build()
        minioClient.putObject(request).await()

        return "${properties.bucket}/$fileKey"
    }
}