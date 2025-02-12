v1.2.0 (2025-02-12)
-------------------

- Add fixed billing feature

v1.1.0 (2024-07-10)
-------------------

- Fix system file, service requires network and uyuni service

v1.0.0 (2024-06-03)
-------------------

- Switch spec build to python 3.11

v0.10.0 (2024-04-17)
-------------------

- Implement 1 month free trial

v0.9.0 (2024-01-12)
-------------------

- Implement metering and usage records archive

v0.8.0 (2023-10-16)
-------------------

- Fix bug when clearing billing status. Use empty dictionary.

v0.7.0 (2023-09-20)
-------------------

- Add and implement get_version hookspec

v0.6.0 (2023-09-12)
-------------------

- Update message when records list is empty
- Only sleep at initial deployment
- Skip invalid records
- Log format variables on a const

v0.5.0 (2023-08-18)
-------------------

- Add logging level from config file

v0.4.0 (2023-08-01)
-------------------

- Handle status dictionary from meter billing and legacy string response.
- Implement supported for tiered consumption reporting.

v0.3.1 (2023-07-03)
-------------------

- Add sub RPM package with systemd file to support run in a VM as daemon

v0.3.0 (2023-06-28)
-------------------

- Add new exception type
- Improved initial metering test exception handling

v0.2.0 (2023-06-07)
-------------------

- Split up `create_csp_config` into smaller components.

v0.1.1 (2023-05-22)
-------------------

- Fix retry on exception in the meter billing test.
- Fix the timestamp in meter billing test call. This is
  a datetime object not a string timestamp.

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
