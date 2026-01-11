package com.archi.satellite.util

import com.archi.satellite.config.SatelliteProperties
import io.minio.ListObjectsArgs
import io.minio.MinioAsyncClient
import io.minio.RemoveObjectsArgs
import io.minio.messages.DeleteObject
import jakarta.annotation.PostConstruct
import org.junit.jupiter.api.AfterEach
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.test.context.SpringBootTest

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
abstract class ServicesCleaner {
//    @Autowired
//    private lateinit var mongoTemplate: ReactiveMongoTemplate

    @Autowired
    private lateinit var minioClient: MinioAsyncClient

    @Autowired
    private lateinit var properties: SatelliteProperties

    @PostConstruct
    @AfterEach
    fun clean() {
//        cleanDatabase()
        cleanFileServer()
    }

    fun cleanFileServer() {
        val items =
            minioClient
                .listObjects(
                    ListObjectsArgs
                        .builder()
                        .apply {
                            bucket(properties.minio.bucket)
                            recursive(true)
                        }.build(),
                ).toList()
                .map { DeleteObject(it.get().objectName(), it.get().versionId()) }
        minioClient
            .removeObjects(
                RemoveObjectsArgs
                    .builder()
                    .apply {
                        bucket(properties.minio.bucket)
                        objects(items)
                    }.build(),
            ).toList()
    }

//    fun cleanDatabase() {
//        runBlocking {
//            mongoTemplate.collectionNames
//                .collect { mongoTemplate.dropCollection(it).awaitSingleOrNull() }
//        }
//    }
}