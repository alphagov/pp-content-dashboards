jq '.modules[] as $i | $i.slug + ", " + $i.title' dft-content-dashboard.json
jq '.modules[] | keys' dft-content-dashboard.json