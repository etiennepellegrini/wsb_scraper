additionalArgs="$@"

# --- Run all scenarios
today=$(date '+%Y%m%dT%H%M')
yday=$(date -d '-1 day' '+%Y%m%d')
ydayDir=$(ls -td output/2021*/ | head -1)

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
            --output "output/${today}/${scoreType}/${timePeriod}" \
            --prev "${ydayDir}/${scoreType}/${timePeriod}/to_buy.txt" \
            ${additionalArgs}"
        echo $cmd
        eval $cmd
    done
done
