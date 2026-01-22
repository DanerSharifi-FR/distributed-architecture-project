FROM php:8.3-cli-alpine

RUN apk add --no-cache $PHPIZE_DEPS linux-headers bash git unzip \
    && pecl install redis \
    && docker-php-ext-enable redis

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

WORKDIR /app

COPY composer.json composer.lock ./
RUN composer install --no-dev --prefer-dist --no-interaction --no-progress

COPY . .

EXPOSE 8080

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["php", "-S", "0.0.0.0:8080", "-t", "public"]
