
# ==============================================
# Stage 1: Builder برای نصب dependencies
# ==============================================
FROM python:3.11-alpine as builder

WORKDIR /build

# فقط ابزارهای ضروری برای کامپایل برخی پکیج‌های پایتون
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    python3-dev \
    musl-dev 
    # linux-headers       #required for pillow & psycop2(not psycop2-binary)

COPY requirements.txt .

# نصب با بهینه‌سازی حداکثری
RUN pip install --user --no-cache-dir -r requirements.txt \
    && apk del .build-deps 
# حذف بسته‌های کامپایل پس از نصب


# ==============================================
# Stage 2: Runtime image نهایی
# ==============================================
FROM python:3.11-alpine

# ایجاد کاربر غیر root
RUN addgroup -S appgroup && \
    adduser -S appuser -G appgroup && \
    mkdir -p /app/static && \
    chown -R appuser:appgroup /app

WORKDIR /app

# کپی dependencies از stage builder
COPY --from=builder --chown=appuser:appgroup /root/.local /home/appuser/.local

# کپی entrypoint و تنظیم دسترسی‌ها
COPY --chown=appuser:appgroup entrypoint.sh /app/
RUN sed -i 's/\r$//g' /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# کپی فایل‌های پروژه
COPY --chown=appuser:appgroup . .

# تنظیم متغیرهای محیطی
ENV PATH="/home/appuser/.local/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

USER appuser

ENTRYPOINT ["/app/entrypoint.sh"]
