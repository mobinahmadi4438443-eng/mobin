FROM php:8.3-cli-alpine

WORKDIR /app
COPY index.php /app/index.php

RUN mkdir -p /data \
 && printf 'memory_limit=256M\nmax_execution_time=0\ndisplay_errors=0\nlog_errors=1\nerror_log=/dev/stderr\ndate.timezone=Asia/Tehran\n' > /usr/local/etc/php/conf.d/zz-bot.ini

ENV PHP_CLI_SERVER_WORKERS=8
EXPOSE 8080

# 1) boot: create the SQLite DB + set the webhook
# 2) background loop: every 5 minutes refresh exchange rates + Fragment stars prices
# 3) web server
CMD ["sh", "-c", "php /app/index.php boot; (while true; do sleep 300; php /app/index.php tick; done) & exec php -S 0.0.0.0:${PORT:-8080} -t /app /app/index.php"]
