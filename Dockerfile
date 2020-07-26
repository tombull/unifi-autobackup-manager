FROM python:alpine
WORKDIR /app
COPY reset-all.py .
RUN pip install --no-cache-dir python-dateutil pytz
ENV BACKUP_FOLDER=/var/lib/unifi/backup/autobackup \
    MONTHS_TO_KEEP_OF_WEEKLY=1 \
    WEEKS_TO_KEEP_OF_DAILY=1 \
    YEARS_TO_KEEP_OF_MONTHLY=0 \
    TIMEZONE=Europe/London
CMD python ./manage-autobackups.py --backupfolder ${BACKUP_FOLDER}} --monthstokeep ${MONTHS_TO_KEEP_OF_WEEKLY}} --weekstokeep ${WEEKS_TO_KEEP_OF_DAILY}} --yearstokeep ${YEARS_TO_KEEP_OF_MONTHLY}} --timezone ${TIMEZONE}
