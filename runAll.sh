additionalArgs="$@"

# --- Run all scenarios
today=$(date '+%Y%m%d')
yday=$(date -d '-1 day' '+%Y%m%d')


for scoreType in {mentions,score}; do

    scoreFlag=''

    if [[ "${scoreType}" == *"score"* ]]; then
        scoreFlag='--score'
    fi

    for timePeriod in {day,week,month}; do
        echo "***** Running ${scoreType} for time period: ${timePeriod} *****"
        cmd="\
        ./run_wsb_scraper.sh \
            ${scoreFlag} \
            --time "${timePeriod}" \
            --top 10 \
            --output "output/${today}/${scoreType}/${timePeriod}" \
            --prev "output/${yday}/${scoreType}/${timePeriod}/to_buy.txt" \
            ${additionalArgs}"
        echo $cmd
        eval $cmd
    done
done
