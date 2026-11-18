# slurm-db-backup-check.sh

<div class="code-file">

Code file from the repository  ·  [View on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/schedulers/slurm-smoke-tests/smoke-scripts/slurm-db-backup-check.sh)  ·  [Raw file](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/fields/schedulers/slurm-smoke-tests/smoke-scripts/slurm-db-backup-check.sh)

</div>

```bash
#!/usr/bin/env bash
# slurm-db-backup-check.sh [DBNAME] - dump the accounting database, restore the dump into a scratch
# database, and compare row counts of the job and association tables. Run as a database admin.
# For a real upgrade, stop slurmdbd first (the Slurm upgrade guide takes the dump while it is stopped).
set -u
DB=${1:-slurm_acct_db}
SCRATCH=${DB}_restorecheck
DUMP=$(mktemp /tmp/${DB}.XXXXXX.sql)
trap 'rm -f "$DUMP"; mariadb -e "DROP DATABASE IF EXISTS \`$SCRATCH\`" 2>/dev/null' EXIT

mysqldump --single-transaction --routines "$DB" > "$DUMP" || { echo "FAIL dump"; exit 1; }
echo "dump: $(wc -c < "$DUMP") bytes"
mariadb -e "DROP DATABASE IF EXISTS \`$SCRATCH\`; CREATE DATABASE \`$SCRATCH\`" || exit 1
mariadb "$SCRATCH" < "$DUMP" || { echo "FAIL restore"; exit 1; }

rc=0
for t in $(mariadb -N -e "SELECT table_name FROM information_schema.tables WHERE table_schema='$DB' AND (table_name LIKE '%\_job\_table' OR table_name LIKE '%\_assoc\_table')"); do
    live=$(mariadb -N "$DB" -e "SELECT COUNT(*) FROM \`$t\`")
    back=$(mariadb -N "$SCRATCH" -e "SELECT COUNT(*) FROM \`$t\`")
    if [ "$live" = "$back" ]; then printf 'PASS  %-24s live=%s restored=%s\n' "$t" "$live" "$back"
    else printf 'FAIL  %-24s live=%s restored=%s\n' "$t" "$live" "$back"; rc=1; fi
done
[ $rc -eq 0 ] && echo "BACKUP RESTORES" || echo "BACKUP DOES NOT MATCH"
exit $rc
```
