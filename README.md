# CSP Billing Adapter

The billing adapter provides a configurable abstraction layer
for applications to report billing information to the CSP API.
It is designed as a plugin oriented Python application using
[Pluggy](https://pluggy.readthedocs.io/en/stable/) for plugin
management.

## Plugin Hooks

The core adapter is designed to work with 3 distinct plugin
layers.

### Storage Layer

This layer handles the storage and backup of adapter billing
data and status. A plugin implementing the hooks for the storage
layer is required to implement all hooks in the
[storage_hookspecs.py](https://github.com/SUSE-Enceladus/csp-billing-adapter/blob/main/csp_billing_adapter/storage_hookspecs.py)
module.

### CSP Layer

This layer handles metered billing in a CSP and metadata
generation. The hooks found in
[csp_hookspecs.py](https://github.com/SUSE-Enceladus/csp-billing-adapter/blob/main/csp_billing_adapter/csp_hookspecs.py)
should be implemented.

### General Setup Layer

There are three hookspecs to implement for the general setup
layer. These include **`setup_adapter`**, **`load_defaults`**, and
**`get_usage_data`**. Details about these hookspecs are found in
[hookspecs.py](https://github.com/SUSE-Enceladus/csp-billing-adapter/blob/main/csp_billing_adapter/hookspecs.py).

## Configuration

The adapter is configured via a YAML file that is accesible to the
binary. The config file is used to setup the different intervals for
billing and usage updates. It is also where the billing dimensions
are configured. These dimensions are used to determine each metered
billing. The following is what a config file may look like:

```
version: 1.1.1
api: THE_PATH_WHERE_WE_GET_THE_UNIT_INFORMATION
billing_interval: monthly|hourly
query_interval: Time in seconds
product_code: TBD
usage_metrics:
  metric_1:
    usage_aggregation: maximum
    consumption_reporting: volume
    dimensions:
    - dimension: dimension_1
  metric_2:
    usage_aggregation: current
    consumption_reporting: volume
    dimensions:
    - dimension: dimension_2
reporting_interval: CSP_DEPENDENT_SETTING
reporting_api_is_cumulative: CSP_DEPENDENT_SETTING
```

For more details about the expected format for the config file see
https://github.com/SUSE-Enceladus/csp-billing-adapter/tree/main/examples.

The default location for the config file is
*/etc/csp_billing_adapter/config.yaml*. This can be modified via the
environment variable **`CSP_ADAPTER_CONFIG_FILE`** such as:

```
export CSP_ADAPTER_CONFIG_FILE=/tmp/my_config.yaml
```

## Datastores

### csp-config

This is a dictionary that is stored based on storage hooks. It provides an
API for the application with the status of the adapter. The dictionary
has the following format:

```
{
    "timestamp": string(date(RFC_3339_Compliant)),
    "billing_api_access_ok": bool,
    "expire": string(date(RFC_3339_Compliant)),
    "errors": list[string],
    "last_billed": string(date(RFC_3339_Compliant)),
    "usage": {"{usage_key}": 10},
    "customer_csp_data": {
      "document": {"accoundId":....},
      "signature": "signature",
      "pkcs7": "pkcs7",
      "cloud_provider": "string"
    },
    "base_product": string
}
```

**timestamp:** Updated every time the adapter meters. This is based on
the query interval.

**billing_api_access_ok:** If false the adapter was not able to meter
billing to the CSP API. Otherwise metered billing API access is okay.

**expire:** This timestamp is updated every time the adapter runs. It's set
to the next expected run time. If it is in the past then the adapter is in
an error state. Either it has crashed or is unable to update csp-config.

**errors:** This is a list of errors that occurred in the last run. If
there are any errors in the list the adapter is in an error state.

**last_billed:** This is a timestamp that denotes the last time the adapter
metered a bill. It's expected that this never gets older than the billing
interval. At first startup and for the first interval this will be empty.

**usage:** This coincides with **last_billed**. This is the usage metered
in last billing. At first startup and for the first month this will be empty.

**customer_csp_data:** This is a dictionary with metadata information for
the running container/vm from the CSP. The format is dependent on the CSP.

**base_product:** This is a CPE product + version string in the following
format `cpe:/o:suse:product:v1.2.3`.

### cache

This is the adapter cache that stores the current state of the adapter. It
is dictionary that is stored based on the storage hookspecs. The format
is as follows:

```
{
  "adapter_start_time": string(date timestamp),
  "next_bill_time": string(date timestamp),
  "next_reporting_time": string(date timestamp),
  "usage_records": [{
    "{usage_key}": int,
    "reporting_time": string,
    "base_product": string
  }],
  "last_bill": {
    "record_id": string,
    "metering_time": string(date timestamp),
    "dimensions": [
      {
        "dimension": string,
        "units": int
      }
    ]
  }
}
```

**adapter_start_time:** This is a timestamp that denotes when the adapter
first started running.

**next_bill_time:** This is a timestamp that denotes when the next bill
is due.

**next_reporting_time:** This is a timestamp that denotes when the next
reporting is due.

**usage_records:** This is a list of usage records accrued since
the last metered bill. Each record is a dictionary containing the usage
data, `reporting_time` and `base_product`. Where `reporting_time` is a
timestamp that denotes when the usage record was reported and
`base_product` is a CPE product + version string.

**last_bill:** This is a dictionary containing info about the last bill.

**record_id:** The ID from the CSP API for the last metered bill.

**metering_time:** A timestamp denoting when the last metering occurred.

**dimensions:** A dictionary containing the dimension names and units
billed in the last metering.

## Service

The adapter service runs continuously based on the query interval which is
set in the config file. For example if the query interval is set to 3600
the adapter service will run every hour. The following actions may be taken
when the adapter runs:

### Get Usage Data

Each time the adapter runs it will check for new usage data via the
`get_usage_data` hook. This hook is will be implemented by a plugin for the
given deployment. It is expected that the function will return a dictionary
with usage data and it should include two keys; `base_product` and
`reporting_time`.

### Meter billing

The billing interval and reporting interval determine when the adapter meters
a bill through the CSP API. In some cases the two interval may be identical.
In this case every metering is billing usage with the CSP. In other cases the
reporting interval is more frequent than the billing interval. This is where
an application is expected to provide a "heartbeat" on a shorter interval than
the product billing period.

The billing interval has two possible values; monthly and hourly. When set to
hourly the adapter bills usage every hour. And when set to monthly the adapter
aggregates usage based on the query interval and bills once a month.

### Save data

At the end of each cycle the adapter will store billing and usage data using
the storage hookspecs. This backs up the data in case the adapter is rebooted
or down for some amount of time.

### Errors

Each time the adapter runs it will start with an empty list of errors, and as
errors are encountered they will be appended to this list which will be saved
in the "errors" field of the csp-config. This means that any errors reported
in the csp-config are from the most recent run.

In the example errors below, "..." denotes an extended error message which
will change based on the specific error. If the adapter is unable to access
metered billing API it will also set `billing_api_access_ok` to False. If any
error state is noticed in csp-config it should be communicated proactively to
the customer through UI.

#### Startup errors

- At startup if the adapter config is invalid an error will be added:
    - "Billing adapter config is invalid. Config is missing {key}" 
- At startup if the adapter has no access to billing API an error will
  be added:
    - "Fatal error while validating metering API access: ..."

#### Operational errors

- If the adapter cannot retrieve usage data then the adapter will add
  an error:
    - "Usage data retrieval failed: ..."
- If the adapter has trouble processing the metering then the adapter
  will:
    - Add error message to list. The specific message will be based on
      the error that occurs.
    - Set `billing_api_access_ok` to False
- If the adapter cannot save csp-config it will add an error:
    - "`csp-config` failed to save: ..."
    - However, this error won't be visible to the application since
      the data is not able to save.
- If the adapter cannot save cache it will add an error:
    - "cache failed to save: ..."

#### Unrecoverable errors

- If there is an unexpected error the adapter will add an error message then crash:
    - "Unexpected error: ..."
- If there is an expected but unrecoverable error an error will be added then adapter will crash:
    - "CSP Billing Adapter error: ..."
- If the config file is missing the version attribute the adapter will raise an error:
    - "Invalid config file. Missing 'version' attribute."
- If the config file has an incompatible version the adapter will raise an error that starts with:
    - "Incompatible config file. Found version: ..."
