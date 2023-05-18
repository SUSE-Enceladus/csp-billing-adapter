v0.1.0 (2023-05-18)
-------------------

- Wait one cycle at startup before checking usage data
- Dry run metering against API at startup
- Sleep only for remainder of cycle to account for processing
  time.
- Handle multiple errors using error list
- Use cache and csp config in memory
- Pass in now timestamp instead of re-generating
- Save config map and cache once at end of loop
- Add base product to csp config
- Add timestamps to log messages
- Add retry mechanism for functions that may fail randomly

v0.0.2 (2023-05-10)
-------------------

- Handle no matching dimension found for volume billing
- Only load testing support plugins in unit tests
- Add additional logging to core paths
- Add Initial exception handling

v0.0.1 (2023-05-03)
-------------------

- initial release
