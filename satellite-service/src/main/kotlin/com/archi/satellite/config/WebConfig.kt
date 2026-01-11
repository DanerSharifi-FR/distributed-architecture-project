package com.archi.satellite.config

import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.web.reactive.function.client.WebClient

@Configuration
class WebConfig {
    @Bean
    fun webClient(): WebClient = WebClient.builder().build()
}