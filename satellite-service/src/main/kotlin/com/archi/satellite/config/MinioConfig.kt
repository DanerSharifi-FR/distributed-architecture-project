package com.archi.satellite.config

import io.minio.BucketExistsArgs
import io.minio.MakeBucketArgs
import io.minio.MinioAsyncClient
import io.minio.SetBucketPolicyArgs
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

@Configuration
class MinioConfig {
    companion object {
        const val PUBLIC_ROOT = "public"
    }

    @Bean
    fun minioClient(properties: SatelliteProperties): MinioAsyncClient = properties.minio.run {
        MinioAsyncClient
            .builder()
            .credentials(accessKey, secretKey)
            .endpoint(endpoint)
            .build()
            .also { client ->
                client
                    .bucketExists(BucketExistsArgs.builder().bucket(bucket).build())
                    .thenAccept { exists ->
                        if (!exists) {
                            client
                                .makeBucket(MakeBucketArgs.builder().bucket(bucket).build())
                                .thenRun {
                                    client.setBucketPolicy(
                                        SetBucketPolicyArgs
                                            .builder()
                                            .apply {
                                                bucket(bucket)
                                                config(
                                                    """
                                                    {
                                                        "Version": "2012-10-17",
                                                        "Statement": [
                                                            {
                                                                "Effect": "Allow",
                                                                "Principal": "*",
                                                                "Action": [
                                                                    "s3:GetObject"
                                                                ],
                                                                "Resource": [
                                                                    "arn:aws:s3:::${bucket}/$PUBLIC_ROOT/*"
                                                                ]
                                                            }
                                                        ]
                                                    }
                                                    """.trimIndent(),
                                                )
                                            }.build(),
                                    )
                                }
                        }
                    }
            }
    }
}
