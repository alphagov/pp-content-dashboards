# Notes on spotlight-config files

Root URL is here:
http://spotlight.perfplat.dev/performance

The JSON config files which are displayed can be linked here:
/Users/ianhopkinson/govuk/spotlight/app/support/stagecraft_stub/responses

spotlight-config abbreviations for a template:
{{dept_name}} - this is the long form name
{{dept_abbrev}} - this is the abbreviation both for humans and for filter-by
{{dept_slug}} - this is the department slug used to construct urls to policies, the department, etc

Validation, internally Spotlight does this:
https://github.com/alphagov/spotlight/blob/master/tools/stagecraft-generate-module-stubs.js

It is fussy about spaces.

We can look at the "no-realistic-dashboard" to see examples of all modules,
but we need to switch the BackdropUrl config here:
/spotlight/config/config.development_bowl_vm.json

Original version:
```json
{
  "assetPath": "/assets/",
  "port": 3057,
  "backdropUrl": "http://perfplat.dev/data/{{ data-group }}/{{ data-type }}",
  "screenshotTargetUrl": "http://spotlight.perfplat.dev",
  "screenshotServiceUrl": "http://spotlight.perfplat.dev:3000",
  "govukHost": "spotlight.dev.gov.uk"
}
```

Modified line:
"backdropUrl": "https://www.preview.performance.service.gov.uk/data/{{ data-group }}/{{ data-type }}",

# Questions

Module 1 - "Traffic" - contains data from two different searches on two separate tabs - this seems not to be possible

Do I merge the two dimensions into one search?
ga:visitors,ga:pageviews